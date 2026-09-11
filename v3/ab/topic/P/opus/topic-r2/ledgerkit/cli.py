"""The ``python -m ledgerkit`` command line.

The subcommands are ``version``, ``inspect``, ``ingest``, ``report``,
``reconcile`` and ``validate``, and the global ``--config PATH`` option points a
single run at another settings file.  ``SPEC.md`` describes what each one does.

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
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.core.store import read_records, write_records
from ledgerkit.core.values import parse_decimal
from ledgerkit.ingest import records_from_exports
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import reconcile_lines
from ledgerkit.report import GROUPINGS, report_lines
from ledgerkit.validate import validate_files

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


def _tolerance(text: str) -> Decimal:
    try:
        value = parse_decimal(text, "tolerance")
    except LedgerParseError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if value < 0:
        raise argparse.ArgumentTypeError(f"tolerance {text!r} is negative")
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
        "--out", metavar="PATH", default=DEFAULT_RECORDS_PATH, help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=GROUPINGS, help="what to total by")
    report_parser.add_argument(
        "--records", metavar="PATH", default=DEFAULT_RECORDS_PATH, help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always included in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="show where the systems disagree")
    reconcile_parser.add_argument(
        "--records", metavar="PATH", default=DEFAULT_RECORDS_PATH, help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=_tolerance,
        default=None,
        help="dollars two systems may differ by and still agree",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check exports for malformed rows")
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
    """Merge the exports named on the command line into one normalized file."""
    settings = load_settings()
    try:
        records = records_from_exports([Path(name) for name in args.files], settings.unknown_account_label)
        count = write_records(records, Path(args.out))
    except (ValueError, OSError) as exc:
        _log.error("ingest failed: %s", exc)
        return 1
    emit(f"wrote={count} to {args.out}")
    return 0


def _load_records(name: str) -> list[Record] | None:
    try:
        return read_records(Path(name))
    except (ValueError, OSError) as exc:
        _log.error("cannot read records file %s: %s", name, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals from a normalized file, by account or by month."""
    settings = load_settings()
    records = _load_records(args.records)
    if records is None:
        return 1
    for line in report_lines(records, args.by, settings):
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    records = _load_records(args.records)
    if records is None:
        return 1
    for line in reconcile_lines(records, tolerance):
        emit(line)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check exports for malformed rows and print how many were checked and rejected."""
    settings = load_settings()
    try:
        result = validate_files([Path(name) for name in args.files], settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2
    emit(f"checked={result.checked} rejected={result.rejected}")
    return 0 if result.passed() else 2


def _run_with_config(args: argparse.Namespace, path: Path) -> int:
    """Run the chosen command with ``LEDGERKIT_CONFIG`` pointed at ``path``.

    ``load_settings`` takes no arguments on purpose, so ``--config`` speaks to it
    the one way it listens: through the environment, for this run only.
    """
    if not path.is_file():
        _log.error("settings file %s does not exist", path)
        return 2
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(path)
    try:
        try:
            load_settings()
        except (ValueError, ArithmeticError, OSError) as exc:
            _log.error("cannot use settings file %s: %s", path, exc)
            return 2
        return int(args.handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is not None:
        return _run_with_config(args, Path(args.config).expanduser())
    return int(args.handler(args))
