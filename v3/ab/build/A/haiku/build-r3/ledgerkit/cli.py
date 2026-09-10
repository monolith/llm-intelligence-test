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
import csv
import os
import re
from collections import defaultdict
from collections.abc import Sequence
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS
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
        help="read settings from this file instead of the default",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to ingest")
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", dest="by", required=True, choices=["account", "month"], help="grouping to total by")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file to read")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find where the systems disagree")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file to read")
    reconcile_parser.add_argument("--tolerance", metavar="N", type=Decimal, help="tolerance for agreement")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to validate")
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
    """Merge exports into one normalized file."""
    settings = load_settings()
    records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
            rows = system_a.read_rows(path) if system == "A" else (
                system_b.read_rows(path) if system == "B" else system_c.read_rows(path)
            )

            for row in rows:
                if system == "A":
                    record = system_a.row_to_record(row, settings.unknown_account_label)
                elif system == "B":
                    record = system_b.row_to_record(row, settings.unknown_account_label)
                else:
                    record = system_c.row_to_record(row, settings.unknown_account_label)
                records.append(record)

        except (LedgerParseError, OSError) as exc:
            _log.error("cannot read %s: %s", path, exc)
            return 1

    normalized = normalize(records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Totals by account or by month."""
    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.is_file():
        _log.error("records file not found: %s", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(RECORD_COLUMNS):
            _log.error("records file has wrong columns")
            return 1

        for row in reader:
            try:
                from datetime import date
                record = Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date.fromisoformat(row["date"]),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                )
                if args.include_refunds or record.amount >= 0:
                    records.append(record)
            except (ValueError, KeyError) as exc:
                _log.error("invalid record: %s", exc)
                return 1

    if args.by == "account":
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for record in records:
            totals[(record.account_code, record.account_name)] += record.amount

        emit("account_code,account_name,total")
        for (code, name), total in sorted(totals.items()):
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN))
            emit(f"{code},{name},{formatted}")

    else:  # month
        totals_by_month: dict[str, Decimal] = defaultdict(Decimal)
        for record in records:
            month = record.month()
            totals_by_month[month] += record.amount

        emit("month,total")
        for month in sorted(totals_by_month.keys()):
            total = totals_by_month[month]
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN))
            emit(f"{month},{formatted}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    records_path = Path(args.records)

    if not records_path.is_file():
        _log.error("records file not found: %s", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                from datetime import date
                record = Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date.fromisoformat(row["date"]),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                )
                records.append(record)
            except (ValueError, KeyError) as exc:
                _log.error("invalid record: %s", exc)
                return 1

    by_acct_month_system: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        by_acct_month_system[key] += record.amount

    by_acct_month: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for (acct, month, system), total in by_acct_month_system.items():
        by_acct_month[(acct, month)][system] = total

    mismatches = 0
    for (acct, month), system_totals in sorted(by_acct_month.items()):
        if len(system_totals) < 2:
            continue

        values = list(system_totals.values())
        spread = max(values) - min(values)
        if spread > tolerance:
            parts = []
            for system in ["A", "B", "C"]:
                if system in system_totals:
                    parts.append(f"{system}={system_totals[system]:.2f}")
                else:
                    parts.append(f"{system}=-")
            emit(f"MISMATCH {acct} {month} spread={spread:.2f} {' '.join(parts)}")
            mismatches += 1

    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)

    checked = 0
    rejected = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        try:
            rows = system_a.read_rows(path) if system == "A" else (
                system_b.read_rows(path) if system == "B" else system_c.read_rows(path)
            )
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        for row in rows:
            checked += 1
            try:
                if system == "A":
                    record = system_a.row_to_record(row, settings.unknown_account_label)
                elif system == "B":
                    record = system_b.row_to_record(row, settings.unknown_account_label)
                else:
                    record = system_c.row_to_record(row, settings.unknown_account_label)

                if not pattern.match(record.account_code):
                    _log.warning("%s: account code %s does not match pattern %s",
                                 path.name, record.account_code, settings.account_code_pattern)
                    rejected += 1
            except (LedgerParseError, ValueError) as exc:
                _log.warning("%s: %s", path.name, exc)
                rejected += 1

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config

    handler = args.handler
    return int(handler(args))
