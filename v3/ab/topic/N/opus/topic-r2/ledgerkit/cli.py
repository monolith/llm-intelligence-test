"""The ``python -m ledgerkit`` command line.

The subcommands are ``version``, ``inspect``, ``ingest``, ``report``,
``reconcile`` and ``validate``; the last four are specified in ``SPEC.md``.  The
global ``--config PATH`` option points ``LEDGERKIT_CONFIG`` at ``PATH`` for the
length of one run, so every subcommand picks it up through
:func:`~ledgerkit.config.load_settings`.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import ledgerfile, totals
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import (
    SYSTEMS,
    count_data_lines,
    detect_system,
    read_records,
    system_a,
    system_b,
    system_c,
)
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = Path("out") / "records.csv"
REPORT_SEPARATOR = ";"

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
        type=Path,
        metavar="PATH",
        help="read this run's settings from PATH instead of the usual place",
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
        type=Path,
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"where to write the normalized file (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"), help="how to group the totals")
    _add_records_option(report_parser)
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; refunds are always included",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    _add_records_option(reconcile_parser)
    reconcile_parser.add_argument(
        "--tolerance",
        type=_decimal_argument,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree (default from settings)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows in exports")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _add_records_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--records",
        type=Path,
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )


def _decimal_argument(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a non-negative number")
    return value


def _load_records_file(path: Path) -> list[Record] | None:
    try:
        return ledgerfile.read_records(path)
    except (LedgerParseError, OSError) as exc:
        _log.error("cannot read records from %s: %s", path, exc)
        return None


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
    """Merge every posting in the named exports into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(read_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot ingest %s: %s; nothing written", path, exc)
            return 1
    records.sort(key=sort_key)
    count = ledgerfile.write_records(records, args.out)
    emit(f"wrote={count} to {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals from a normalized file, by account or by month.

    Refunds are always part of the totals; ``--include-refunds`` is accepted so
    that existing scripts keep working, and changes nothing.
    """
    settings = load_settings()
    records = _load_records_file(args.records)
    if records is None:
        return 1

    def shown(total: Decimal) -> str:
        return settings.format_amount(totals.round_total(total, settings.decimals))

    if args.by == "account":
        emit(REPORT_SEPARATOR.join(("account_code", "account_name", "total")))
        for code, (name, total) in totals.totals_by_account(records).items():
            emit(REPORT_SEPARATOR.join((code, name, shown(total))))
    else:
        emit(REPORT_SEPARATOR.join(("month", "total")))
        for month, total in totals.totals_by_month(records).items():
            emit(REPORT_SEPARATOR.join((month, shown(total))))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = _load_records_file(args.records)
    if records is None:
        return 1

    mismatches = totals.find_mismatches(records, tolerance)
    for mismatch in mismatches:
        per_system = " ".join(
            f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread:.2f} {per_system}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of the named exports and report how many were rejected."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("[validate] account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2

    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            result = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue
        checked += result.checked
        rejected += result.rejected
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code.

    ``--config PATH`` sets ``LEDGERKIT_CONFIG`` for the length of the run and puts
    back whatever was there before, so a caller that runs :func:`main` in
    process does not inherit it.
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is None:
        return int(args.handler(args))

    config = args.config.expanduser()
    if not config.is_file():
        parser.error(f"--config: {config} is not a file")
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config)
    try:
        return int(args.handler(args))
    finally:
        if previous is None:
            del os.environ[CONFIG_ENV_VAR]
        else:
            os.environ[CONFIG_ENV_VAR] = previous
