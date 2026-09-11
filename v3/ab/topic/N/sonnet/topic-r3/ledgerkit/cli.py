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
from collections.abc import Callable, Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__, validate
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import ledger_file
from ledgerkit.core.build import record_from_row
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

READERS_BY_SYSTEM: dict[str, Callable[[Path], list[dict[str, str]]]] = {
    "A": system_a.read_rows,
    "B": system_b.read_rows,
    "C": system_c.read_rows,
}


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def _dollar_amount(value: str) -> Decimal:
    """Parse a command line argument as a decimal number of dollars."""
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{value!r} is not a valid decimal amount") from exc


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

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized file")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", choices=("account", "month"), required=True, help="which grouping to total by")
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; totals always include refunds",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=_dollar_amount, default=None, metavar="N", help="dollars of allowed spread"
    )
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
    """Merge any number of export files into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            raw_rows = READERS_BY_SYSTEM[system](path)
            records.extend(record_from_row(system, row, settings.unknown_account_label) for row in raw_rows)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    records.sort(key=sort_key)
    out_path = Path(args.out)
    count = ledger_file.write_records(out_path, records)
    emit(f"wrote={count} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account code or by month from a normalized file."""
    settings = load_settings()
    records_path = Path(args.records)
    try:
        records = ledger_file.read_records(records_path)
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot report on %s: %s", records_path, exc)
        return 1

    # Refund handling was amended after SPEC.md was written: totals now always
    # include refunds, so --include-refunds is accepted but does nothing.
    quantum = Decimal(1).scaleb(-settings.decimals)

    totals: dict[str, Decimal] = {}
    if args.by == "account":
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
            names.setdefault(record.account_code, record.account_name)
        emit("account_code,account_name,total")
        for code in sorted(totals):
            rounded = totals[code].quantize(quantum)
            emit(f"{code},{names[code]},{settings.format_amount(rounded)}")
    else:
        for record in records:
            key = record.month()
            totals[key] = totals.get(key, Decimal(0)) + record.amount
        emit("month,total")
        for month in sorted(totals):
            rounded = totals[month].quantize(quantum)
            emit(f"{month},{settings.format_amount(rounded)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    records_path = Path(args.records)
    try:
        records = ledger_file.read_records(records_path)
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot reconcile %s: %s", records_path, exc)
        return 1

    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    cents = Decimal("0.01")

    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        per_system = totals.setdefault(key, {})
        per_system[record.source_system] = per_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches = 0
    for account_code, month in sorted(totals):
        per_system = totals[(account_code, month)]
        if len(per_system) < 2:
            continue
        spread = max(per_system.values()) - min(per_system.values())
        if spread <= tolerance:
            continue
        mismatches += 1
        amounts = " ".join(
            f"{system}={per_system[system].quantize(cents)}" if system in per_system else f"{system}=-"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {account_code} {month} spread={spread.quantize(cents)} {amounts}")
    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
    settings = load_settings()
    checked_total = 0
    rejected_total = 0
    any_failure = False
    for name in args.files:
        result = validate.validate_file(Path(name), settings.account_code_pattern)
        if result is None:
            any_failure = True
            continue
        checked, rejected = result
        checked_total += checked
        rejected_total += rejected

    emit(f"checked={checked_total} rejected={rejected_total}")
    return 2 if rejected_total > 0 or any_failure else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is not None:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
