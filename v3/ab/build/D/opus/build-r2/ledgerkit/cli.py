"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``, as written up in ``SPEC.md``.  The global ``--config PATH`` option,
given before the subcommand, makes one run read its settings from ``PATH``.

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
from ledgerkit.core.fields import join_record
from ledgerkit.core.normalized import read_records
from ledgerkit.core.records import LedgerParseError
from ledgerkit.ingest import ingest_files
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches
from ledgerkit.report import round_total, totals_by_account, totals_by_month
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
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
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"where to write the normalized file (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"), help="grouping")
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="count refunds in the totals; this is now the default and the flag is kept for existing scripts",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="report where the systems disagree")
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=_tolerance,
        default=None,
        help="dollars two systems may differ by and still agree (default from settings)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed export rows")
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
    """Merge the named exports into one normalized file and say how many rows it holds."""
    settings = load_settings()
    try:
        count = ingest_files([Path(name) for name in args.files], Path(args.out), settings.unknown_account_label)
    except (LedgerParseError, OSError) as exc:
        _log.error("ingest failed: %s", exc)
        return 1
    emit(f"wrote={count} to {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals from a normalized file, by account or by month.

    Refunds are always counted.  ``--include-refunds`` is accepted so that
    scripts which still pass it keep working, and changes nothing.
    """
    settings = load_settings()
    try:
        records = read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.error("cannot read %s: %s", args.records, exc)
        return 1

    def show(total: Decimal) -> str:
        return settings.format_amount(round_total(total, settings.decimals))

    if args.by == "account":
        emit(join_record(["account_code", "account_name", "total"], REPORT_DELIMITER))
        for code, name, total in totals_by_account(records):
            emit(join_record([code, name, show(total)], REPORT_DELIMITER))
    else:
        emit(join_record(["month", "total"], REPORT_DELIMITER))
        for month, total in totals_by_month(records):
            emit(join_record([month, show(total)], REPORT_DELIMITER))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    try:
        records = read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.error("cannot read %s: %s", args.records, exc)
        return 1
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(mismatch.to_line())
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check the named exports row by row; exit 2 if anything was rejected or unreadable."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2

    checked = 0
    rejected = 0
    unreadable = 0
    for name in args.files:
        path = Path(name)
        try:
            file_checked, file_rejected = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("%s: cannot be read: %s", path, exc)
            unreadable += 1
            continue
        checked += file_checked
        rejected += file_rejected

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is None:
        return int(args.handler(args))

    # load_settings() takes its override from the environment and nowhere else,
    # so --config is that same override, scoped to this one call.
    config = Path(args.config).expanduser()
    if not config.is_file():
        parser.error(f"--config: {config} is not a file")
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config)
    try:
        return int(args.handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
