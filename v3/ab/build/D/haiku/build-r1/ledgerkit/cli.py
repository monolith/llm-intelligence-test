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
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings, CONFIG_ENV_VAR, config_path
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS, sort_key
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
    parser.add_argument("--config", type=str, default=None, help="path to override settings file")
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
    ingest_parser.add_argument("--out", type=str, default="out/records.csv", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping to total by")
    report_parser.add_argument("--records", type=str, default="out/records.csv", help="normalized file to read")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument("--records", type=str, default="out/records.csv", help="normalized file to read")
    reconcile_parser.add_argument("--tolerance", type=float, default=None, help="dollar tolerance for agreement")
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


def _read_records_from_exports(file_paths: list[str]) -> list[Record]:
    """Read and convert all records from export files."""
    settings = load_settings()
    all_records: list[Record] = []

    for file_path in file_paths:
        path = Path(file_path)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            continue

        converter = {"A": system_a.to_record, "B": system_b.to_record, "C": system_c.to_record}[system]
        for raw in raw_rows:
            try:
                record = converter(raw, settings.unknown_account_label)
                all_records.append(record)
            except LedgerParseError as exc:
                _log.warning("cannot convert row from %s: %s", path, exc)

    return all_records


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports into one normalized file."""
    records = _read_records_from_exports(args.files)
    normalized = normalize(records, keep_refunds=True)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {output_path}")
    return 0


def _read_normalized_csv(path: Path) -> list[Record]:
    """Read records from a normalized CSV file."""
    records: list[Record] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(RECORD_COLUMNS):
                _log.warning("CSV header mismatch in %s", path)
                return []
            for row in reader:
                records.append(
                    Record(
                        record_id=row["record_id"],
                        source_system=row["source_system"],
                        date=date.fromisoformat(row["date"]),
                        account_code=row["account_code"],
                        account_name=row["account_name"],
                        description=row["description"],
                        amount=Decimal(row["amount"]),
                    )
                )
    except (OSError, ValueError) as exc:
        _log.warning("cannot read %s: %s", path, exc)
    return records


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    settings = load_settings()
    records = _read_normalized_csv(Path(args.records))

    if args.include_refunds:
        filtered = records
    else:
        filtered = [r for r in records if not r.is_refund()]

    if args.by == "account":
        totals: dict[tuple[str, str], Decimal] = defaultdict(Decimal)
        for record in filtered:
            key = (record.account_code, record.account_name)
            totals[key] += record.amount

        emit("account_code,account_name,total")
        for (code, name) in sorted(totals.keys()):
            amount = totals[(code, name)]
            rounded = amount.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{code},{name},{settings.format_amount(rounded)}")
    else:
        totals_by_month: dict[str, Decimal] = defaultdict(Decimal)
        for record in filtered:
            month = record.month()
            totals_by_month[month] += record.amount

        emit("month,total")
        for month in sorted(totals_by_month.keys()):
            amount = totals_by_month[month]
            rounded = amount.quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(rounded)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where systems disagree."""
    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    records = _read_normalized_csv(Path(args.records))

    combinations: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        month = record.month()
        key = (record.account_code, month)
        combinations[key][record.source_system] += record.amount

    mismatches = 0
    for (account_code, month) in sorted(combinations.keys()):
        system_totals = combinations[(account_code, month)]
        if len(system_totals) < 2:
            continue

        amounts = list(system_totals.values())
        spread = max(amounts) - min(amounts)

        if spread > tolerance:
            mismatches += 1
            parts = []
            for system in ["A", "B", "C"]:
                if system in system_totals:
                    amount = system_totals[system]
                    parts.append(f"{system}={amount.quantize(Decimal('0.01'))}")
                else:
                    parts.append(f"{system}=-")
            emit(f"MISMATCH {account_code} {month} spread={spread.quantize(Decimal('0.01'))} {' '.join(parts)}")

    emit(f"mismatches={mismatches}")
    return 0


def _validate_system_a(raw: dict[str, str], account_pattern: re.Pattern[str]) -> str | None:
    """Validate one System A row, return error message or None if valid."""
    if not raw.get("posted_on"):
        return "missing date field"
    try:
        date.fromisoformat(raw["posted_on"])
    except ValueError:
        return f"invalid date format: {raw['posted_on']}"
    if not raw.get("amount"):
        return "missing amount field"
    try:
        Decimal(raw["amount"])
    except ValueError:
        return f"invalid amount: {raw['amount']}"
    if not account_pattern.match(raw.get("account", "")):
        return f"account code does not match pattern: {raw.get('account')}"
    return None


def _validate_system_b(raw: dict[str, str], account_pattern: re.Pattern[str]) -> str | None:
    """Validate one System B row, return error message or None if valid."""
    if not raw.get("value_date"):
        return "missing date field"
    try:
        date.fromisoformat(raw["value_date"])
    except ValueError:
        return f"invalid date format: {raw['value_date']}"
    if not raw.get("amount"):
        return "missing amount field"
    try:
        system_b.to_major_units(raw["amount"])
    except (ValueError, LedgerParseError) as exc:
        return f"invalid amount: {exc}"
    if not account_pattern.match(raw.get("acct", "")):
        return f"account code does not match pattern: {raw.get('acct')}"
    return None


def _validate_system_c(raw: dict[str, str], account_pattern: re.Pattern[str]) -> str | None:
    """Validate one System C row, return error message or None if valid."""
    if not raw.get("txn_date"):
        return "missing date field"
    try:
        datetime.strptime(raw["txn_date"], "%d/%m/%Y")
    except ValueError:
        return f"invalid date format: {raw['txn_date']}"
    if not raw.get("gross_amount"):
        return "missing amount field"
    try:
        Decimal(raw["gross_amount"])
    except ValueError:
        return f"invalid amount: {raw['gross_amount']}"
    if not account_pattern.match(raw.get("ledger_acct", "")):
        return f"account code does not match pattern: {raw.get('ledger_acct')}"
    return None


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)
    total_checked = 0
    total_rejected = 0

    validators = {"A": _validate_system_a, "B": _validate_system_b, "C": _validate_system_c}

    for file_path in args.files:
        path = Path(file_path)
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
            total_rejected += 1
            continue

        validator = validators[system]
        for line_num, raw in enumerate(raw_rows, start=2):
            total_checked += 1
            error = validator(raw, account_pattern)
            if error:
                _log.warning("%s line %d: %s", path.name, line_num, error)
                total_rejected += 1

    if total_rejected > 0:
        emit(f"checked={total_checked} rejected={total_rejected}")
        return 2

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
