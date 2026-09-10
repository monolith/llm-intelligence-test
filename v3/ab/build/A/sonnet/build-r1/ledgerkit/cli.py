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
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from pathlib import Path

from ledgerkit import __version__, mapping
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import build, records_file, validate as validate_core
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


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def _decimal_arg(text: str) -> Decimal:
    """Parse a command line argument as a :class:`~decimal.Decimal`."""
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"invalid decimal value: {text!r}") from exc


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

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge export files from any of the three systems into one normalized CSV"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write the normalized CSV"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
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
        type=_decimal_arg,
        default=None,
        metavar="N",
        help="dollars; two systems agree when their totals differ by no more than this",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows without writing anything"
    )
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
    """Merge export files from any of the three systems into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    had_failure = False
    for name in args.files:
        path = Path(name)
        try:
            records.extend(build.build_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            had_failure = True
    records.sort(key=sort_key)
    out_path = Path(args.out)
    records_file.write_normalized(out_path, records)
    emit(f"wrote={len(records)} to {out_path}")
    return 1 if had_failure else 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month, read from a normalized file."""
    settings = load_settings()
    records = records_file.read_normalized(Path(args.records))
    if not args.include_refunds:
        records = [record for record in records if not record.is_refund()]
    quantum = Decimal(f"1e-{settings.decimals}")

    totals: dict[str, Decimal] = {}
    if args.by == "account":
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        emit("account_code,account_name,total")
        for code in sorted(totals):
            total = totals[code].quantize(quantum, rounding=ROUND_HALF_EVEN)
            name = mapping.account_name(code, settings.unknown_account_label)
            emit(f"{code},{name},{settings.format_amount(total)}")
    else:
        for record in records:
            totals[record.month()] = totals.get(record.month(), Decimal(0)) + record.amount
        emit("month,total")
        for month in sorted(totals):
            total = totals[month].quantize(quantum, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(total)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = records_file.read_normalized(Path(args.records))

    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = totals.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches = 0
    for account_code, month in sorted(totals):
        by_system = totals[(account_code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread <= tolerance:
            continue
        mismatches += 1
        spread_display = spread.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        parts = []
        for system in SYSTEMS:
            if system in by_system:
                amount = by_system[system].quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
                parts.append(f"{system}={amount}")
            else:
                parts.append(f"{system}=-")
        emit(f"MISMATCH {account_code} {month} spread={spread_display} " + " ".join(parts))
    emit(f"mismatches={mismatches}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    checked_total = 0
    rejected_total = 0
    had_failure = False
    for name in args.files:
        path = Path(name)
        try:
            checked, rejected = validate_core.scan_file(path, pattern)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            had_failure = True
            continue
        checked_total += checked
        rejected_total += rejected
    emit(f"checked={checked_total} rejected={rejected_total}")
    return 2 if (rejected_total or had_failure) else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
