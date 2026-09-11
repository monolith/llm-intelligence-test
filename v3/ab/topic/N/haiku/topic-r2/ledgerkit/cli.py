"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import os

from ledgerkit import __version__
from ledgerkit.config import load_settings, CONFIG_ENV_VAR
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS
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
        type=str,
        metavar="PATH",
        help="load settings from this file instead of the default",
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
        "ingest", help="merge exports into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out",
        type=str,
        default="out/records.csv",
        metavar="PATH",
        help="where to write the normalized CSV (default: out/records.csv)",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser(
        "report", help="print totals by account or by month"
    )
    report_parser.add_argument(
        "--by",
        type=str,
        required=True,
        choices=["account", "month"],
        metavar="account|month",
        help="group totals by account or month",
    )
    report_parser.add_argument(
        "--records",
        type=str,
        default="out/records.csv",
        metavar="PATH",
        help="normalized file to read (default: out/records.csv)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include negative amounts in totals (now default; kept for compatibility)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="find where systems disagree"
    )
    reconcile_parser.add_argument(
        "--records",
        type=str,
        default="out/records.csv",
        metavar="PATH",
        help="normalized file to read (default: out/records.csv)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=float,
        metavar="N",
        help="tolerance in dollars (default from settings)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows"
    )
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


def _build_records_from_rows(system: str, rows: list[dict[str, str]], settings_unknown_label: str) -> list[Record]:
    """Convert raw rows from a system into Record objects."""
    records: list[Record] = []
    for row in rows:
        try:
            if system == "A":
                date = datetime.fromisoformat(row["posted_on"]).date()
                amount = Decimal(row["amount"].strip())
                record_id = row["entry_id"].strip()
                acct = row["account"].strip().upper()
                desc = row["memo"]
            elif system == "B":
                date = datetime.fromisoformat(row["value_date"]).date()
                amount = system_b.to_major_units(row["amount"])
                record_id = row["doc_no"].strip()
                acct = row["acct"].strip().upper()
                desc = row["descr"]
            else:  # system == "C"
                date = datetime.strptime(row["txn_date"].strip(), "%d/%m/%Y").date()
                amount = Decimal(row["gross_amount"].strip())
                record_id = row["ref"].strip()
                acct = row["ledger_acct"].strip().upper()
                desc = row["narrative"]

            acct_name = account_name(acct, settings_unknown_label)
            record = Record(
                record_id=record_id,
                source_system=system,
                date=date,
                account_code=acct,
                account_name=acct_name,
                description=desc,
                amount=amount,
            )
            records.append(record)
        except (ValueError, KeyError) as e:
            _log.warning("could not build record from row in system %s: %s", system, e)
            continue
    return records


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge export files into one normalized CSV."""
    settings = load_settings()
    all_records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
            records = _build_records_from_rows(system, raw_rows, settings.unknown_account_label)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    normalized = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    row_count = len(normalized)
    emit(f"wrote={row_count} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    settings = load_settings()
    records_path = Path(args.records)

    try:
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(RECORD_COLUMNS):
                _log.error("invalid record file header")
                return 1
            records = []
            for row in reader:
                record = Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=datetime.fromisoformat(row["date"]).date(),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                )
                records.append(record)
    except (OSError, ValueError) as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        totals: dict[str, tuple[str, Decimal]] = {}
        for record in records:
            key = record.account_code
            if key not in totals:
                totals[key] = (record.account_name, Decimal(0))
            name, total = totals[key]
            totals[key] = (name, total + record.amount)

        emit("account_code,account_name,total")
        for code in sorted(totals.keys()):
            name, total = totals[code]
            rounded = total.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{code},{name},{settings.format_amount(rounded)}")

    else:  # args.by == "month"
        totals_by_month: dict[str, Decimal] = {}
        for record in records:
            month = record.month()
            if month not in totals_by_month:
                totals_by_month[month] = Decimal(0)
            totals_by_month[month] += record.amount

        emit("month,total")
        for month in sorted(totals_by_month.keys()):
            total = totals_by_month[month]
            rounded = total.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(rounded)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month combinations where systems disagree."""
    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance

    records_path = Path(args.records)

    try:
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(RECORD_COLUMNS):
                _log.error("invalid record file header")
                return 1
            records = []
            for row in reader:
                record = Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=datetime.fromisoformat(row["date"]).date(),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                )
                records.append(record)
    except (OSError, ValueError) as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    from collections import defaultdict

    by_acct_month_system: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    all_acct_months: set[tuple[str, str]] = set()

    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        by_acct_month_system[key] += record.amount
        all_acct_months.add((record.account_code, record.month()))

    mismatches: list[str] = []

    for acct, month in sorted(all_acct_months):
        systems_for_this = [
            (system, by_acct_month_system.get((acct, month, system), Decimal(0)))
            for system in ["A", "B", "C"]
        ]
        posted = [s for s, amt in systems_for_this if (acct, month, s) in by_acct_month_system]

        if len(posted) < 2:
            continue

        amounts = [amt for _, amt in systems_for_this]
        spread = max(amounts) - min(amounts)

        if spread > tolerance:
            parts = [f"MISMATCH {acct} {month} spread={spread:.2f}"]
            for system, amt in systems_for_this:
                if system in posted:
                    parts.append(f"{system}={amt:.2f}")
                else:
                    parts.append(f"{system}=-")
            mismatches.append(" ".join(parts))

    for line in mismatches:
        emit(line)

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)

    total_checked = 0
    total_rejected = 0
    had_error = False

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            had_error = True
            continue

        try:
            raw_rows = read_rows(path)
        except LedgerParseError as exc:
            _log.warning("cannot read %s: %s", path, exc)
            had_error = True
            continue

        for row in raw_rows:
            total_checked += 1
            rejected = False
            reason = None

            try:
                if system == "A":
                    date_str = row.get("posted_on", "").strip()
                    datetime.fromisoformat(date_str)
                    amount_str = row.get("amount", "").strip()
                    Decimal(amount_str)
                    acct = row.get("account", "").strip()
                elif system == "B":
                    date_str = row.get("value_date", "").strip()
                    datetime.fromisoformat(date_str)
                    amount_str = row.get("amount", "").strip()
                    int(amount_str)
                    acct = row.get("acct", "").strip()
                else:  # system == "C"
                    date_str = row.get("txn_date", "").strip()
                    datetime.strptime(date_str, "%d/%m/%Y")
                    amount_str = row.get("gross_amount", "").strip()
                    Decimal(amount_str)
                    acct = row.get("ledger_acct", "").strip()

                if not pattern.match(acct):
                    rejected = True
                    reason = f"account code {acct!r} does not match pattern"
            except (ValueError, KeyError) as e:
                rejected = True
                reason = str(e)

            if rejected:
                total_rejected += 1
                _log.warning("row rejected in %s: %s", path, reason)

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if (total_rejected > 0 or had_error) else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if hasattr(args, "config") and args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
