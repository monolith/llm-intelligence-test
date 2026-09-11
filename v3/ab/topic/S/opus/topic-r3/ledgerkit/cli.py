"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``, as written up in ``SPEC.md``.  The global ``--config PATH`` option
makes one run read its settings from ``PATH``.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
import tomllib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, config_path, load_settings
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.core.store import read_normalized, write_normalized
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, read_records, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches
from ledgerkit.report import GROUPINGS, report_lines
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

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


def _dollars(text: str) -> Decimal:
    """Argument type for ``--tolerance``: a finite, non-negative dollar amount."""
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not a dollar amount: {text!r}") from None
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"not a non-negative dollar amount: {text!r}")
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files from A, B or C")
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help=f"where to write (default {DEFAULT_RECORDS_PATH})"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=GROUPINGS, help="which grouping to total by")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help=f"normalized file to read (default {DEFAULT_RECORDS_PATH})"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help=f"normalized file to read (default {DEFAULT_RECORDS_PATH})"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_dollars,
        metavar="N",
        help="dollars two system totals may differ by and still agree (default: the [reconcile] tolerance setting)",
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
    """Merge every posting in the named exports into one normalized file.

    Every file is read before anything is written, so a file that cannot be read
    leaves no half written output behind.
    """
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        try:
            records.extend(read_records(Path(name), settings.unknown_account_label))
        except (OSError, ValueError) as exc:
            _log.error("cannot ingest %s: %s", name, exc)
            return 1
    records.sort(key=sort_key)
    try:
        count = write_normalized(records, Path(args.out))
    except OSError as exc:
        _log.error("cannot write %s: %s", args.out, exc)
        return 1
    emit(f"wrote={count} to {args.out}")
    return 0


def _load_normalized(name: str) -> list[Record] | None:
    """Read a normalized file, logging and returning ``None`` when it cannot be read."""
    try:
        return read_normalized(Path(name))
    except (OSError, ValueError) as exc:
        _log.error("cannot read records from %s: %s", name, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1
    for line in report_lines(records, args.by, settings):
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations where the systems disagree."""
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(mismatch.to_line())
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
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
        try:
            file_checked, file_rejected = validate_file(Path(name), pattern)
        except (OSError, ValueError) as exc:
            _log.error("cannot read %s: %s", name, exc)
            unreadable = True
            continue
        checked += file_checked
        rejected += file_rejected
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


@contextmanager
def _settings_from(path: str | None) -> Iterator[None]:
    """Point ``LEDGERKIT_CONFIG`` at ``path`` for the length of one run.

    :func:`~ledgerkit.config.load_settings` takes no arguments on purpose, so
    ``--config`` goes through the same environment variable an operator would
    set by hand.  The previous value is put back afterwards, so calling
    :func:`main` in process does not leak one run's settings into the next.
    """
    if path is None:
        yield
        return
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = path
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
        _log.error("settings file %s does not exist", args.config)
        return 2
    with _settings_from(args.config):
        try:
            return int(args.handler(args))
        except tomllib.TOMLDecodeError as exc:
            _log.error("cannot read settings from %s: %s", config_path(), exc)
            return 2
