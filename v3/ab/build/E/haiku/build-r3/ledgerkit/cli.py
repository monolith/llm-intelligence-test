"""The ``python -m ledgerkit`` command line.

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
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, read_rows, count_data_lines, system_a, system_b, system_c

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
    parser.add_argument("--config", type=str, help="Path to settings TOML file")

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized CSV")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to ingest")
    ingest_parser.add_argument("--out", type=str, default="out/records.csv", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping method")
    report_parser.add_argument("--records", type=str, default="out/records.csv", help="normalized records file")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find disagreements between systems")
    reconcile_parser.add_argument("--records", type=str, default="out/records.csv", help="normalized records file")
    reconcile_parser.add_argument("--tolerance", type=float, help="tolerance for mismatches")
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


def _parse_system_a_row(raw: dict[str, str], unknown_label: str) -> Record:
    """Convert a System A raw row to a Record."""
    amount = Decimal(raw["amount"].strip())
    date = datetime.strptime(raw["posted_on"].strip(), "%Y-%m-%d").date()
    return Record(
        record_id=raw["entry_id"],
        source_system="A",
        date=date,
        account_code=raw["account"],
        account_name=account_name(raw["account"], unknown_label),
        description=raw["memo"],
        amount=amount,
    )


def _parse_system_b_row(raw: dict[str, str], unknown_label: str) -> Record:
    """Convert a System B raw row to a Record."""
    from ledgerkit.parsers.system_b import to_major_units
    amount = to_major_units(raw["amount"])
    date = datetime.strptime(raw["value_date"].strip(), "%Y-%m-%d").date()
    return Record(
        record_id=raw["doc_no"],
        source_system="B",
        date=date,
        account_code=raw["acct"],
        account_name=account_name(raw["acct"], unknown_label),
        description=raw["descr"],
        amount=amount,
    )


def _parse_system_c_row(raw: dict[str, str], unknown_label: str) -> Record:
    """Convert a System C raw row to a Record."""
    amount = Decimal(raw["gross_amount"].strip())
    # System C date format is DD/MM/YYYY
    date = datetime.strptime(raw["txn_date"].strip(), "%d/%m/%Y").date()
    return Record(
        record_id=raw["ref"],
        source_system="C",
        date=date,
        account_code=raw["ledger_acct"],
        account_name=account_name(raw["ledger_acct"], unknown_label),
        description=raw["narrative"],
        amount=amount,
    )


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports into one normalized CSV."""
    settings = load_settings()
    all_records: list[Record] = []

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            continue

        for raw in raw_rows:
            try:
                if system == "A":
                    record = _parse_system_a_row(raw, settings.unknown_account_label)
                elif system == "B":
                    record = _parse_system_b_row(raw, settings.unknown_account_label)
                else:
                    record = _parse_system_c_row(raw, settings.unknown_account_label)
                all_records.append(record)
            except (ValueError, KeyError) as exc:
                _log.warning("cannot parse row from %s: %s", path, exc)
                continue

    normalized = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.exists():
        _log.error("records file not found: %s", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return 1
        for row in reader:
            amount = Decimal(row["amount"])
            date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            records.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date,
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=amount,
                )
            )

    if args.by == "account":
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for record in records:
            totals[(record.account_code, record.account_name)] += record.amount

        emit("account_code;account_name;total")
        for (code, name), total in sorted(totals.items()):
            formatted = settings.format_amount(total)
            emit(f"{code};{name};{formatted}")
    else:
        month_totals: dict[str, Decimal] = defaultdict(Decimal)
        for record in records:
            month = record.month()
            month_totals[month] += record.amount

        emit("month;total")
        for month in sorted(month_totals.keys()):
            formatted = settings.format_amount(month_totals[month])
            emit(f"{month};{formatted}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find disagreements between systems."""
    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance

    records_path = Path(args.records)
    if not records_path.exists():
        _log.error("records file not found: %s", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return 1
        for row in reader:
            amount = Decimal(row["amount"])
            date = datetime.strptime(row["date"], "%Y-%m-%d").date()
            records.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date,
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=amount,
                )
            )

    group_totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        month = record.month()
        key = (record.account_code, month, record.source_system)
        group_totals[key] += record.amount

    account_months: dict[tuple[str, str], set[str]] = defaultdict(set)
    for account_code, month, system in group_totals:
        account_months[(account_code, month)].add(system)

    mismatches = []
    for (account_code, month), systems in account_months.items():
        if len(systems) < 2:
            continue

        totals = {}
        for system in ["A", "B", "C"]:
            key = (account_code, month, system)
            if key in group_totals:
                totals[system] = group_totals[key]

        values = list(totals.values())
        spread = max(values) - min(values)

        if spread > tolerance:
            parts = [f"MISMATCH {account_code} {month} spread={settings.format_amount(spread)}"]
            for system in ["A", "B", "C"]:
                if system in totals:
                    parts.append(f"{system}={settings.format_amount(totals[system])}")
                else:
                    parts.append(f"{system}=-")
            mismatches.append(" ".join(parts))

    mismatches.sort()
    for line in mismatches:
        emit(line)

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files without writing."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)

    total_checked = 0
    total_rejected = 0

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            total_rejected += 1
            continue

        try:
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            total_rejected += len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])
            continue

        for raw in raw_rows:
            total_checked += 1
            rejected = False

            if system == "A":
                parser_func = _parse_system_a_row
                date_field = "posted_on"
                date_format = "%Y-%m-%d"
                amount_field = "amount"
                account_field = "account"
            elif system == "B":
                parser_func = _parse_system_b_row
                date_field = "value_date"
                date_format = "%Y-%m-%d"
                amount_field = "amount"
                account_field = "acct"
            else:
                parser_func = _parse_system_c_row
                date_field = "txn_date"
                date_format = "%d/%m/%Y"
                amount_field = "gross_amount"
                account_field = "ledger_acct"

            try:
                datetime.strptime(raw[date_field].strip(), date_format)
            except (ValueError, KeyError):
                _log.warning("%s: cannot parse date %r", path, raw.get(date_field))
                rejected = True

            try:
                Decimal(raw[amount_field].strip())
            except (ValueError, KeyError, InvalidOperation):
                _log.warning("%s: cannot parse amount %r", path, raw.get(amount_field))
                rejected = True

            account_code = raw.get(account_field, "").strip().upper()
            if not account_pattern.match(account_code):
                _log.warning("%s: account code %r does not match pattern", path, account_code)
                rejected = True

            if rejected:
                total_rejected += 1

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    argv_list = list(argv) if argv is not None else None

    config_path = None
    if argv_list:
        if "--config" in argv_list:
            idx = argv_list.index("--config")
            if idx + 1 < len(argv_list):
                config_path = argv_list[idx + 1]

    if config_path:
        os.environ[CONFIG_ENV_VAR] = config_path

    parser = build_parser()
    args = parser.parse_args(argv_list)
    handler = args.handler
    return int(handler(args))
