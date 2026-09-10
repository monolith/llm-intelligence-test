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
import os
import re
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit import parsers as parsers_module
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}


def _build_record(row: dict[str, str], system: str, settings) -> Record:
    """Build a Record from a raw parsed row."""
    if system == "A":
        record_id = row["entry_id"]
        date = datetime.fromisoformat(row["posted_on"]).date()
        account_code = row["account"]
        description = row["memo"]
        amount = Decimal(row["amount"])
    elif system == "B":
        record_id = row["doc_no"]
        date = datetime.fromisoformat(row["value_date"]).date()
        account_code = row["acct"]
        description = row["descr"]
        amount = system_b.to_major_units(row["amount"])
    else:
        record_id = row["ref"]
        date = datetime.strptime(row["txn_date"], "%d/%m/%Y").date()
        account_code = row["ledger_acct"]
        description = row["narrative"]
        amount = Decimal(row["gross_amount"])

    return Record(
        record_id=record_id,
        source_system=system,
        date=date,
        account_code=account_code,
        account_name=account_name(account_code, settings.unknown_account_label),
        description=description,
        amount=amount,
    )


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
        help="path to settings file (overrides LEDGERKIT_CONFIG env var)",
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
    ingest_parser.add_argument("--out", type=str, metavar="PATH", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or month")
    report_parser.add_argument(
        "--by",
        type=str,
        choices=["account", "month"],
        required=True,
        metavar="account|month",
        help="group by account or month",
    )
    report_parser.add_argument(
        "--records", type=str, metavar="PATH", help="normalized records file"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include refunds in totals (now default)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="find account/month combos where systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", type=str, metavar="PATH", help="normalized records file"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=str,
        metavar="N",
        help="tolerance in dollars",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check exports for malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports into one normalized file."""
    settings = load_settings()
    out_path = Path(args.out or "out/records.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records: list[Record] = []
    for file_path in args.files:
        path = Path(file_path)
        system = detect_system(path)
        rows = system_a.read_rows(path) if system == "A" else (
            system_b.read_rows(path) if system == "B" else system_c.read_rows(path)
        )
        for row in rows:
            record = _build_record(row, system, settings)
            records.append(record)

    normalized = normalize(records, keep_refunds=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        f.write(join_record(list(RECORD_COLUMNS)) + "\n")
        for record in normalized:
            f.write(join_record(record.to_row()) + "\n")

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    settings = load_settings()
    records_path = Path(args.records or "out/records.csv")

    records = _read_records(records_path)
    by_what = args.by

    if by_what == "account":
        by_account = {}
        for record in records:
            key = (record.account_code, record.account_name)
            by_account[key] = by_account.get(key, Decimal(0)) + record.amount

        emit("account_code;account_name;total")
        for (code, name), total in sorted(by_account.items()):
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{code};{name};{formatted}")
    else:
        by_month = {}
        for record in records:
            month = record.month()
            by_month[month] = by_month.get(month, Decimal(0)) + record.amount

        emit("month;total")
        for month, total in sorted(by_month.items()):
            formatted = settings.format_amount(total.quantize(Decimal(10) ** -settings.decimals))
            emit(f"{month};{formatted}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account/month combos where systems disagree."""
    settings = load_settings()
    records_path = Path(args.records or "out/records.csv")
    tolerance = Decimal(args.tolerance) if args.tolerance else settings.tolerance

    records = _read_records(records_path)

    by_group = {}
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        by_group[key] = by_group.get(key, Decimal(0)) + record.amount

    by_account_month = {}
    for (code, month, system), total in by_group.items():
        key = (code, month)
        if key not in by_account_month:
            by_account_month[key] = {}
        by_account_month[key][system] = total

    mismatches = 0
    for (code, month) in sorted(by_account_month.keys()):
        systems_data = by_account_month[(code, month)]
        if len(systems_data) < 2:
            continue

        totals = list(systems_data.values())
        spread = max(totals) - min(totals)

        if spread > tolerance:
            mismatches += 1
            systems_line = " ".join(
                f"{system}={systems_data[system]:.2f}" if system in systems_data else f"{system}=-"
                for system in ["A", "B", "C"]
            )
            emit(f"MISMATCH {code} {month} spread={spread:.2f} {systems_line}")

    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check exports for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    total_checked = 0
    total_rejected = 0
    status = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            status = 2
            continue

        try:
            rows = system_a.read_rows(path) if system == "A" else (
                system_b.read_rows(path) if system == "B" else system_c.read_rows(path)
            )
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            status = 2
            continue

        for row in rows:
            total_checked += 1
            reason = None

            if system == "A":
                date_str = row.get("posted_on", "")
                amount_str = row.get("amount", "")
                code_str = row.get("account", "")
            elif system == "B":
                date_str = row.get("value_date", "")
                amount_str = row.get("amount", "")
                code_str = row.get("acct", "")
            else:
                date_str = row.get("txn_date", "")
                amount_str = row.get("gross_amount", "")
                code_str = row.get("ledger_acct", "")

            if not pattern.match(code_str.strip()):
                reason = f"account code {code_str!r} does not match pattern"
            elif system == "A":
                try:
                    datetime.fromisoformat(date_str)
                except (ValueError, TypeError):
                    reason = f"cannot parse A date {date_str!r} as YYYY-MM-DD"
            elif system == "B":
                try:
                    datetime.fromisoformat(date_str)
                except (ValueError, TypeError):
                    reason = f"cannot parse B date {date_str!r} as YYYY-MM-DD"
            elif system == "C":
                try:
                    datetime.strptime(date_str, "%d/%m/%Y")
                except (ValueError, TypeError):
                    reason = f"cannot parse C date {date_str!r} as DD/MM/YYYY"

            if reason is None:
                try:
                    Decimal(amount_str)
                except Exception:
                    reason = f"cannot parse amount {amount_str!r}"

            if reason:
                total_rejected += 1
                _log.warning("%s: %s", path.name, reason)

    if total_rejected:
        status = 2
    emit(f"checked={total_checked} rejected={total_rejected}")
    return status


def _read_records(path: Path) -> list[Record]:
    """Read a normalized records CSV file."""
    from ledgerkit.core.fields import split_record

    records = []
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()
        if not lines:
            return records

        for i, line in enumerate(lines[1:], start=2):
            line = line.rstrip("\r\n")
            parts = split_record(line)
            if len(parts) != len(RECORD_COLUMNS):
                _log.warning("line %d: expected %d fields, got %d", i, len(RECORD_COLUMNS), len(parts))
                continue

            records.append(Record(
                record_id=parts[0],
                source_system=parts[1],
                date=datetime.fromisoformat(parts[2]).date(),
                account_code=parts[3],
                account_name=parts[4],
                description=parts[5],
                amount=Decimal(parts[6]),
            ))
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


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config
    handler = args.handler
    return int(handler(args))
