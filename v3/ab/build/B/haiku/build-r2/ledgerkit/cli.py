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
import sys
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, Settings, load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write (default: out/records.csv)"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by",
        required=True,
        choices=["account", "month"],
        metavar="account|month",
        help="which grouping to total by",
    )
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="normalized file to read (default: out/records.csv)"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include refunds in totals (default: refunds are included)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="normalized file to read (default: out/records.csv)"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=float,
        metavar="N",
        help="tolerance in dollars (default: from settings)",
    )
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


def _rows_to_records(
    raw_rows: list[dict[str, str]], system: str, settings: Settings
) -> list[Record]:
    records: list[Record] = []
    for row in raw_rows:
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
            _log.warning("skipping malformed row from system %s: %s", system, exc)
    return records


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports into one normalized CSV."""
    settings = load_settings()
    all_records: list[Record] = []

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
            records = _rows_to_records(raw_rows, system, settings)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    from ledgerkit.core.normalize import normalize
    from ledgerkit.core.records import sort_key

    all_records.sort(key=sort_key)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in all_records:
            writer.writerow(record.to_row())

    emit(f"wrote={len(all_records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.exists():
        _log.warning("records file %s not found", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(RECORD_COLUMNS):
            _log.warning("records file has unexpected columns")
            return 1
        for row in reader:
            try:
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
            except (ValueError, KeyError) as exc:
                _log.warning("skipping malformed row: %s", exc)

    if args.by == "account":
        totals: dict[str, tuple[str, Decimal]] = {}
        for record in records:
            key = record.account_code
            if key not in totals:
                totals[key] = (record.account_name, Decimal(0))
            name, total = totals[key]
            totals[key] = (name, total + record.amount)

        emit(join_record(["account_code", "account_name", "total"], delimiter=";"))
        for code in sorted(totals.keys()):
            name, total = totals[code]
            formatted_total = settings.format_amount(total)
            emit(join_record([code, name, formatted_total], delimiter=";"))
    else:
        totals_by_month: dict[str, Decimal] = {}
        for record in records:
            month = record.month()
            totals_by_month[month] = totals_by_month.get(month, Decimal(0)) + record.amount

        emit(join_record(["month", "total"], delimiter=";"))
        for month in sorted(totals_by_month.keys()):
            total = totals_by_month[month]
            formatted_total = settings.format_amount(total)
            emit(join_record([month, formatted_total], delimiter=";"))

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month combinations where systems disagree beyond tolerance."""
    settings = load_settings()
    tolerance = (
        Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    )

    records_path = Path(args.records)

    if not records_path.exists():
        _log.warning("records file %s not found", records_path)
        return 1

    records: list[Record] = []
    with records_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
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
            except (ValueError, KeyError) as exc:
                _log.warning("skipping malformed row: %s", exc)

    group: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        if key not in group:
            group[key] = {}
        if record.source_system not in group[key]:
            group[key][record.source_system] = Decimal(0)
        group[key][record.source_system] += record.amount

    mismatches = 0
    for (account_code, month) in sorted(group.keys()):
        systems = group[(account_code, month)]
        if len(systems) < 2:
            continue

        amounts = list(systems.values())
        spread = max(amounts) - min(amounts)

        if spread > tolerance:
            mismatches += 1
            parts = [f"MISMATCH {account_code} {month}"]
            parts.append(f"spread={spread:.2f}")
            for sys in sorted("ABC"):
                if sys in systems:
                    parts.append(f"{sys}={systems[sys]:.2f}")
                else:
                    parts.append(f"{sys}=-")
            emit(" ".join(parts))

    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)

    total_checked = 0
    total_rejected = 0

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        try:
            raw_rows = read_rows(path)
        except LedgerParseError as exc:
            _log.warning("cannot parse %s: %s", path, exc)
            return 2

        if system == "A":
            data_line_start = next(i for i, line in enumerate(lines) if line and not line.startswith("#"))
            header_idx = data_line_start
            data_start = data_line_start + 1
        elif system == "B":
            data_start = 1
        else:
            data_start = 2

        for idx, row in enumerate(raw_rows):
            total_checked += 1
            line_num = data_start + idx

            try:
                if system == "A":
                    account_code_field = "account"
                    date_field = "posted_on"
                    amount_field = "amount"
                    _ = datetime.strptime(row[date_field], "%Y-%m-%d")
                    _ = Decimal(row[amount_field])
                elif system == "B":
                    account_code_field = "acct"
                    date_field = "value_date"
                    amount_field = "amount"
                    _ = datetime.strptime(row[date_field], "%Y-%m-%d")
                    _ = system_b.to_major_units(row[amount_field])
                else:
                    account_code_field = "ledger_acct"
                    date_field = "txn_date"
                    amount_field = "gross_amount"
                    _ = datetime.strptime(row[date_field], "%d/%m/%Y")
                    _ = Decimal(row[amount_field])

                account_code = row.get(account_code_field, "")
                if not pattern.match(account_code.strip()):
                    _log.warning(
                        "%s line %d: account code %r does not match pattern %s",
                        path.name, line_num, account_code, settings.account_code_pattern,
                    )
                    total_rejected += 1
            except (ValueError, KeyError, LedgerParseError) as exc:
                _log.warning("%s line %d: %s", path.name, line_num, exc)
                total_rejected += 1

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config

    handler = args.handler
    return int(handler(args))
