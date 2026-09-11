"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, and the four written up in ``SPEC.md``,
``ingest``, ``report``, ``reconcile`` and ``validate``.  The global ``--config
PATH`` option, given before the subcommand, makes one run read its settings from
``PATH``.  It does that the one way ``docs/CONVENTIONS.md`` allows, by pointing
``LEDGERKIT_CONFIG`` at the file for the length of the run.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
import tomllib
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, config_path, load_settings
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.core.store import read_records, write_records
from ledgerkit.ingest import ingest_exports
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches, format_mismatch
from ledgerkit.report import GROUPINGS, report_lines
from ledgerkit.validate import validate_files

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS = "out/records.csv"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

# What can go wrong reading an input file: a missing or unreadable file, a file
# that is not UTF-8, or a file whose contents are not the shape they should be.
_READ_ERRORS = (LedgerParseError, OSError, UnicodeError)


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def _tolerance(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not a number of dollars: {text!r}") from None
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"must be zero or more dollars: {text!r}")
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
        help="read this run's settings from PATH, layered over config/settings.toml",
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
    ingest_parser.add_argument(
        "files", nargs="+", metavar="FILE", help="export files, from any of the three systems"
    )
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS, metavar="PATH", help="where to write (default: %(default)s)"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=GROUPINGS, help="which grouping to total by")
    report_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS,
        metavar="PATH",
        help="the normalized file to read (default: %(default)s)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted so existing scripts keep working; refunds are always counted",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS,
        metavar="PATH",
        help="the normalized file to read (default: %(default)s)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree (default: the setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows in exports")
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
    """Merge the named exports into one normalized records file."""
    settings = load_settings()
    try:
        records = ingest_exports([Path(name) for name in args.files], settings.unknown_account_label)
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


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized records file."""
    settings = load_settings()
    records = _load_records(args.records)
    if records is None:
        return 2
    for line in report_lines(records, args.by, settings):
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree on."""
    settings = load_settings()
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    records = _load_records(args.records)
    if records is None:
        return 2
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(format_mismatch(mismatch))
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row and print how many rows were rejected."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a regular expression: %s", settings.account_code_pattern, exc)
        return 2
    result = validate_files([Path(name) for name in args.files], pattern)
    emit(f"checked={result.checked} rejected={result.rejected}")
    return 0 if result.passed else 2


def _load_records(name: str) -> list[Record] | None:
    try:
        return read_records(Path(name))
    except _READ_ERRORS as exc:
        _log.error("cannot read records from %s: %s", name, exc)
        return None


@contextmanager
def _settings_from(path: Path) -> Iterator[None]:
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(path)
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous


def _run(handler: Callable[[argparse.Namespace], int], args: argparse.Namespace) -> int:
    try:
        return int(handler(args))
    except tomllib.TOMLDecodeError as exc:
        _log.error("cannot read settings from %s: %s", config_path(), exc)
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return _run(handler, args)

    chosen = Path(args.config).expanduser()
    if not chosen.is_file():
        _log.error("--config %s: no such settings file", args.config)
        return 2
    with _settings_from(chosen):
        return _run(handler, args)
