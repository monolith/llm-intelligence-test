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
from collections.abc import Sequence
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.normalize import normalize
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
        help="read settings from this file instead of config/settings.toml",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to ingest")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="output file (default: out/records.csv)"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by",
        choices=["account", "month"],
        required=True,
        help="group by account code or month",
    )
    report_parser.add_argument(
        "--records",
        default="out/records.csv",
        metavar="PATH",
        help="normalized file to read (default: out/records.csv)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include refunds in totals (deprecated; refunds now included by default)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="find where systems disagree"
    )
    reconcile_parser.add_argument(
        "--records",
        default="out/records.csv",
        metavar="PATH",
        help="normalized file to read (default: out/records.csv)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=float,
        help="tolerance in dollars (default from settings)",
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


def _rows_to_records(system: str, raw_rows: list[dict[str, str]]) -> list[Record]:
    """Convert raw rows from a system into Record objects."""
    records: list[Record] = []
    for row in raw_rows:
        if system == "A":
            records.append(_record_from_a(row))
        elif system == "B":
            records.append(_record_from_b(row))
        elif system == "C":
            records.append(_record_from_c(row))
    return records


def _record_from_a(row: dict[str, str]) -> Record:
    """Build a Record from an Ardent row."""
    posted_on = date.fromisoformat(row["posted_on"])
    amount = Decimal(row["amount"]).quantize(Decimal("0.01"))
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=posted_on,
        account_code=row["account"],
        account_name=account_name(row["account"], load_settings().unknown_account_label),
        description=row["memo"],
        amount=amount,
    )


def _record_from_b(row: dict[str, str]) -> Record:
    """Build a Record from a Borough row."""
    value_date = date.fromisoformat(row["value_date"])
    amount = system_b.to_major_units(row["amount"])
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=value_date,
        account_code=row["acct"],
        account_name=account_name(row["acct"], load_settings().unknown_account_label),
        description=row["descr"],
        amount=amount,
    )


def _record_from_c(row: dict[str, str]) -> Record:
    """Build a Record from a Calder row."""
    txn_date = _parse_calder_date(row["txn_date"])
    amount = Decimal(row["gross_amount"]).quantize(Decimal("0.01"))
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=txn_date,
        account_code=row["ledger_acct"],
        account_name=account_name(row["ledger_acct"], load_settings().unknown_account_label),
        description=row["narrative"],
        amount=amount,
    )


def _parse_calder_date(date_str: str) -> date:
    """Parse Calder's DD/MM/YYYY date format."""
    from datetime import datetime
    return datetime.strptime(date_str, "%d/%m/%Y").date()


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports into one normalized file."""
    settings = load_settings()
    all_records: list[Record] = []

    for filepath in args.files:
        path = Path(filepath)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
            records = _rows_to_records(system, raw_rows)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
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
    """Print totals by account or by month."""
    settings = load_settings()
    records_path = Path(args.records)

    try:
        records = _read_normalized_csv(records_path)
    except OSError as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        _report_by_account(records, settings)
    elif args.by == "month":
        _report_by_month(records, settings)

    return 0


def _read_normalized_csv(path: Path) -> list[Record]:
    """Read a normalized CSV file back into Record objects."""
    records: list[Record] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != list(RECORD_COLUMNS):
            raise ValueError("CSV header does not match expected format")
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
    return records


def _report_by_account(records: list[Record], settings: object) -> None:
    """Print report totals grouped by account."""
    totals: dict[str, tuple[str, Decimal]] = {}
    for record in records:
        key = record.account_code
        if key not in totals:
            totals[key] = (record.account_name, Decimal(0))
        name, total = totals[key]
        totals[key] = (name, total + record.amount)

    emit("account_code;account_name;total")
    for code in sorted(totals.keys()):
        name, total = totals[code]
        formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
        emit(f"{code};{name};{formatted}")


def _report_by_month(records: list[Record], settings: object) -> None:
    """Print report totals grouped by month."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount

    emit("month;total")
    for month in sorted(totals.keys()):
        total = totals[month]
        formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
        emit(f"{month};{formatted}")


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account+month combinations where systems disagree."""
    settings = load_settings()
    tolerance = settings.tolerance
    if args.tolerance is not None:
        tolerance = Decimal(str(args.tolerance))

    records_path = Path(args.records)
    try:
        records = _read_normalized_csv(records_path)
    except OSError as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    mismatches = _find_mismatches(records, tolerance, settings)
    for mismatch in mismatches:
        emit(mismatch)

    emit(f"mismatches={len(mismatches)}")
    return 0


def _find_mismatches(
    records: list[Record], tolerance: Decimal, settings: object
) -> list[str]:
    """Find account+month combinations where systems disagree."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}

    for record in records:
        key = (record.account_code, record.month())
        if key not in groups:
            groups[key] = {}
        system = record.source_system
        groups[key][system] = groups[key].get(system, Decimal(0)) + record.amount

    mismatches: list[str] = []
    for (account_code, month), systems in sorted(groups.items()):
        if len(systems) < 2:
            continue

        values = sorted(systems.values())
        spread = values[-1] - values[0]

        if spread > tolerance:
            parts = [f"MISMATCH {account_code} {month}"]
            parts.append(f"spread={spread.quantize(Decimal('0.01'))}")

            for sys in ["A", "B", "C"]:
                if sys in systems:
                    parts.append(f"{sys}={systems[sys].quantize(Decimal('0.01'))}")
                else:
                    parts.append(f"{sys}=-")

            mismatches.append(" ".join(parts))

    return mismatches


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
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        for row in raw_rows:
            total_checked += 1
            account_code = _get_account_code(system, row)

            if not pattern.match(account_code):
                _log.warning(
                    "%s: account code %r does not match pattern",
                    path.name,
                    account_code,
                )
                total_rejected += 1

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected > 0 else 0


def _get_account_code(system: str, row: dict[str, str]) -> str:
    """Extract account code from a raw row."""
    if system == "A":
        return row.get("account", "")
    elif system == "B":
        return row.get("acct", "")
    elif system == "C":
        return row.get("ledger_acct", "")
    return ""


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    argv_list = list(argv) if argv is not None else None
    if argv_list and "--config" in argv_list:
        config_idx = argv_list.index("--config")
        if config_idx + 1 < len(argv_list):
            os.environ["LEDGERKIT_CONFIG"] = argv_list[config_idx + 1]
    parser = build_parser()
    args = parser.parse_args(argv_list)
    handler = args.handler
    return int(handler(args))
