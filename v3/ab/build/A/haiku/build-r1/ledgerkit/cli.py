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
from collections.abc import Sequence
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS, sort_key
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import count_data_lines, detect_system, read_rows, system_a, system_b, system_c

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


def _rows_to_records(system: str, rows: list[dict[str, str]], settings) -> list[Record]:
    """Convert raw rows from a system to Record objects."""
    records: list[Record] = []
    for row in rows:
        try:
            if system == "A":
                record = Record(
                    record_id=row["entry_id"],
                    source_system="A",
                    date=datetime.strptime(row["posted_on"], "%Y-%m-%d").date(),
                    account_code=row["account"],
                    account_name=account_name(row["account"], settings.unknown_account_label),
                    description=row["memo"],
                    amount=Decimal(row["amount"]),
                )
            elif system == "B":
                record = Record(
                    record_id=row["doc_no"],
                    source_system="B",
                    date=datetime.strptime(row["value_date"], "%Y-%m-%d").date(),
                    account_code=row["acct"],
                    account_name=account_name(row["acct"], settings.unknown_account_label),
                    description=row["descr"],
                    amount=system_b.to_major_units(row["amount"]),
                )
            elif system == "C":
                record = Record(
                    record_id=row["ref"],
                    source_system="C",
                    date=datetime.strptime(row["txn_date"], "%d/%m/%Y").date(),
                    account_code=row["ledger_acct"],
                    account_name=account_name(row["ledger_acct"], settings.unknown_account_label),
                    description=row["narrative"],
                    amount=Decimal(row["gross_amount"]),
                )
            else:
                continue
            records.append(record)
        except (ValueError, KeyError) as exc:
            _log.warning("cannot convert row from system %s: %s", system, exc)
    return records


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )

    parser.add_argument(
        "--config",
        metavar="PATH",
        help="use alternate settings file",
        dest="config_override",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to read")
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or month")
    report_parser.add_argument("--by", metavar="account|month", required=True, help="grouping")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find account/month mismatches")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file")
    reconcile_parser.add_argument("--tolerance", metavar="N", type=float, help="tolerance in dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check files for malformed rows")
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
    """Read exports and write normalized CSV."""
    settings = load_settings()
    all_records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
            records = _rows_to_records(system, raw_rows, settings)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 1

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

    if not records_path.is_file():
        _log.warning("records file %s not found", records_path)
        return 1

    records: list[Record] = []
    try:
        with records_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                ))
    except (OSError, ValueError, KeyError) as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for record in records:
            key = (record.account_code, record.account_name)
            totals[key] += record.amount

        emit("account_code;account_name;total")
        for (code, name), total in sorted(totals.items()):
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{code};{name};{formatted}")
    elif args.by == "month":
        totals = defaultdict(Decimal)
        for record in records:
            month = record.month()
            totals[month] += record.amount

        emit("month;total")
        for month in sorted(totals.keys()):
            total = totals[month]
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{month};{formatted}")
    else:
        _log.error("--by must be 'account' or 'month'")
        return 1

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account/month pairs where systems disagree."""
    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    records_path = Path(args.records)

    if not records_path.is_file():
        _log.warning("records file %s not found", records_path)
        return 1

    records: list[Record] = []
    try:
        with records_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                ))
    except (OSError, ValueError, KeyError) as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    group_totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        group_totals[key] += record.amount

    mismatches: list[tuple[str, str, dict[str, Decimal]]] = []
    seen: set[tuple[str, str]] = set()

    for (account_code, month, _), _ in group_totals.items():
        if (account_code, month) in seen:
            continue
        seen.add((account_code, month))

        systems_with_data = set()
        system_totals: dict[str, Decimal] = {}
        for system in ["A", "B", "C"]:
            key = (account_code, month, system)
            if key in group_totals:
                systems_with_data.add(system)
                system_totals[system] = group_totals[key]

        if len(systems_with_data) < 2:
            continue

        values = [system_totals.get(s, Decimal(0)) for s in systems_with_data]
        max_val = max(values)
        min_val = min(values)
        spread = max_val - min_val

        if spread > tolerance:
            mismatches.append((account_code, month, system_totals))

    mismatches.sort(key=lambda x: (x[0], x[1]))

    for account_code, month, system_totals in mismatches:
        vals = []
        for s in ["A", "B", "C"]:
            if s in system_totals:
                vals.append(f"{s}={settings.format_amount(system_totals[s].quantize(Decimal('0.01')))}")
            else:
                vals.append(f"{s}=-")

        values = [system_totals.get(s, Decimal(0)) for s in system_totals.keys()]
        max_val = max(values)
        min_val = min(values)
        spread = max_val - min_val

        emit(f"MISMATCH {account_code} {month} spread={settings.format_amount(spread.quantize(Decimal('0.01')))} {' '.join(vals)}")

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)

    total_checked = 0
    total_rejected = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        for row_num, row in enumerate(raw_rows, start=2):
            total_checked += 1
            try:
                if system == "A":
                    date_val = row.get("posted_on", "")
                    datetime.strptime(date_val, "%Y-%m-%d")
                    amount_val = Decimal(row.get("amount", ""))
                    acct = row.get("account", "")
                elif system == "B":
                    date_val = row.get("value_date", "")
                    datetime.strptime(date_val, "%Y-%m-%d")
                    amount_val = system_b.to_major_units(row.get("amount", ""))
                    acct = row.get("acct", "")
                elif system == "C":
                    date_val = row.get("txn_date", "")
                    datetime.strptime(date_val, "%d/%m/%Y")
                    amount_val = Decimal(row.get("gross_amount", ""))
                    acct = row.get("ledger_acct", "")
                else:
                    total_rejected += 1
                    _log.warning("%s line %d: unknown system", path.name, row_num)
                    continue

                if not pattern.match(acct.strip()):
                    total_rejected += 1
                    _log.warning("%s line %d: account code %r does not match pattern", path.name, row_num, acct)
            except (ValueError, KeyError, LedgerParseError) as exc:
                total_rejected += 1
                _log.warning("%s line %d: %s", path.name, row_num, exc)

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config_override:
        os.environ["LEDGERKIT_CONFIG"] = args.config_override

    handler = args.handler
    return int(handler(args))
