"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``.  The global ``--config PATH`` option, given before the subcommand,
makes one run read its settings from ``PATH``; it does so by pointing
``LEDGERKIT_CONFIG`` at that file for the length of the run, which is the one
way ``docs/CONVENTIONS.md`` allows settings to be redirected.

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
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.core.store import read_records as read_records_file
from ledgerkit.core.store import write_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, read_records, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches
from ledgerkit.report import round_total, totals_by_account, totals_by_month
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

# ``report`` separates its columns with semicolons because the warehouse team's
# spreadsheet expects them.  The ``ingest`` output stays comma separated.
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
        metavar="PATH",
        default=None,
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files from any system")
    ingest_parser.add_argument(
        "--out",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"where to write the normalized file (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by", required=True, choices=("account", "month"), help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="show where the systems disagree")
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=_decimal_argument,
        default=None,
        help="dollars two systems may differ by and still agree (default: the [reconcile] tolerance setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files for malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _decimal_argument(text: str) -> Decimal:
    try:
        value = Decimal(text.strip())
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a non-negative number")
    return value


def _load_records(path: Path) -> list[Record] | None:
    try:
        return read_records_file(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
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
    """Merge every posting from the named exports into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    failed = False
    for name in args.files:
        path = Path(name)
        try:
            records.extend(read_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            failed = True
    if failed:
        # Writing the files that did read would silently leave postings out.
        _log.error("nothing written; fix or remove the files above and run again")
        return 2

    records.sort(key=sort_key)
    out = Path(args.out)
    try:
        count = write_records(records, out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return 2
    emit(f"wrote={count} to {out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = _load_records(Path(args.records))
    if records is None:
        return 2

    def shown(total: Decimal) -> str:
        return settings.format_amount(round_total(total, settings.decimals))

    if args.by == "account":
        emit(REPORT_SEPARATOR.join(("account_code", "account_name", "total")))
        for code, name, total in totals_by_account(records):
            emit(REPORT_SEPARATOR.join((code, name, shown(total))))
    else:
        emit(REPORT_SEPARATOR.join(("month", "total")))
        for month, total in totals_by_month(records):
            emit(REPORT_SEPARATOR.join((month, shown(total))))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree about."""
    settings = load_settings()
    records = _load_records(Path(args.records))
    if records is None:
        return 2
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(mismatch.to_line())
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row and print how many rows were rejected."""
    settings = load_settings()
    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            file_checked, file_rejected = validate_file(path, settings.account_code_pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError, re.error) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
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

    chosen = Path(args.config).expanduser()
    if not chosen.is_file():
        _log.error("settings file %s given with --config does not exist", chosen)
        return 2
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(chosen)
    try:
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
