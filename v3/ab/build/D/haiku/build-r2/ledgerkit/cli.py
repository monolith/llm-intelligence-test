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
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings, CONFIG_ENV_VAR
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


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="settings file to use instead of the default",
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
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output file")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="grouping")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="records file")
    report_parser.add_argument("--include-refunds", action="store_true", help="include negative amounts")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find account/month mismatches")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="records file")
    reconcile_parser.add_argument("--tolerance", metavar="N", help="tolerance in dollars")
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


def _row_to_record(row: dict[str, str], system: str, settings) -> Record:
    """Convert a raw row to a Record."""
    if system == "A":
        return Record(
            record_id=row["entry_id"],
            source_system="A",
            date=datetime.strptime(row["posted_on"], "%Y-%m-%d").date(),
            account_code=row["account"],
            account_name=account_name(row["account"], settings.unknown_account_label),
            description=row["memo"],
            amount=Decimal(row["amount"]),
        )
    elif system == "B":
        return Record(
            record_id=row["doc_no"],
            source_system="B",
            date=datetime.strptime(row["value_date"], "%Y-%m-%d").date(),
            account_code=row["acct"],
            account_name=account_name(row["acct"], settings.unknown_account_label),
            description=row["descr"],
            amount=system_b.to_major_units(row["amount"]),
        )
    else:  # system == "C"
        return Record(
            record_id=row["ref"],
            source_system="C",
            date=datetime.strptime(row["txn_date"], "%d/%m/%Y").date(),
            account_code=row["ledger_acct"],
            account_name=account_name(row["ledger_acct"], settings.unknown_account_label),
            description=row["narrative"],
            amount=Decimal(row["gross_amount"]),
        )


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge export files into one normalized CSV."""
    settings = load_settings()
    all_records: list[Record] = []

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 1

        for row in raw_rows:
            try:
                record = _row_to_record(row, system, settings)
                all_records.append(record)
            except (ValueError, KeyError) as exc:
                _log.warning("cannot convert row from %s: %s", path, exc)
                return 1

    records = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())

    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.is_file():
        _log.warning("records file %s not found", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(RECORD_COLUMNS):
            _log.warning("unexpected header in %s", records_path)
            return 1

        for row in reader:
            amount = Decimal(row["amount"])
            if amount < 0 and not args.include_refunds:
                continue
            record = Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=amount,
            )
            records.append(record)

    if args.by == "account":
        by_account: dict[str, tuple[str, Decimal]] = {}
        for record in records:
            key = record.account_code
            if key not in by_account:
                by_account[key] = (record.account_name, Decimal(0))
            name, total = by_account[key]
            by_account[key] = (name, total + record.amount)

        emit("account_code,account_name,total")
        for code in sorted(by_account.keys()):
            name, total = by_account[code]
            rounded = total.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{code},{name},{settings.format_amount(rounded)}")
    else:  # by month
        by_month: dict[str, Decimal] = defaultdict(Decimal)
        for record in records:
            month = record.month()
            by_month[month] += record.amount

        emit("month,total")
        for month in sorted(by_month.keys()):
            total = by_month[month]
            rounded = total.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(rounded)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account/month combinations where systems disagree."""
    settings = load_settings()
    tolerance = Decimal(args.tolerance) if args.tolerance else settings.tolerance

    records_path = Path(args.records)
    if not records_path.is_file():
        _log.warning("records file %s not found", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(RECORD_COLUMNS):
            _log.warning("unexpected header in %s", records_path)
            return 1

        for row in reader:
            record = Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            records.append(record)

    by_combo: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        key = (record.account_code, record.month())
        by_combo[key][record.source_system] += record.amount

    mismatches = []
    for (code, month), systems in by_combo.items():
        if len(systems) < 2:
            continue

        values = sorted(systems.values())
        spread = values[-1] - values[0]

        if spread > tolerance:
            systems_list = ["A", "B", "C"]
            amounts_str = " ".join(
                f"{sys}={systems[sys]:.2f}" if sys in systems else f"{sys}=-"
                for sys in systems_list
            )
            mismatches.append((code, month, spread, amounts_str))

    mismatches.sort(key=lambda x: (x[0], x[1]))

    for code, month, spread, amounts_str in mismatches:
        emit(f"MISMATCH {code} {month} spread={spread:.2f} {amounts_str}")

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files without parsing full data."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)

    total_rows = 0
    rejected_rows = 0

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        raw_rows = []
        try:
            raw_rows = read_rows(path)
        except LedgerParseError as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        for row in raw_rows:
            total_rows += 1
            try:
                if system == "A":
                    datetime.strptime(row["posted_on"], "%Y-%m-%d")
                    Decimal(row["amount"])
                    code = row["account"]
                elif system == "B":
                    datetime.strptime(row["value_date"], "%Y-%m-%d")
                    int(row["amount"])
                    code = row["acct"]
                else:  # C
                    datetime.strptime(row["txn_date"], "%d/%m/%Y")
                    Decimal(row["gross_amount"])
                    code = row["ledger_acct"]

                if not account_pattern.match(code):
                    _log.warning("%s: account code %r does not match pattern", path.name, code)
                    rejected_rows += 1
            except (ValueError, KeyError, InvalidOperation) as exc:
                _log.warning("%s: %s", path.name, exc)
                rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    argv_list = list(argv) if argv is not None else None

    if argv_list and "--config" in argv_list:
        idx = argv_list.index("--config")
        if idx + 1 < len(argv_list):
            os.environ[CONFIG_ENV_VAR] = argv_list[idx + 1]
            argv_list = argv_list[:idx] + argv_list[idx + 2:]

    parser = build_parser()
    args = parser.parse_args(argv_list)
    handler = args.handler
    return int(handler(args))
