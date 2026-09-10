"""The ``python -m ledgerkit`` command line.

Only two subcommands are wired up so far, ``version`` and ``inspect``.  The rest
of the commands the operations team has asked for are written up in ``SPEC.md``
and are not implemented yet.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, read_csv
from ledgerkit.ingest import ingest_files
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches
from ledgerkit.report import totals_by_account, totals_by_month
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


def _decimal_argument(value: str) -> Decimal:
    """Parse a CLI argument as a :class:`~decimal.Decimal`, for argparse's ``type=``."""
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a decimal number") from exc


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
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
    ingest_parser.add_argument("--out", default="out/records.csv", metavar="PATH", help="where to write")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping to total by")
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="kept for compatibility; refunds are included in totals regardless",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=_decimal_argument, default=None, metavar="N", help="dollars of agreement allowed"
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
    records = ingest_files(paths, settings)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(RECORD_COLUMNS)]
    lines.extend(join_record(record.to_row()) for record in records)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized records file."""
    settings = load_settings()
    records = read_csv(Path(args.records))
    include_refunds = True

    if args.by == "account":
        emit("account_code;account_name;total")
        for code, name, total in totals_by_account(records, include_refunds=include_refunds):
            emit(f"{code};{name};{settings.format_amount(total)}")
    else:
        emit("month;total")
        for month, total in totals_by_month(records, include_refunds=include_refunds):
            emit(f"{month};{settings.format_amount(total)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print account/month combinations where the systems disagree."""
    settings = load_settings()
    records = read_csv(Path(args.records))
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        parts = " ".join(
            f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread():.2f} {parts}")
    emit(f"mismatches={len(mismatches)}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
    settings = load_settings()
    checked = 0
    rejected = 0
    had_failure = False

    for name in args.files:
        path = Path(name)
        try:
            result = validate_file(path, settings)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            had_failure = True
            continue
        checked += result.checked
        rejected += result.rejected

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or had_failure else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
