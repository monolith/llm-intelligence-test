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
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH, load_settings
from ledgerkit.core.records import LedgerParseError
from ledgerkit.core.values import parse_decimal
from ledgerkit.ingest import ingest_exports
from ledgerkit.log import get_logger
from ledgerkit.normalized import read_records, write_records
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import reconcile_lines
from ledgerkit.report import GROUPINGS, report_lines
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
CONFIG_DIR = DEFAULT_CONFIG_PATH.parent

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
        default=None,
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

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge export files into one normalized records file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"where to write the records (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser(
        "report", help="print totals by account or by month from a records file"
    )
    report_parser.add_argument(
        "--by", required=True, choices=GROUPINGS, help="total by account code or by month"
    )
    report_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"the normalized records file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month totals the systems disagree on"
    )
    reconcile_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"the normalized records file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two system totals may differ by and still agree (default from settings)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows without writing anything"
    )
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _tolerance(text: str) -> Decimal:
    try:
        value = parse_decimal(text)
    except LedgerParseError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number of dollars") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is negative")
    return value


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


def _is_under_config(path: Path) -> bool:
    return path.resolve().is_relative_to(CONFIG_DIR.resolve())


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge the named exports into one normalized records file."""
    settings = load_settings()
    out = Path(args.out)
    if _is_under_config(out):
        _log.error("refusing to write %s: nothing under %s is written", out, CONFIG_DIR)
        return 1
    try:
        records = ingest_exports([Path(name) for name in args.files], settings.unknown_account_label)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot ingest: %s", exc)
        return 1
    try:
        count = write_records(records, out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return 1
    emit(f"wrote={count} to {out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals from a normalized records file, by account or by month.

    Refunds are counted whether or not ``--include-refunds`` is given; the flag
    is still accepted because the operations team's scripts pass it.
    """
    settings = load_settings()
    path = Path(args.records)
    try:
        records = read_records(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read %s: %s", path, exc)
        return 1
    for line in report_lines(records, args.by, settings):
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree on, then the count."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    path = Path(args.records)
    try:
        records = read_records(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read %s: %s", path, exc)
        return 1
    for line in reconcile_lines(records, tolerance):
        emit(line)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of the named exports and print how many were checked and rejected.

    Returns 2 when any row was rejected or any file could not be read at all.
    """
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2

    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            file_checked, file_rejected = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            unreadable = True
            continue
        checked += file_checked
        rejected += file_rejected

    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code.

    ``--config PATH`` points ``LEDGERKIT_CONFIG`` at ``PATH`` for the length of
    the run, which is the one way ``docs/CONVENTIONS.md`` allows a run to take
    its settings from somewhere else, and puts the previous value back after.
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return int(handler(args))

    config_file = Path(args.config).expanduser()
    if not config_file.is_file():
        _log.error("settings file %s does not exist", config_file)
        return 2
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config_file)
    try:
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
