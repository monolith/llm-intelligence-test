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

from ledgerkit import __version__, ingest, validate as validate_mod
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
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


def _decimal_argument(text: str) -> Decimal:
    """Parse a command line argument as a :class:`~decimal.Decimal`, never a float."""
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"not a decimal number: {text!r}") from exc


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        dest="config",
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

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge exports from any of the three systems into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", dest="out", default="out/records.csv", metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument(
        "--by", dest="by", choices=("account", "month"), required=True, help="grouping to total by"
    )
    report_parser.add_argument(
        "--records", dest="records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        dest="include_refunds",
        action="store_true",
        help="include postings with a negative amount in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", dest="records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        dest="tolerance",
        type=_decimal_argument,
        default=None,
        metavar="N",
        help="dollars; two systems agree when their totals differ by no more than this",
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


def _quantum(decimals: int) -> Decimal:
    """The :meth:`~decimal.Decimal.quantize` target for a given number of decimal places."""
    return Decimal(1).scaleb(-decimals)


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge any number of export files, from any of the three systems, into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(ingest.read_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError, ValueError, ArithmeticError) as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            return 1
    records.sort(key=sort_key)
    out_path = Path(args.out)
    count = ingest.write_normalized(records, out_path)
    emit(f"wrote={count} to {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = ingest.read_normalized(Path(args.records))
    if not args.include_refunds:
        records = [record for record in records if record.amount >= 0]
    quantum = _quantum(settings.decimals)

    if args.by == "account":
        totals: dict[str, Decimal] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        emit("account_code,account_name,total")
        for code in sorted(totals):
            name = account_name(code, settings.unknown_account_label)
            total = totals[code].quantize(quantum, rounding=ROUND_HALF_EVEN)
            emit(f"{code},{name},{settings.format_amount(total)}")
    else:
        month_totals: dict[str, Decimal] = {}
        for record in records:
            month_totals[record.month()] = month_totals.get(record.month(), Decimal(0)) + record.amount
        emit("month,total")
        for month in sorted(month_totals):
            total = month_totals[month].quantize(quantum, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(total)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree on the total."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = ingest.read_normalized(Path(args.records))

    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        per_system = groups.setdefault((record.account_code, record.month()), {})
        per_system[record.source_system] = per_system.get(record.source_system, Decimal(0)) + record.amount

    count = 0
    for code, month in sorted(groups):
        per_system = groups[(code, month)]
        if len(per_system) < 2:
            continue
        totals = list(per_system.values())
        spread = max(totals) - min(totals)
        if spread <= tolerance:
            continue
        count += 1
        parts = []
        for system in ("A", "B", "C"):
            if system in per_system:
                amount = per_system[system].quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
                parts.append(f"{system}={amount:.2f}")
            else:
                parts.append(f"{system}=-")
        spread_amount = spread.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        emit(f"MISMATCH {code} {month} spread={spread_amount:.2f} " + " ".join(parts))
    emit(f"mismatches={count}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    checked_total = 0
    rejected_total = 0
    read_failed = False

    for name in args.files:
        path = Path(name)
        try:
            checked, issues = validate_mod.scan_file(path, pattern)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            read_failed = True
            continue
        checked_total += checked
        rejected_total += len(issues)
        for issue in issues:
            _log.warning("%s line %d: %s", path.name, issue.line, issue.reason)

    emit(f"checked={checked_total} rejected={rejected_total}")
    return 2 if (rejected_total or read_failed) else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
