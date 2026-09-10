"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import fields
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record, read_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

MODULES_BY_SYSTEM = {"A": system_a, "B": system_b, "C": system_c}

SYSTEM_LETTERS: tuple[str, ...] = ("A", "B", "C")


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
        default=None,
        help="read settings from PATH instead of config/settings.toml for this run",
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
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by", choices=("account", "month"), required=True, help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include postings with a negative amount in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=Decimal,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files without writing anything")
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
    """Merge any number of export files, from any of the three systems, into one CSV."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        system = detect_system(path)
        module = MODULES_BY_SYSTEM[system]
        for row in module.read_rows(path):
            records.append(module.to_record(row, settings.unknown_account_label))

    normalized = normalize(records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(",".join(RECORD_COLUMNS) + "\n")
        for record in normalized:
            handle.write(fields.join_record(record.to_row()) + "\n")

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def _quantize(value: Decimal, decimals: int) -> Decimal:
    """Round ``value`` to ``decimals`` places, half to even, per docs/CONVENTIONS.md."""
    return value.quantize(Decimal(1).scaleb(-decimals))


def cmd_report(args: argparse.Namespace) -> int:
    """Read a normalized file and print totals by account or by month."""
    settings = load_settings()
    records = read_records(Path(args.records))
    if not args.include_refunds:
        records = [record for record in records if not record.is_refund()]

    totals: dict[str, Decimal] = {}
    if args.by == "account":
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
            names[record.account_code] = record.account_name
        emit("account_code,account_name,total")
        for code in sorted(totals):
            total = _quantize(totals[code], settings.decimals)
            emit(f"{code},{names[code]},{settings.format_amount(total)}")
    else:
        for record in records:
            month = record.month()
            totals[month] = totals.get(month, Decimal(0)) + record.amount
        emit("month,total")
        for month in sorted(totals):
            total = _quantize(totals[month], settings.decimals)
            emit(f"{month},{settings.format_amount(total)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Read a normalized file and report account/month combinations that disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = read_records(Path(args.records))

    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        by_system = totals.setdefault(key, {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    count = 0
    for account, month in sorted(totals):
        by_system = totals[(account, month)]
        if len(by_system) < 2:
            continue
        values = list(by_system.values())
        spread = max(values) - min(values)
        if spread <= tolerance:
            continue
        count += 1
        parts = " ".join(
            f"{system}={_quantize(by_system[system], 2):.2f}" if system in by_system else f"{system}=-"
            for system in SYSTEM_LETTERS
        )
        emit(f"MISMATCH {account} {month} spread={_quantize(spread, 2):.2f} {parts}")

    emit(f"mismatches={count}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    checked = 0
    rejected = 0
    had_failure = False

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            module = MODULES_BY_SYSTEM[system]
            header = module.read_header(path)
            lines = module.iter_data_lines(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("%s: cannot be read: %s", path.name, exc)
            had_failure = True
            continue

        for number, line in lines:
            checked += 1
            reason = _bad_row_reason(module, header, line, pattern)
            if reason is not None:
                _log.warning("%s line %d: %s", path.name, number, reason)
                rejected += 1

    emit(f"checked={checked} rejected={rejected}")
    return 2 if (rejected or had_failure) else 0


def _bad_row_reason(module: Any, header: list[str], line: str, pattern: re.Pattern[str]) -> str | None:
    """Return why one raw data line should be rejected, or ``None`` when it is fine."""
    values = module.split_line(line)
    if len(values) != len(header):
        return f"expected {len(header)} fields, found {len(values)}"

    try:
        row = dict(zip(header, values, strict=True))
        date_raw = row[module.DATE_FIELD]
        amount_raw = row[module.AMOUNT_FIELD]
        code = row[module.ACCOUNT_FIELD].strip()
    except KeyError as exc:
        return f"header is missing the {exc} column"

    try:
        module.parse_date(date_raw)
    except (LedgerParseError, ValueError) as exc:
        return str(exc)

    try:
        module.parse_amount(amount_raw)
    except (LedgerParseError, ValueError) as exc:
        return str(exc)

    if not pattern.fullmatch(code):
        return f"account code {code!r} does not match {pattern.pattern!r}"

    return None


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
