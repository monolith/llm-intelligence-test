"""The ``python -m ledgerkit`` command line.

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

from ledgerkit import __version__
from ledgerkit.build import record_from_row
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import io as records_io
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, read_rows, system_a, system_b, system_c
from ledgerkit.reconcile import SYSTEMS_IN_ORDER, find_mismatches
from ledgerkit.report import round_total, totals_by_account, totals_by_month
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

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
        help="read settings from PATH instead of the usual place, for this run only",
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
    ingest_parser.add_argument("--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", choices=("account", "month"), required=True, help="which grouping to total by")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="accepted for compatibility; refunds are always included"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument("--tolerance", type=Decimal, default=None, metavar="N", help="dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows")
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
    """Merge any number of export files, from any of the three systems, into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1
        try:
            records.extend(record_from_row(system, row, settings) for row in raw_rows)
        except LedgerParseError as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    normalized = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    records_io.write_records(out_path, normalized)
    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month, read from a normalized file."""
    settings = load_settings()
    try:
        records = records_io.read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot report on %s: %s", args.records, exc)
        return 1

    if args.by == "account":
        emit("account_code;account_name;total")
        for row in totals_by_account(records, include_refunds=True):
            total = round_total(row.total, settings.decimals)
            emit(f"{row.account_code};{row.account_name};{settings.format_amount(total)}")
    else:
        emit("month;total")
        for row in totals_by_month(records, include_refunds=True):
            total = round_total(row.total, settings.decimals)
            emit(f"{row.month};{settings.format_amount(total)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree, from a normalized file."""
    settings = load_settings()
    try:
        records = records_io.read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot reconcile %s: %s", args.records, exc)
        return 1

    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        parts = " ".join(
            f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
            for system in SYSTEMS_IN_ORDER
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread():.2f} {parts}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files without writing anything."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0
    had_unreadable_file = False
    for name in args.files:
        path = Path(name)
        try:
            outcome = validate_file(path, settings)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            had_unreadable_file = True
            continue
        total_checked += outcome.checked
        total_rejected += outcome.rejected

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected or had_unreadable_file else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
