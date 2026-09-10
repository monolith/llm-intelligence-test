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
import tomllib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, config_path, load_settings
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import (
    count_data_lines,
    detect_system,
    read_records,
    system_a,
    system_b,
    system_c,
)
from ledgerkit.reconcile import find_mismatches
from ledgerkit.records_file import read_records_file, write_records
from ledgerkit.report import account_report, month_report
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
        "ingest", help="merge exports from any of the three systems into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"where to write the normalized file (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser(
        "report", help="print totals by account or by month from a normalized file"
    )
    report_parser.add_argument(
        "--by", required=True, choices=("account", "month"), help="which grouping to total by"
    )
    _add_records_option(report_parser)
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    _add_records_option(reconcile_parser)
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree (default: the [reconcile] "
        "tolerance setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows without writing anything"
    )
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _tolerance(text: str) -> Decimal:
    """Read ``--tolerance`` as an exact, non-negative number of dollars."""
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from None
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"must be a number of dollars zero or above: {text!r}")
    return value


def _add_records_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )


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
    """Read every export named on the command line and write one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(read_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            return 1
    records.sort(key=sort_key)

    out = Path(args.out)
    try:
        written = write_records(records, out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return 1
    emit(f"wrote={written} to {out}")
    return 0


def _load_records(path: Path) -> list[Record] | None:
    """Read a normalized records file, or log why not and return ``None``."""
    try:
        return read_records_file(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file.

    Refunds are always counted.  ``--include-refunds`` is still accepted so that
    scripts written against the original spec keep working, and changes nothing.
    """
    settings = load_settings()
    records = _load_records(Path(args.records))
    if records is None:
        return 1
    if args.by == "account":
        lines = account_report(records, settings)
    else:
        lines = month_report(records, settings)
    for line in lines:
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    records = _load_records(Path(args.records))
    if records is None:
        return 1
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(mismatch.to_line())
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of every export named on the command line.

    Exits 2 when any row was rejected or any file could not be read, 0 otherwise.
    """
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2

    checked = rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            file_checked, file_rejected = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("%s: cannot be read: %s", path, exc)
            unreadable = True
            continue
        checked += file_checked
        rejected += file_rejected
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


@contextmanager
def _settings_from(path: Path) -> Iterator[None]:
    """Point ``LEDGERKIT_CONFIG`` at ``path`` for the duration of one run.

    ``load_settings()`` takes no arguments on purpose and the environment is the
    one place it looks, so ``--config`` says the same thing through the same door
    and puts the previous value back afterwards.
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


def _run(args: argparse.Namespace) -> int:
    try:
        return int(args.handler(args))
    except tomllib.TOMLDecodeError as exc:
        _log.error("cannot read settings from %s: %s", config_path(), exc)
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is None:
        return _run(args)
    config_file = Path(args.config).expanduser()
    if not config_file.is_file():
        parser.error(f"--config: {args.config} is not a readable file")
    with _settings_from(config_file.resolve()):
        return _run(args)
