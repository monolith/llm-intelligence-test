"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.convert import system_a_to_record, system_b_to_record, system_c_to_record
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger
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
        "--config", type=str, metavar="PATH", help="read settings from this TOML file instead of the default"
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
    ingest_parser.add_argument(
        "--out", type=str, default="out/records.csv", metavar="PATH", help="where to write the output"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or month")
    report_parser.add_argument(
        "--by", choices=["account", "month"], required=True, help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records", type=str, default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="include refunds in the totals"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", type=str, default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=float, metavar="N", help="dollars; two systems agree within this tolerance"
    )
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
    all_records: list[Record] = []

    converters = {
        "A": system_a_to_record,
        "B": system_b_to_record,
        "C": system_c_to_record,
    }

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 1

        converter = converters[system]
        for raw_row in raw_rows:
            try:
                record = converter(raw_row, settings.unknown_account_label)
                all_records.append(record)
            except LedgerParseError as exc:
                _log.warning("cannot convert row from %s: %s", path, exc)
                return 1

    normalized = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", newline="", encoding="utf-8") as f:
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
        _log.warning("cannot read %s", records_path)
        return 1

    records: list[Record] = []
    try:
        with records_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if tuple(reader.fieldnames or []) != RECORD_COLUMNS:
                _log.warning("unexpected columns in %s", records_path)
                return 1
            for row in reader:
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
    except (OSError, ValueError, KeyError) as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for record in records:
            totals[(record.account_code, record.account_name)] += record.amount

        emit("account_code;account_name;total")
        for (code, name), total in sorted(totals.items()):
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{code};{name};{formatted}")

    else:  # args.by == "month"
        totals = defaultdict(Decimal)
        for record in records:
            month = record.month()
            totals[month] += record.amount

        emit("month;total")
        for month in sorted(totals.keys()):
            total = totals[month]
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{month};{formatted}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report mismatches between systems."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    tolerance = Decimal(str(tolerance))

    records_path = Path(args.records)
    if not records_path.is_file():
        _log.warning("cannot read %s", records_path)
        return 1

    records: list[Record] = []
    try:
        with records_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if tuple(reader.fieldnames or []) != RECORD_COLUMNS:
                _log.warning("unexpected columns in %s", records_path)
                return 1
            for row in reader:
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
    except (OSError, ValueError, KeyError) as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        totals[key] += record.amount

    combos: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: {})
    for (code, month, system), total in totals.items():
        combos[(code, month)][system] = total

    mismatches = 0
    for (code, month), systems in sorted(combos.items()):
        if len(systems) < 2:
            continue

        amounts = sorted(systems.values())
        spread = amounts[-1] - amounts[0]

        if spread > tolerance:
            mismatches += 1
            parts = []
            for sys in ("A", "B", "C"):
                if sys in systems:
                    parts.append(f"{sys}={systems[sys]:.2f}")
                else:
                    parts.append(f"{sys}=-")
            emit(f"MISMATCH {code} {month} spread={spread:.2f} {' '.join(parts)}")

    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files without writing anything."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)

    total_rows = 0
    rejected_rows = 0

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        converters = {
            "A": system_a_to_record,
            "B": system_b_to_record,
            "C": system_c_to_record,
        }
        converter = converters[system]

        for line_num, raw_row in enumerate(raw_rows, start=2):
            total_rows += 1
            try:
                record = converter(raw_row, settings.unknown_account_label)
                if not account_pattern.match(record.account_code):
                    rejected_rows += 1
                    _log.warning(
                        "%s line %d: account code %r does not match pattern %r",
                        path.name,
                        line_num,
                        record.account_code,
                        settings.account_code_pattern,
                    )
            except LedgerParseError as exc:
                rejected_rows += 1
                _log.warning("%s line %d: %s", path.name, line_num, exc)

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        import os

        os.environ["LEDGERKIT_CONFIG"] = args.config
    handler = args.handler
    return int(handler(args))
