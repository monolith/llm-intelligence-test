"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings, config_path
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, read_records, system_a, system_b, system_c

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
    parser.add_argument("--config", type=Path, metavar="PATH", help="config file to use")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized file")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to read")
    ingest_parser.add_argument("--out", type=Path, default=Path("out/records.csv"), help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to validate")
    validate_parser.set_defaults(handler=cmd_validate)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="grouping method")
    report_parser.add_argument("--records", type=Path, default=Path("out/records.csv"), help="normalized file to read")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where systems disagree")
    reconcile_parser.add_argument("--records", type=Path, default=Path("out/records.csv"), help="normalized file to read")
    reconcile_parser.add_argument("--tolerance", type=Decimal, help="tolerance for differences")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

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
    """Read exports and write one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    for file_path in args.files:
        path = Path(file_path)
        try:
            file_records = read_records(path, settings.unknown_account_label)
            records.extend(file_records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 1

    normalized = normalize(records, keep_refunds=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "source_system", "date", "account_code", "account_name", "description", "amount"])
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {args.out}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check exports without writing anything."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except LedgerParseError as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        pattern = re.compile(settings.account_code_pattern)
        raw_rows = None
        try:
            if system == "A":
                raw_rows = system_a.read_rows(path)
            elif system == "B":
                raw_rows = system_b.read_rows(path)
            else:
                raw_rows = system_c.read_rows(path)
        except LedgerParseError as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        for row_num, raw_row in enumerate(raw_rows, start=1):
            try:
                if system == "A":
                    system_a.to_record(raw_row, settings.unknown_account_label)
                elif system == "B":
                    system_b.to_record(raw_row, settings.unknown_account_label)
                else:
                    system_c.to_record(raw_row, settings.unknown_account_label)

                account = raw_row.get("account" if system == "A" else "acct" if system == "B" else "ledger_acct", "")
                if not pattern.match(account.strip()):
                    _log.warning("%s line %d: account code %r does not match pattern", path.name, row_num + 2, account)
                    total_rejected += 1
                total_checked += 1
            except LedgerParseError as exc:
                _log.warning("%s line %d: %s", path.name, row_num + 2, exc)
                total_rejected += 1
                total_checked += 1

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected > 0 else 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    settings = load_settings()
    if not args.records.is_file():
        _log.warning("records file %s not found", args.records)
        return 1

    records: list[Record] = []
    with args.records.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            ))

    if args.by == "account":
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for record in records:
            totals[(record.account_code, record.account_name)] += record.amount

        emit("account_code;account_name;total")
        for (code, name), total in sorted(totals.items()):
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{code};{name};{formatted}")
    else:
        totals_month: dict[str, Decimal] = defaultdict(Decimal)
        for record in records:
            totals_month[record.month()] += record.amount

        emit("month;total")
        for month in sorted(totals_month.keys()):
            formatted = settings.format_amount(totals_month[month].quantize(Decimal(10) ** -settings.decimals))
            emit(f"{month};{formatted}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month combinations where systems disagree."""
    settings = load_settings()
    if not args.records.is_file():
        _log.warning("records file %s not found", args.records)
        return 1

    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    records: list[Record] = []
    with args.records.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            ))

    by_account_month_system: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        by_account_month_system[key] += record.amount

    def format_two_decimals(value: Decimal) -> str:
        return f"{value:.2f}"

    mismatches = 0
    for account_code in sorted({key[0] for key in by_account_month_system.keys()}):
        for month in sorted({key[1] for key in by_account_month_system.keys() if key[0] == account_code}):
            systems_in_key = {key[2] for key in by_account_month_system.keys() if key[0] == account_code and key[1] == month}
            if len(systems_in_key) < 2:
                continue

            totals_by_system = {}
            for system in systems_in_key:
                totals_by_system[system] = by_account_month_system[(account_code, month, system)]

            values = list(totals_by_system.values())
            spread = max(values) - min(values)
            if spread > tolerance:
                mismatches += 1
                parts = []
                for system in sorted(systems_in_key):
                    parts.append(f"{system}={format_two_decimals(totals_by_system[system])}")
                missing = {"A", "B", "C"} - systems_in_key
                for system in sorted(missing):
                    parts.append(f"{system}=-")
                emit(f"MISMATCH {account_code} {month} spread={format_two_decimals(spread)} {' '.join(parts)}")

    emit(f"mismatches={mismatches}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if hasattr(args, "config") and args.config:
        import os
        os.environ["LEDGERKIT_CONFIG"] = str(args.config)

    handler = args.handler
    return int(handler(args))
