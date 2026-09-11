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
import re
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.converters import row_to_record_a, row_to_record_b, row_to_record_c
from ledgerkit.core.records import LedgerParseError, Record, sort_key
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
        help="override settings file for this run",
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
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output file")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", metavar="account|month", required=True, choices=["account", "month"], help="grouping")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file")
    report_parser.add_argument("--include-refunds", action="store_true", help="include refunds in totals")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file")
    reconcile_parser.add_argument("--tolerance", metavar="N", type=Decimal, help="tolerance in dollars")
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
    """Merge exports into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
            if system == "A":
                rows = system_a.read_rows(path)
                records.extend(row_to_record_a(row, settings.unknown_account_label) for row in rows)
            elif system == "B":
                rows = system_b.read_rows(path)
                records.extend(row_to_record_b(row, settings.unknown_account_label) for row in rows)
            else:
                rows = system_c.read_rows(path)
                records.extend(row_to_record_c(row, settings.unknown_account_label) for row in rows)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            return 1

    records.sort(key=sort_key)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["record_id", "source_system", "date", "account_code", "account_name", "description", "amount"])
        for record in records:
            writer.writerow(record.to_row())

    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    from ledgerkit.mapping import ACCOUNT_NAMES
    settings = load_settings()
    records_path = Path(args.records)

    try:
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader) if reader else []
    except OSError as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        totals: dict[str, Decimal] = defaultdict(Decimal)
        for row in records:
            totals[row["account_code"]] += Decimal(row["amount"])

        emit("account_code;account_name;total")
        for code in sorted(totals.keys()):
            name = ACCOUNT_NAMES.get(code, settings.unknown_account_label)
            total = totals[code].quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{code};{name};{settings.format_amount(total)}")
    else:
        totals_by_month: dict[str, Decimal] = defaultdict(Decimal)
        for row in records:
            month = row["date"][:7]
            totals_by_month[month] += Decimal(row["amount"])

        emit("month;total")
        for month in sorted(totals_by_month.keys()):
            total = totals_by_month[month].quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{month};{settings.format_amount(total)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month pairs where systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records_path = Path(args.records)

    try:
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader) if reader else []
    except OSError as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    group_totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for row in records:
        key = (row["account_code"], row["date"][:7], row["source_system"])
        group_totals[key] += Decimal(row["amount"])

    mismatches: list[str] = []
    checked: set[tuple[str, str]] = set()

    for (account, month, system), total in sorted(group_totals.items()):
        combo = (account, month)
        if combo in checked:
            continue

        systems_in_combo = {s for (a, m, s), _ in group_totals.items() if a == account and m == month}
        if len(systems_in_combo) < 2:
            continue

        checked.add(combo)

        totals_by_system = {s: group_totals[(account, month, s)] for s in systems_in_combo}
        values = list(totals_by_system.values())
        spread = max(values) - min(values)

        if spread > tolerance:
            parts = [f"MISMATCH {account} {month} spread={spread:.2f}"]
            for s in "ABC":
                if s in totals_by_system:
                    parts.append(f"{s}={totals_by_system[s]:.2f}")
                else:
                    parts.append(f"{s}=-")
            mismatches.append(" ".join(parts))

    for line in mismatches:
        emit(line)
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check for malformed rows."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)
    total_rows = 0
    rejected_rows = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except LedgerParseError as exc:
            _log.warning("%s: %s", path, exc)
            return 2

        try:
            if system == "A":
                rows = system_a.read_rows(path)
                converter = row_to_record_a
                date_format = "%Y-%m-%d"
                date_key = "posted_on"
                amount_key = "amount"
                account_key = "account"
            elif system == "B":
                rows = system_b.read_rows(path)
                converter = row_to_record_b
                date_format = "%Y-%m-%d"
                date_key = "value_date"
                amount_key = "amount"
                account_key = "acct"
            else:
                rows = system_c.read_rows(path)
                converter = row_to_record_c
                date_format = "%d/%m/%Y"
                date_key = "txn_date"
                amount_key = "gross_amount"
                account_key = "ledger_acct"
        except OSError as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        for row in rows:
            total_rows += 1
            is_valid = True

            if date_key in row:
                try:
                    datetime.strptime(row[date_key].strip(), date_format)
                except ValueError:
                    _log.warning("%s: invalid date format: %s", path, row[date_key])
                    is_valid = False

            if amount_key in row:
                try:
                    if system == "B":
                        int(row[amount_key].strip())
                    else:
                        Decimal(row[amount_key].strip())
                except Exception:
                    _log.warning("%s: invalid amount: %s", path, row[amount_key])
                    is_valid = False

            if account_key in row:
                if not account_pattern.match(row[account_key].strip()):
                    _log.warning("%s: invalid account code: %s", path, row[account_key])
                    is_valid = False

            if not is_valid:
                rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    import os
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config
    handler = args.handler
    return int(handler(args))
