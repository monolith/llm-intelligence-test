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
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__, parsers
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import fields
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record, read_csv, write_csv
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

VALIDATE_SPEC: dict[str, dict[str, object]] = {
    "A": {
        "account_field": "account",
        "date_field": "posted_on",
        "amount_field": "amount",
        "parse_date": system_a.parse_date,
        "read_header": system_a.read_header,
        "iter_data_lines": system_a.iter_data_lines,
    },
    "B": {
        "account_field": "acct",
        "date_field": "value_date",
        "amount_field": "amount",
        "parse_date": system_b.parse_date,
        "read_header": system_b.read_header,
        "iter_data_lines": system_b.iter_data_lines,
    },
    "C": {
        "account_field": "ledger_acct",
        "date_field": "txn_date",
        "amount_field": "gross_amount",
        "parse_date": system_c.parse_date,
        "read_header": system_c.read_header,
        "iter_data_lines": system_c.iter_data_lines,
    },
}

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
        help="read settings from PATH for this run instead of the usual place",
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
        "ingest", help="merge exports from any of the three systems into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument("--out", default="out/records.csv", metavar="PATH", help="where to write")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="how to group totals")
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="include postings with a negative amount in the totals"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument("--tolerance", type=Decimal, default=None, metavar="N", help="dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows in export files")
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


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports from any of the three systems into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        records.extend(parsers.read_records(Path(name), settings.unknown_account_label))
    normalized = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    count = write_csv(out_path, normalized)
    emit(f"wrote={count} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = read_csv(Path(args.records))
    if not args.include_refunds:
        records = [record for record in records if not record.is_refund()]

    exponent = Decimal(1).scaleb(-settings.decimals)

    if args.by == "account":
        totals: dict[str, Decimal] = {}
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
            names[record.account_code] = record.account_name
        emit("account_code,account_name,total")
        for code in sorted(totals):
            rounded = totals[code].quantize(exponent, rounding=ROUND_HALF_EVEN)
            emit(f"{code},{names[code]},{settings.format_amount(rounded)}")
    else:
        month_totals: dict[str, Decimal] = {}
        for record in records:
            month_totals[record.month()] = month_totals.get(record.month(), Decimal(0)) + record.amount
        emit("month,total")
        for month in sorted(month_totals):
            rounded = month_totals[month].quantize(exponent, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(rounded)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = read_csv(Path(args.records))

    totals: dict[tuple[str, str, str], Decimal] = {}
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        totals[key] = totals.get(key, Decimal(0)) + record.amount

    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for (code, month, system), total in totals.items():
        groups.setdefault((code, month), {})[system] = total

    count = 0
    for code, month in sorted(groups):
        by_system = groups[(code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread <= tolerance:
            continue
        count += 1
        parts = " ".join(
            f"{system}={by_system[system].quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN):.2f}"
            if system in by_system
            else f"{system}=-"
            for system in ("A", "B", "C")
        )
        spread_str = spread.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        emit(f"MISMATCH {code} {month} spread={spread_str:.2f} {parts}")
    emit(f"mismatches={count}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    checked = 0
    rejected = 0
    unreadable = False

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            spec = VALIDATE_SPEC[system]
            header = spec["read_header"](path)
            data_lines = list(spec["iter_data_lines"](path))
        except (LedgerParseError, OSError) as exc:
            _log.warning("%s: cannot read: %s", path, exc)
            unreadable = True
            continue

        for number, line in data_lines:
            checked += 1
            problems: list[str] = []
            values = fields.split_record(line)
            if len(values) != len(header):
                problems.append(f"expected {len(header)} fields, found {len(values)}")
            else:
                row = dict(zip(header, values, strict=True))
                date_raw = row[spec["date_field"]]
                try:
                    spec["parse_date"](date_raw)
                except ValueError:
                    problems.append(f"date {date_raw!r} is not valid")

                amount_raw = row[spec["amount_field"]]
                try:
                    Decimal(amount_raw.strip())
                except (InvalidOperation, ValueError):
                    problems.append(f"amount {amount_raw!r} is not a number")

                account_raw = row[spec["account_field"]]
                if not pattern.match(account_raw.strip()):
                    problems.append(f"account code {account_raw!r} does not match {settings.account_code_pattern!r}")

            if problems:
                rejected += 1
                _log.warning("%s line %d: %s", path.name, number, "; ".join(problems))

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
