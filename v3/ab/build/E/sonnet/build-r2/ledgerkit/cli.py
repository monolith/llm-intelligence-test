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

from ledgerkit import __version__, records_io, report, reconcile as reconcile_
from ledgerkit import validate as validate_
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

READERS_BY_SYSTEM = {
    "A": system_a.read_rows,
    "B": system_b.read_rows,
    "C": system_c.read_rows,
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
        help="read settings from PATH instead of config/settings.toml",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge export files from any of the three systems into one normalized CSV"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write the normalized CSV"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="how to group totals")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include postings with a negative amount in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account/month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", default=None, metavar="N", help="dollars; two systems agree within this much"
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files for malformed rows")
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
    """Merge one or more export files into a single normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            for row in READERS_BY_SYSTEM[system](path):
                records.append(records_io.record_from_row(system, row, settings.unknown_account_label))
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    normalized = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    count = records_io.write_normalized(out_path, normalized)
    emit(f"wrote={count} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = records_io.read_normalized(Path(args.records))
    if args.by == "account":
        totals = report.totals_by_account(records, include_refunds=args.include_refunds)
        emit("account_code,account_name,total")
        for code in sorted(totals):
            name, total = totals[code]
            emit(f"{code},{name},{settings.format_amount(total)}")
    else:
        totals = report.totals_by_month(records, include_refunds=args.include_refunds)
        emit("month,total")
        for month in sorted(totals):
            emit(f"{month},{settings.format_amount(totals[month])}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month combinations where the systems disagree."""
    settings = load_settings()
    if args.tolerance is not None:
        try:
            tolerance = Decimal(args.tolerance)
        except InvalidOperation as exc:
            raise SystemExit(f"{PROGRAM_NAME}: --tolerance must be a number, got {args.tolerance!r}") from exc
    else:
        tolerance = settings.tolerance

    records = records_io.read_normalized(Path(args.records))
    mismatches = reconcile_.find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(reconcile_.format_mismatch(mismatch))
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    checked = 0
    rejected = 0
    ok = True
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            file_checked, file_rejected = validate_.check_file(path, system, settings.account_code_pattern)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            ok = False
            continue
        checked += file_checked
        rejected += file_rejected

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected > 0 or not ok else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
