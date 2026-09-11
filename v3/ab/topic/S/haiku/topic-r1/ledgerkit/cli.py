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
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS
from ledgerkit.core.readers import rows_to_records
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
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="settings file to use for this run",
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
        "--out",
        metavar="PATH",
        default="out/records.csv",
        help="where to write the normalized file (default: out/records.csv)",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or month")
    report_parser.add_argument(
        "--by",
        choices=["account", "month"],
        required=True,
        help="group by account or month",
    )
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default="out/records.csv",
        help="normalized file to read (default: out/records.csv)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include negative amounts in totals (default: already included)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="find account/month pairs where systems disagree"
    )
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default="out/records.csv",
        help="normalized file to read (default: out/records.csv)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=Decimal,
        help="tolerance in dollars (default: from settings)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files for errors")
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
    """Merge export files into one normalized CSV."""
    settings = load_settings()
    all_records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            records = rows_to_records(path, settings.unknown_account_label)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 1

    # Normalize and sort
    normalized = normalize(all_records, keep_refunds=True)

    # Write output
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
    path = Path(args.records)

    try:
        records = _read_records_csv(path)
    except OSError as exc:
        _log.warning("cannot read %s: %s", path, exc)
        return 1

    # All records are included in report now (refunds are counted by default)
    if args.by == "account":
        emit(_report_by_account(records, settings))
    else:
        emit(_report_by_month(records, settings))

    return 0


def _report_by_account(records: list[Record], settings) -> str:
    """Generate report grouped by account."""
    totals: dict[str, tuple[str, Decimal]] = {}

    for record in records:
        code = record.account_code
        if code not in totals:
            totals[code] = (record.account_name, Decimal(0))
        name, total = totals[code]
        totals[code] = (name, total + record.amount)

    lines = ["account_code;account_name;total"]
    for code in sorted(totals.keys()):
        name, total = totals[code]
        formatted = settings.format_amount(total)
        lines.append(f"{code};{name};{formatted}")

    return "\n".join(lines)


def _report_by_month(records: list[Record], settings) -> str:
    """Generate report grouped by month."""
    totals: dict[str, Decimal] = {}

    for record in records:
        month = record.month()
        if month not in totals:
            totals[month] = Decimal(0)
        totals[month] += record.amount

    lines = ["month;total"]
    for month in sorted(totals.keys()):
        formatted = settings.format_amount(totals[month])
        lines.append(f"{month};{formatted}")

    return "\n".join(lines)


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find mismatches where systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    path = Path(args.records)
    try:
        records = _read_records_csv(path)
    except OSError as exc:
        _log.warning("cannot read %s: %s", path, exc)
        return 1

    # Group by account, month, system
    groups: dict[tuple[str, str, str], Decimal] = {}
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        if key not in groups:
            groups[key] = Decimal(0)
        groups[key] += record.amount

    # Find mismatches
    mismatches: list[tuple[str, str, dict[str, Decimal], Decimal]] = []

    # Get unique account/month combinations
    combinations = set((acc, month) for acc, month, _ in groups.keys())

    for account, month in sorted(combinations):
        systems = {}
        for sys in ["A", "B", "C"]:
            key = (account, month, sys)
            if key in groups:
                systems[sys] = groups[key]

        # Only check combinations with at least 2 systems
        if len(systems) >= 2:
            amounts = sorted(systems.values())
            spread = amounts[-1] - amounts[0]
            if spread > tolerance:
                mismatches.append((account, month, systems, spread))

    for account, month, systems, spread in mismatches:
        values = []
        for sys in ["A", "B", "C"]:
            if sys in systems:
                amount = systems[sys]
                values.append(f"{sys}={amount:.2f}")
            else:
                values.append(f"{sys}=-")
        emit(f"MISMATCH {account} {month} spread={spread:.2f} {' '.join(values)}")

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files."""
    settings = load_settings()
    total_rows = 0
    rejected_rows = 0
    pattern = re.compile(settings.account_code_pattern)

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except LedgerParseError as exc:
            _log.warning("%s: %s", path, exc)
            return 2

        if system == "A":
            rows = system_a.read_rows(path)
        elif system == "B":
            rows = system_b.read_rows(path)
        else:
            rows = system_c.read_rows(path)

        for row in rows:
            total_rows += 1
            # Validate account code
            code = row.get("account" if system == "A" else "acct" if system == "B" else "ledger_acct", "")
            if not pattern.match(code):
                _log.warning(
                    "%s line %d: account code %r does not match pattern",
                    path.name,
                    total_rows,
                    code,
                )
                rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def _read_records_csv(path: Path) -> list[Record]:
    """Read records from a CSV file."""
    records: list[Record] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Reconstruct a Record from the CSV row
            record = Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=__import__("datetime").date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            records.append(record)
    return records


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config

    handler = args.handler
    return int(handler(args))
