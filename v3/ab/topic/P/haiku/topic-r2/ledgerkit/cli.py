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
from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
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

    # Global --config option
    parser.add_argument("--config", metavar="PATH", help="read settings from this file")

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
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="grouping")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds (default: already included)")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file")
    reconcile_parser.add_argument("--tolerance", type=Decimal, metavar="N", help="tolerance in dollars")
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
    """Merge multiple exports into one normalized file."""
    records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            raw_rows = read_rows(path)
            system = detect_system(path)
            records.extend(_rows_to_records(system, raw_rows, path))
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)

    # Normalize and write
    settings = load_settings()
    normalized = normalize(records, keep_refunds=True)

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    settings = load_settings()

    # Read the normalized file
    path = Path(args.records)
    try:
        records = _read_normalized_csv(path)
    except (OSError, LedgerParseError) as exc:
        _log.warning("cannot read %s: %s", path, exc)
        return 1

    if args.by == "account":
        _report_by_account(records, settings)
    else:
        _report_by_month(records, settings)

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report where systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    # Read the normalized file
    path = Path(args.records)
    try:
        records = _read_normalized_csv(path)
    except (OSError, LedgerParseError) as exc:
        _log.warning("cannot read %s: %s", path, exc)
        return 1

    mismatches = _find_mismatches(records, tolerance)

    for account_code, month, spread, totals in mismatches:
        amounts_str = " ".join(
            f"{system}={totals.get(system, Decimal('0.00')):.2f}"
            if system in totals
            else f"{system}=-"
            for system in ["A", "B", "C"]
        )
        emit(f"MISMATCH {account_code} {month} spread={spread:.2f} {amounts_str}")

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    total_rows = 0
    rejected_rows = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            raw_rows = read_rows(path)
            system = detect_system(path)
            total_rows += len(raw_rows)

            for row in raw_rows:
                try:
                    _row_to_record(system, row, settings)
                except Exception as exc:
                    rejected_rows += 1
                    _log.warning("%s: %s", path, exc)

        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def _rows_to_records(system: str, rows: list[dict[str, str]], path: Path) -> list[Record]:
    """Convert raw rows from a system into Records."""
    records: list[Record] = []
    for i, row in enumerate(rows, start=1):
        try:
            record = _row_to_record(system, row, load_settings())
            records.append(record)
        except LedgerParseError as exc:
            _log.warning("%s line %d: %s", path.name, i, exc)
    return records


def _row_to_record(system: str, row: dict[str, str], settings) -> Record:
    """Convert one raw row into a Record."""
    if system == "A":
        return _parse_system_a_row(row, settings)
    elif system == "B":
        return _parse_system_b_row(row, settings)
    else:
        return _parse_system_c_row(row, settings)


def _parse_system_a_row(row: dict[str, str], settings) -> Record:
    """Parse a System A row."""
    try:
        date_obj = datetime.fromisoformat(row["posted_on"]).date()
        amount = Decimal(row["amount"])
        code = row["account"]
    except (KeyError, ValueError) as exc:
        raise LedgerParseError(f"invalid System A row: {exc}") from exc

    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=date_obj,
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["memo"],
        amount=amount,
    )


def _parse_system_b_row(row: dict[str, str], settings) -> Record:
    """Parse a System B row."""
    try:
        date_obj = datetime.fromisoformat(row["value_date"]).date()
        amount = system_b.to_major_units(row["amount"])
        code = row["acct"]
    except (KeyError, ValueError) as exc:
        raise LedgerParseError(f"invalid System B row: {exc}") from exc

    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=date_obj,
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["descr"],
        amount=amount,
    )


def _parse_system_c_row(row: dict[str, str], settings) -> Record:
    """Parse a System C row."""
    try:
        date_obj = datetime.strptime(row["txn_date"], "%d/%m/%Y").date()
        amount = Decimal(row["gross_amount"])
        code = row["ledger_acct"]
    except (KeyError, ValueError) as exc:
        raise LedgerParseError(f"invalid System C row: {exc}") from exc

    return Record(
        record_id=row["ref"],
        source_system="C",
        date=date_obj,
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["narrative"],
        amount=amount,
    )


def _read_normalized_csv(path: Path) -> list[Record]:
    """Read a normalized CSV file."""
    records: list[Record] = []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_obj = datetime.fromisoformat(row["date"]).date()
            amount = Decimal(row["amount"])
            records.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date_obj,
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=amount,
                )
            )

    return records


def _report_by_account(records: Iterable[Record], settings) -> None:
    """Print totals grouped by account code."""
    totals: dict[str, tuple[str, Decimal]] = {}

    for record in records:
        if record.account_code not in totals:
            totals[record.account_code] = (record.account_name, Decimal(0))
        name, total = totals[record.account_code]
        totals[record.account_code] = (name, total + record.amount)

    emit("account_code;account_name;total")
    for code in sorted(totals.keys()):
        name, total = totals[code]
        formatted_total = settings.format_amount(total)
        emit(f"{code};{name};{formatted_total}")


def _report_by_month(records: Iterable[Record], settings) -> None:
    """Print totals grouped by month."""
    totals: dict[str, Decimal] = {}

    for record in records:
        month = record.month()
        if month not in totals:
            totals[month] = Decimal(0)
        totals[month] += record.amount

    emit("month;total")
    for month in sorted(totals.keys()):
        formatted_total = settings.format_amount(totals[month])
        emit(f"{month};{formatted_total}")


def _find_mismatches(
    records: Iterable[Record], tolerance: Decimal
) -> list[tuple[str, str, Decimal, dict[str, Decimal]]]:
    """Find account/month combinations where systems disagree."""
    # Group by account, month, and system
    by_key: dict[tuple[str, str, str], Decimal] = {}

    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        if key not in by_key:
            by_key[key] = Decimal(0)
        by_key[key] += record.amount

    # Find mismatches
    mismatches: list[tuple[str, str, Decimal, dict[str, Decimal]]] = []
    seen: set[tuple[str, str]] = set()

    for (account, month, system), total in by_key.items():
        key = (account, month)
        if key in seen:
            continue

        # Get totals for all systems for this account/month
        systems_totals: dict[str, Decimal] = {}
        for s in ["A", "B", "C"]:
            sys_key = (account, month, s)
            if sys_key in by_key:
                systems_totals[s] = by_key[sys_key]

        # Only check if at least 2 systems posted to it
        if len(systems_totals) >= 2:
            values = list(systems_totals.values())
            spread = max(values) - min(values)

            if spread > tolerance:
                seen.add(key)
                mismatches.append((account, month, spread, systems_totals))

    # Sort by account, then month
    mismatches.sort(key=lambda x: (x[0], x[1]))

    return mismatches


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    # Handle --config before parsing
    if argv is not None:
        argv_list = list(argv)
    else:
        argv_list = None

    if argv_list and "--config" in argv_list:
        idx = argv_list.index("--config")
        if idx + 1 < len(argv_list):
            config_path = argv_list[idx + 1]
            os.environ["LEDGERKIT_CONFIG"] = config_path

    parser = build_parser()
    args = parser.parse_args(argv_list)
    handler = args.handler
    return int(handler(args))
