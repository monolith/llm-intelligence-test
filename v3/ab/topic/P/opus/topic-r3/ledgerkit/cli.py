"""The ``python -m ledgerkit`` command line.

Subcommands are ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile``
and ``validate``; ``SPEC.md`` describes the last four.  The global
``--config PATH`` option, given before the subcommand, makes one run read its
settings from ``PATH``.

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
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.records import LedgerParseError
from ledgerkit.core.store import read_normalized, write_normalized
from ledgerkit.log import get_logger
from ledgerkit.parsers import (
    count_data_lines,
    detect_system,
    read_all_records,
    system_a,
    system_b,
    system_c,
)
from ledgerkit.reconcile import reconcile_lines
from ledgerkit.report import GROUPINGS, report_lines
from ledgerkit.validate import validate_files

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
VALIDATION_FAILED = 2

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
    except InvalidOperation:
        value = Decimal("NaN")
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"expected a number of dollars, zero or more; got {text!r}")
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
        help="read this run's settings from PATH instead of config/settings.toml",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files, any system")
    ingest_parser.add_argument(
        "--out",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help="where to write the normalized file (default %(default)s)",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by", required=True, choices=GROUPINGS, help="group totals by account or by month"
    )
    report_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help="the normalized file to read (default %(default)s)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help="the normalized file to read (default %(default)s)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree (default: [reconcile] tolerance)",
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
    """Merge every export named into one normalized file.

    Every file is read before anything is written, so a file that cannot be read
    leaves no partial output behind.
    """
    settings = load_settings()
    try:
        records = read_all_records([Path(name) for name in args.files], settings.unknown_account_label)
        written = write_normalized(records, Path(args.out))
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("ingest failed: %s", exc)
        return 1
    emit(f"wrote={written} to {args.out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file.

    Refunds are always counted; ``--include-refunds`` is accepted and changes
    nothing.
    """
    settings = load_settings()
    try:
        records = read_normalized(Path(args.records))
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read %s: %s", args.records, exc)
        return 1
    for line in report_lines(records, args.by, settings):
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    try:
        records = read_normalized(Path(args.records))
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read %s: %s", args.records, exc)
        return 1
    for line in reconcile_lines(records, tolerance):
        emit(line)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files, logging a warning for each rejected row."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a regular expression: %s", settings.account_code_pattern, exc)
        return VALIDATION_FAILED
    result = validate_files([Path(name) for name in args.files], pattern)
    emit(f"checked={result.checked} rejected={result.rejected}")
    return 0 if result.passed else VALIDATION_FAILED


@contextmanager
def _settings_file(config: str | None) -> Iterator[None]:
    """Point ``LEDGERKIT_CONFIG`` at ``config`` for one run, then put it back.

    This is how ``--config`` works without giving ``load_settings`` a second way
    to be told where settings come from.
    """
    if config is None:
        yield
        return
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = config
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
    if args.config is not None and not Path(args.config).expanduser().is_file():
        parser.error(f"--config: {args.config} is not a file")
    with _settings_file(args.config):
        return int(args.handler(args))
