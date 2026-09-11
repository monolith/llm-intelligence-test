"""The ``python -m ledgerkit`` command line.

The subcommands are ``version``, ``inspect``, ``ingest``, ``report``,
``reconcile`` and ``validate``; ``SPEC.md`` describes the last four.  The global
``--config PATH`` option, given before the subcommand, makes one run read its
settings from another file.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.core.values import decimal_from_text
from ledgerkit.ingest import read_exports
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import reconcile_lines
from ledgerkit.recordfile import read_records, write_records
from ledgerkit.report import GROUPINGS, report_lines
from ledgerkit.validate import validate_files

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

# What "this file could not be read" looks like: a missing or unreadable file,
# bytes that are not UTF-8, or a file that is not the shape it should be.
_READ_ERRORS = (LedgerParseError, OSError, UnicodeDecodeError)

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
        value = decimal_from_text(text)
    except LedgerParseError:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number of dollars") from None
    if value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is negative")
    return value


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config", metavar="PATH", help="read this run's settings from PATH instead of config/settings.toml"
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized records file")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files from any of the systems")
    ingest_parser.add_argument(
        "--out", metavar="PATH", default=DEFAULT_RECORDS_PATH, help=f"where to write (default {DEFAULT_RECORDS_PATH})"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=GROUPINGS, help="which grouping to total by")
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted",
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
        help="dollars two systems may differ by and still agree (default: the [reconcile] tolerance setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files and report malformed rows")
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
    """Merge the named exports into one normalized records file.

    Nothing is written unless every file reads cleanly, so a bad export can never
    leave behind a records file that is missing postings.
    """
    settings = load_settings()
    try:
        records = read_exports([Path(name) for name in args.files], settings.unknown_account_label)
    except _READ_ERRORS as exc:
        _log.error("ingest stopped, nothing written: %s", exc)
        return 2
    try:
        written = write_records(records, Path(args.out))
    except OSError as exc:
        _log.error("cannot write %s: %s", args.out, exc)
        return 2
    emit(f"wrote={written} to {args.out}")
    return 0


def _load_records(path: Path) -> list[Record] | None:
    try:
        return read_records(path)
    except _READ_ERRORS as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized records file.

    Refunds are always counted; ``--include-refunds`` is accepted and changes nothing.
    """
    settings = load_settings()
    records = _load_records(Path(args.records))
    if records is None:
        return 2
    for line in report_lines(records, args.by, settings):
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree about."""
    settings = load_settings()
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    records = _load_records(Path(args.records))
    if records is None:
        return 2
    for line in reconcile_lines(records, tolerance):
        emit(line)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row; exit 2 if any row is rejected or any file is unreadable."""
    settings = load_settings()
    try:
        result = validate_files([Path(name) for name in args.files], settings.account_code_pattern)
    except re.error as exc:
        _log.error("[validate] account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2
    emit(f"checked={result.checked} rejected={result.rejected}")
    return 0 if result.passed() else 2


@contextmanager
def _settings_from(path: Path) -> Iterator[None]:
    """Make :func:`load_settings` read ``path`` for the length of the block.

    ``LEDGERKIT_CONFIG`` is the one way a run gets different settings (see
    ``docs/CONVENTIONS.md``), so ``--config`` sets it rather than giving
    ``load_settings`` a parameter.  The previous value comes back afterwards.
    """
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return int(handler(args))

    config = Path(args.config).expanduser()
    if not config.is_file():
        _log.error("settings file %s does not exist", config)
        return 2
    with _settings_from(config):
        return int(handler(args))
