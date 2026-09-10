"""The ``python -m ledgerkit`` command line.

``version`` and ``inspect`` were the first two subcommands wired up; ``ingest``,
``report``, ``reconcile`` and ``validate`` implement the rest of ``SPEC.md``.

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
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import fields
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record, read_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

PARSERS_BY_SYSTEM = {
    "A": system_a,
    "B": system_b,
    "C": system_c,
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
        help="read settings from PATH instead of the usual place, for this run only",
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
    ingest_parser.add_argument("--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"), help="grouping to total by")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="include postings with a negative amount"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="normalized file to read"
    )
    reconcile_parser.add_argument("--tolerance", default=None, metavar="N", help="dollars of allowed spread")
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


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge any number of export files into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    status = 0
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            parser = PARSERS_BY_SYSTEM[system]
            raw_rows = parser.read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            status = 1
            continue
        for row in raw_rows:
            records.append(parser.to_record(row, settings.unknown_account_label))

    normalized = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {out_path}")
    return status


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = read_records(Path(args.records))
    if not args.include_refunds:
        records = [record for record in records if not record.is_refund()]

    quantum = Decimal(1).scaleb(-settings.decimals)

    if args.by == "account":
        totals: dict[str, Decimal] = defaultdict(Decimal)
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] += record.amount
            names[record.account_code] = record.account_name
        emit("account_code,account_name,total")
        for code in sorted(totals):
            total = totals[code].quantize(quantum)
            emit(f"{code},{names[code]},{settings.format_amount(total)}")
    else:
        month_totals: dict[str, Decimal] = defaultdict(Decimal)
        for record in records:
            month_totals[record.month()] += record.amount
        emit("month,total")
        for month in sorted(month_totals):
            total = month_totals[month].quantize(quantum)
            emit(f"{month},{settings.format_amount(total)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    records = read_records(Path(args.records))

    totals: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        totals[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches = 0
    for code, month in sorted(totals):
        by_system = totals[(code, month)]
        if len(by_system) < 2:
            continue
        values = list(by_system.values())
        spread = max(values) - min(values)
        if spread <= tolerance:
            continue
        mismatches += 1
        parts = " ".join(
            f"{letter}={by_system[letter]:.2f}" if letter in by_system else f"{letter}=-"
            for letter in ("A", "B", "C")
        )
        emit(f"MISMATCH {code} {month} spread={spread:.2f} {parts}")

    emit(f"mismatches={mismatches}")
    return 0


def _check_row(
    parser: object,
    header: list[str],
    values: list[str],
    account_pattern: re.Pattern[str],
) -> str | None:
    """Return a description of what is wrong with one data row, or ``None``."""
    if len(values) != len(header):
        return f"expected {len(header)} fields, found {len(values)}"

    row = dict(zip(header, values, strict=True))
    problems: list[str] = []

    try:
        parser.parse_date(row[parser.DATE_FIELD])
    except LedgerParseError as exc:
        problems.append(str(exc))

    try:
        parser.parse_amount(row[parser.AMOUNT_FIELD])
    except LedgerParseError as exc:
        problems.append(str(exc))

    account_code = row[parser.ACCOUNT_FIELD].strip()
    if not account_pattern.match(account_code):
        problems.append(f"account code {account_code!r} does not match the configured pattern")

    if not problems:
        return None
    return "; ".join(problems)


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)

    checked = 0
    rejected = 0
    unreadable = False

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            parser = PARSERS_BY_SYSTEM[system]
            header = parser.read_header(path)
            rows = parser.data_lines(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue

        for number, line in rows:
            values = fields.split_record(line) if system == "A" else line.split(",")

            problem = _check_row(parser, header, values, account_pattern)
            checked += 1
            if problem is not None:
                rejected += 1
                _log.warning("%s line %d: %s", path.name, number, problem)

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
