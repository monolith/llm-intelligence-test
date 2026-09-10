"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings, CONFIG_ENV_VAR
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS
from ledgerkit.core import fields as csv_fields
from ledgerkit.core.normalize import normalize
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
    parser.add_argument("--config", metavar="PATH", help="read settings from this file instead of the default")
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
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="where to write (default: out/records.csv)")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], metavar="account|month", help="group by account or month")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file to read (default: out/records.csv)")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals (default: already included)")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find account/month mismatches")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file to read (default: out/records.csv)")
    reconcile_parser.add_argument("--tolerance", metavar="N", type=float, help="tolerance in dollars (default: from settings)")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files for malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _rows_to_records(rows: list[dict[str, str]], system: str, settings) -> list[Record]:
    """Convert raw parsed rows to Record objects for the given system."""
    records: list[Record] = []
    for raw_row in rows:
        try:
            if system == "A":
                record = Record(
                    record_id=raw_row["entry_id"],
                    source_system="A",
                    date=datetime.strptime(raw_row["posted_on"], "%Y-%m-%d").date(),
                    account_code=raw_row["account"],
                    account_name=account_name(raw_row["account"], settings.unknown_account_label),
                    description=raw_row["memo"],
                    amount=Decimal(raw_row["amount"]),
                )
            elif system == "B":
                record = Record(
                    record_id=raw_row["doc_no"],
                    source_system="B",
                    date=datetime.strptime(raw_row["value_date"], "%Y-%m-%d").date(),
                    account_code=raw_row["acct"],
                    account_name=account_name(raw_row["acct"], settings.unknown_account_label),
                    description=raw_row["descr"],
                    amount=system_b.to_major_units(raw_row["amount"]),
                )
            elif system == "C":
                date_str = raw_row["txn_date"]
                date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
                record = Record(
                    record_id=raw_row["ref"],
                    source_system="C",
                    date=date_obj,
                    account_code=raw_row["ledger_acct"],
                    account_name=account_name(raw_row["ledger_acct"], settings.unknown_account_label),
                    description=raw_row["narrative"],
                    amount=Decimal(raw_row["gross_amount"]),
                )
            else:
                continue
            records.append(record)
        except (ValueError, KeyError) as exc:
            _log.warning("could not convert row from system %s: %s", system, exc)
            continue
    return records


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
    """Merge exports into one normalized CSV file."""
    settings = load_settings()
    all_records: list[Record] = []

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            rows = read_rows(path)
            records = _rows_to_records(rows, system, settings)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot read %s: %s", path, exc)
            return 1

    normalized = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(",".join(RECORD_COLUMNS) + "\n")
        for record in normalized:
            row = record.to_row()
            handle.write(csv_fields.join_record(row) + "\n")

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Report totals by account or month."""
    settings = load_settings()
    records_path = Path(args.records)

    try:
        records: list[Record] = []
        with records_path.open("r", encoding="utf-8") as handle:
            header = handle.readline().strip()
            if header != ",".join(RECORD_COLUMNS):
                _log.error("invalid header in %s", records_path)
                return 1

            for line in handle:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                values = csv_fields.split_record(line)
                if len(values) != len(RECORD_COLUMNS):
                    _log.error("wrong number of fields in %s", records_path)
                    return 1

                record = Record(
                    record_id=values[0],
                    source_system=values[1],
                    date=datetime.strptime(values[2], "%Y-%m-%d").date(),
                    account_code=values[3],
                    account_name=values[4],
                    description=values[5],
                    amount=Decimal(values[6]),
                )
                records.append(record)
    except OSError as exc:
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

        emit(f"account_code;account_name;total")
        for code in sorted(totals.keys()):
            name, total = totals[code]
            formatted_total = settings.format_amount(total)
            emit(f"{code};{name};{formatted_total}")

    elif args.by == "month":
        totals_by_month: dict[str, Decimal] = {}
        for record in records:
            month = record.month()
            totals_by_month[month] = totals_by_month.get(month, Decimal(0)) + record.amount

        emit(f"month;total")
        for month in sorted(totals_by_month.keys()):
            total = totals_by_month[month]
            formatted_total = settings.format_amount(total)
            emit(f"{month};{formatted_total}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account/month combinations where systems disagree."""
    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    records_path = Path(args.records)

    try:
        records: list[Record] = []
        with records_path.open("r", encoding="utf-8") as handle:
            header = handle.readline().strip()
            if header != ",".join(RECORD_COLUMNS):
                _log.error("invalid header in %s", records_path)
                return 1

            for line in handle:
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                values = csv_fields.split_record(line)
                if len(values) != len(RECORD_COLUMNS):
                    _log.error("wrong number of fields in %s", records_path)
                    return 1

                record = Record(
                    record_id=values[0],
                    source_system=values[1],
                    date=datetime.strptime(values[2], "%Y-%m-%d").date(),
                    account_code=values[3],
                    account_name=values[4],
                    description=values[5],
                    amount=Decimal(values[6]),
                )
                records.append(record)
    except OSError as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    grouped: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        grouped[key] += record.amount

    combinations: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for (account, month, system), total in grouped.items():
        combinations[(account, month)][system] = total

    mismatches = []
    for (account, month), systems_totals in sorted(combinations.items()):
        if len(systems_totals) < 2:
            continue

        totals_list = sorted(systems_totals.values())
        spread = totals_list[-1] - totals_list[0]

        if spread > tolerance:
            systems_str_parts = []
            for system in ["A", "B", "C"]:
                if system in systems_totals:
                    formatted = f"{systems_totals[system]:.2f}"
                    systems_str_parts.append(f"{system}={formatted}")
                else:
                    systems_str_parts.append(f"{system}=-")

            mismatch_line = f"MISMATCH {account} {month} spread={spread:.2f} " + " ".join(systems_str_parts)
            mismatches.append(mismatch_line)

    for line in mismatches:
        emit(line)

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot read %s: %s", path, exc)
            return 2

        try:
            rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("%s: %s", path, exc)
            return 2

        for raw_row in rows:
            total_checked += 1
            try:
                if system == "A":
                    if "entry_id" not in raw_row or "posted_on" not in raw_row or "account" not in raw_row or "amount" not in raw_row:
                        raise ValueError("missing required field")
                    datetime.strptime(raw_row["posted_on"], "%Y-%m-%d")
                    Decimal(raw_row["amount"])
                    account_code = raw_row["account"].strip().upper()
                elif system == "B":
                    if "doc_no" not in raw_row or "value_date" not in raw_row or "acct" not in raw_row or "amount" not in raw_row:
                        raise ValueError("missing required field")
                    datetime.strptime(raw_row["value_date"], "%Y-%m-%d")
                    system_b.to_major_units(raw_row["amount"])
                    account_code = raw_row["acct"].strip().upper()
                elif system == "C":
                    if "ref" not in raw_row or "txn_date" not in raw_row or "ledger_acct" not in raw_row or "gross_amount" not in raw_row:
                        raise ValueError("missing required field")
                    datetime.strptime(raw_row["txn_date"], "%d/%m/%Y")
                    Decimal(raw_row["gross_amount"])
                    account_code = raw_row["ledger_acct"].strip().upper()
                else:
                    continue

                if not re.match(settings.account_code_pattern, account_code):
                    raise ValueError(f"account code {account_code} does not match pattern {settings.account_code_pattern}")
            except (ValueError, LedgerParseError) as exc:
                total_rejected += 1
                _log.warning("%s: invalid row: %s", path, exc)

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
