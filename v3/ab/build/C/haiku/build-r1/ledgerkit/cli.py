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
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.readers import read_records_from_file
from ledgerkit.core.records import LedgerParseError, RECORD_COLUMNS
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
    parser.add_argument("--config", type=str, help="settings file to use instead of the default")

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge exports into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument("--out", type=str, default="out/records.csv", help="output file")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser(
        "report", help="print totals by account or by month"
    )
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping")
    report_parser.add_argument("--records", type=str, default="out/records.csv", help="input file")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="find account-month combinations where systems disagree"
    )
    reconcile_parser.add_argument("--records", type=str, default="out/records.csv", help="input file")
    reconcile_parser.add_argument("--tolerance", type=float, help="tolerance in dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows"
    )
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="files to validate")
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
    """Merge exports into one normalized CSV."""
    settings = load_settings()
    all_records: list = []

    for file_name in args.files:
        path = Path(file_name)
        try:
            records = read_records_from_file(path, settings.unknown_account_label)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot read %s: %s", path, exc)
            return 1

    normalized = normalize(all_records, keep_refunds=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    from datetime import date as date_class

    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.exists():
        _log.error("file not found: %s", records_path)
        return 1

    records: list = []
    with records_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(RECORD_COLUMNS):
            _log.error("invalid normalized file format")
            return 1
        for row in reader:
            records.append({
                "account_code": row["account_code"],
                "account_name": row["account_name"],
                "date": date_class.fromisoformat(row["date"]),
                "amount": Decimal(row["amount"]),
            })

    if args.by == "account":
        by_account: dict = defaultdict(lambda: {"name": "", "total": Decimal("0")})
        for rec in records:
            by_account[rec["account_code"]]["name"] = rec["account_name"]
            by_account[rec["account_code"]]["total"] += rec["amount"]

        emit(";".join(["account_code", "account_name", "total"]))
        for code in sorted(by_account.keys()):
            data = by_account[code]
            emit(f"{code};{data['name']};{settings.format_amount(data['total'])}")
    else:  # by month
        by_month: dict = defaultdict(lambda: Decimal("0"))
        for rec in records:
            month = f"{rec['date'].year:04d}-{rec['date'].month:02d}"
            by_month[month] += rec["amount"]

        emit(";".join(["month", "total"]))
        for month in sorted(by_month.keys()):
            emit(f"{month};{settings.format_amount(by_month[month])}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account-month combinations where systems disagree."""
    from datetime import date as date_class

    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    records_path = Path(args.records)

    if not records_path.exists():
        _log.error("file not found: %s", records_path)
        return 1

    records: list = []
    with records_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(RECORD_COLUMNS):
            _log.error("invalid normalized file format")
            return 1
        for row in reader:
            records.append({
                "account_code": row["account_code"],
                "date": date_class.fromisoformat(row["date"]),
                "source_system": row["source_system"],
                "amount": Decimal(row["amount"]),
            })

    # Group by (account_code, month, source_system) and sum amounts
    by_group: dict = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    for rec in records:
        month = f"{rec['date'].year:04d}-{rec['date'].month:02d}"
        key = (rec["account_code"], month)
        by_group[key][rec["source_system"]] += rec["amount"]

    # Find mismatches
    mismatches: list = []
    for (account_code, month), systems in by_group.items():
        if len(systems) < 2:
            continue
        amounts = list(systems.values())
        spread = max(amounts) - min(amounts)
        if spread > tolerance:
            mismatches.append((account_code, month, systems))

    # Sort and output
    mismatches.sort(key=lambda x: (x[0], x[1]))
    for account_code, month, systems in mismatches:
        parts = [f"MISMATCH {account_code} {month} spread={settings.format_amount(max(systems.values()) - min(systems.values()))}"]
        for sys in "ABC":
            if sys in systems:
                parts.append(f" {sys}={settings.format_amount(systems[sys])}")
            else:
                parts.append(" -")
        emit("".join(parts))

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    total_rows = 0
    rejected_rows = 0

    for file_name in args.files:
        path = Path(file_name)
        if not path.exists():
            _log.warning("file not found: %s", path)
            return 2

        try:
            system = detect_system(path)
        except LedgerParseError as exc:
            _log.warning("%s: %s", path, exc)
            return 2

        try:
            if system == "A":
                rows = system_a.read_rows(path)
            elif system == "B":
                rows = system_b.read_rows(path)
            else:
                rows = system_c.read_rows(path)
        except LedgerParseError as exc:
            _log.warning("%s: %s", path, exc)
            return 2

        # Validate each row
        for row in rows:
            total_rows += 1
            try:
                if system == "A":
                    date_str = row["posted_on"]
                    amount_str = row["amount"]
                    account_str = row["account"]
                elif system == "B":
                    date_str = row["value_date"]
                    amount_str = row["amount"]
                    account_str = row["acct"]
                else:
                    date_str = row["txn_date"]
                    amount_str = row["gross_amount"]
                    account_str = row["ledger_acct"]

                # Check account code pattern
                if not pattern.match(account_str.strip().upper()):
                    _log.warning("%s: account code %r does not match pattern", path, account_str)
                    rejected_rows += 1
                    continue

                # Try parsing date
                if system == "A" or system == "B":
                    datetime.strptime(date_str.strip(), "%Y-%m-%d")
                else:
                    datetime.strptime(date_str.strip(), "%d/%m/%Y")

                # Try parsing amount
                Decimal(amount_str.strip())
            except Exception as exc:
                _log.warning("%s: %s", path, exc)
                rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if hasattr(args, "config") and args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config
    handler = args.handler
    return int(handler(args))
