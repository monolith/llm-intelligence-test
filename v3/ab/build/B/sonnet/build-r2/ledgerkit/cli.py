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
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import csvio
from ledgerkit.core.build import read_records as build_records
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError
from ledgerkit.core.validation import validate_file
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

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

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge exports from any of the three systems into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument(
        "--by", choices=("account", "month"), required=True, help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include postings with a negative amount in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=Decimal,
        default=None,
        metavar="N",
        help="dollars; two systems agree when their totals differ by no more than this",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows in export files")
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
    """Merge any number of export files into one normalized CSV."""
    settings = load_settings()
    records = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(build_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError, ValueError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    normalized = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    csvio.write_records(out_path, normalized)
    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account code or by month from a normalized file."""
    settings = load_settings()
    records_path = Path(args.records)
    try:
        records = csvio.read_records(records_path)
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot report on %s: %s", records_path, exc)
        return 1

    if not args.include_refunds:
        records = [record for record in records if not record.is_refund()]

    if args.by == "account":
        totals: dict[str, Decimal] = {}
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
            names[record.account_code] = record.account_name
        emit("account_code,account_name,total")
        for code in sorted(totals):
            emit(f"{code},{names[code]},{settings.format_amount(totals[code])}")
    else:
        month_totals: dict[str, Decimal] = {}
        for record in records:
            month = record.month()
            month_totals[month] = month_totals.get(month, Decimal(0)) + record.amount
        emit("month,total")
        for month in sorted(month_totals):
            emit(f"{month},{settings.format_amount(month_totals[month])}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    records_path = Path(args.records)
    try:
        records = csvio.read_records(records_path)
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot reconcile %s: %s", records_path, exc)
        return 1

    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        by_system = groups.setdefault(key, {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[tuple[str, str, Decimal, dict[str, Decimal]]] = []
    for code, month in sorted(groups):
        by_system = groups[(code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append((code, month, spread, by_system))

    for code, month, spread, by_system in mismatches:
        parts = [
            f"{system}={by_system[system]:.2f}" if system in by_system else f"{system}=-"
            for system in ("A", "B", "C")
        ]
        emit(f"MISMATCH {code} {month} spread={spread:.2f} {' '.join(parts)}")
    emit(f"mismatches={len(mismatches)}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0
    unreadable = False

    for name in args.files:
        path = Path(name)
        try:
            result = validate_file(path, settings.account_code_pattern)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue
        total_checked += result.checked
        total_rejected += result.rejected

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if (total_rejected > 0 or unreadable) else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
