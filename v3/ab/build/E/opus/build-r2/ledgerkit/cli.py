"""The ``python -m ledgerkit`` command line.

The subcommands are ``version``, ``inspect``, ``ingest``, ``report``,
``reconcile`` and ``validate``; ``SPEC.md`` describes the last four.  The global
``--config PATH`` option, given before the subcommand, points this one run at
another settings file.

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
from ledgerkit.config import CONFIG_ENV_VAR, Settings, load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.ledger import ingest_files, read_records, write_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reports import find_mismatches, round_total, totals_by_account, totals_by_month
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
# The warehouse team's sheet expects semicolons in report output.  The records
# file that ingest writes stays comma separated.
REPORT_DELIMITER = ";"

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


def _tolerance(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number of dollars") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a non-negative number of dollars")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help=f"read this run's settings from PATH (the same as setting {CONFIG_ENV_VAR})",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files from any system")
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help=f"where to write (default {DEFAULT_RECORDS_PATH})"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=["account", "month"], help="what to total by")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help=f"normalized file (default {DEFAULT_RECORDS_PATH})"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always included in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="list account months where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help=f"normalized file (default {DEFAULT_RECORDS_PATH})"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        metavar="N",
        help="largest spread in dollars that still counts as agreeing (default: the [reconcile] tolerance setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files and reject malformed rows")
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
    """Merge every posting from the named exports into one normalized file."""
    settings = load_settings()
    out = Path(args.out)
    try:
        records = ingest_files([Path(name) for name in args.files], settings.unknown_account_label)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.warning("cannot ingest, nothing written: %s", exc)
        return 1
    try:
        write_records(records, out)
    except OSError as exc:
        _log.warning("cannot write %s: %s", out, exc)
        return 1
    emit(f"wrote={len(records)} to {out}")
    return 0


def _load_records(name: str) -> list[Record] | None:
    try:
        return read_records(Path(name))
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.warning("cannot read records file %s: %s", name, exc)
        return None


def _display_total(value: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_total(value, settings.decimals))


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month, refunds included."""
    settings = load_settings()
    records = _load_records(args.records)
    if records is None:
        return 1
    if args.by == "account":
        emit(join_record(["account_code", "account_name", "total"], REPORT_DELIMITER))
        for code, name, total in totals_by_account(records):
            emit(join_record([code, name, _display_total(total, settings)], REPORT_DELIMITER))
    else:
        emit(join_record(["month", "total"], REPORT_DELIMITER))
        for month, total in totals_by_month(records):
            emit(join_record([month, _display_total(total, settings)], REPORT_DELIMITER))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account months where the systems' totals disagree by more than the tolerance."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = _load_records(args.records)
    if records is None:
        return 1
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        per_system = " ".join(
            f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread:.2f} {per_system}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of the named exports; exit 2 if any row or file is bad."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.warning("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2
    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        try:
            file_checked, file_rejected = validate_file(Path(name), pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("cannot validate %s: %s", name, exc)
            unreadable = True
            continue
        checked += file_checked
        rejected += file_rejected
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return int(handler(args))

    # load_settings() takes no arguments by design; the environment is the one
    # way to tell it where settings come from.  Put it back afterwards so an
    # in-process caller is left as it was.
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = args.config
    try:
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
