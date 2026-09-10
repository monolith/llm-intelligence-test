"""The ``python -m ledgerkit`` command line.

Six subcommands: ``version``, ``inspect``, ``ingest``, ``report``,
``reconcile`` and ``validate``, plus the global ``--config`` option, all
specified in ``SPEC.md``.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__, reconcile, report
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.io import read_records, write_records
from ledgerkit.core.records import LedgerParseError
from ledgerkit.ingest import build_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="read settings from PATH instead of config/settings.toml for this run",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized file")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write the normalized CSV"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="how to group totals")
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="kept for compatibility; refunds are included in totals by default now",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="report where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=Decimal, default=None, metavar="N", help="dollars two systems may differ by"
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files without writing anything")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def cmd_version(args: argparse.Namespace) -> int:
    """Print the package version and the settings file in force."""
    settings = load_settings()
    emit(f"{PROGRAM_NAME} {__version__}")
    emit(f"settings={settings.source_path}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Print the format, size and column names of each export named on the command line."""
    status = 0
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            lines = count_data_lines(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot inspect %s: %s", path, exc)
            status = 1
            continue
        emit(f"file={path.name}")
        emit(f"system={system}")
        emit(f"data_lines={lines}")
        emit("columns=" + ",".join(COLUMNS_BY_SYSTEM[system]))
    return status


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge any mixture of export files into one normalized CSV."""
    settings = load_settings()
    paths = [Path(name) for name in args.files]
    try:
        records = build_records(paths, settings)
    except (LedgerParseError, OSError) as exc:
        _log.error("ingest failed: %s", exc)
        return 1
    out_path = Path(args.out)
    write_records(out_path, records)
    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals from a normalized file, grouped by account or by month."""
    settings = load_settings()
    try:
        records = read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.error("report failed: %s", exc)
        return 1

    sep = report.FIELD_SEPARATOR
    if args.by == "account":
        emit(sep.join(["account_code", "account_name", "total"]))
        for code, name, total in report.totals_by_account(records, settings):
            emit(sep.join([code, name, settings.format_amount(total)]))
    else:
        emit(sep.join(["month", "total"]))
        for month, total in report.totals_by_month(records, settings):
            emit(sep.join([month, settings.format_amount(total)]))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print account/month combinations where the systems disagree."""
    settings = load_settings()
    try:
        records = read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.error("reconcile failed: %s", exc)
        return 1

    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    mismatches = reconcile.find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(reconcile.format_mismatch(mismatch))
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0
    had_unreadable_file = False
    for name in args.files:
        path = Path(name)
        try:
            checked, rejected = validate_file(path, settings)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            had_unreadable_file = True
            continue
        total_checked += checked
        total_rejected += rejected

    emit(f"checked={total_checked} rejected={total_rejected}")
    if had_unreadable_file or total_rejected > 0:
        return 2
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is not None:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
