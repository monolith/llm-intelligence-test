"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``, as written up in ``SPEC.md``, plus the global ``--config`` option.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit import ingest as ingest_module
from ledgerkit import report as report_module
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.normalized import DEFAULT_RECORDS_PATH, read_records, write_records
from ledgerkit.reconcile import find_mismatches
from ledgerkit.validate import validate_file
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

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


def _decimal_argument(text: str) -> Decimal:
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a non-negative number")
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
        default=str(DEFAULT_RECORDS_PATH),
        help=f"where to write the normalized file (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"))
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=str(DEFAULT_RECORDS_PATH),
        help=f"normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    # Refunds are counted by default now; the flag stays so existing scripts
    # that pass it keep working.
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="count refunds in the totals (this is the default)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month totals the systems disagree on"
    )
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default=str(DEFAULT_RECORDS_PATH),
        help=f"normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=_decimal_argument,
        default=None,
        help="dollars two systems may differ by and still agree (default from settings)",
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
    """Merge every posting in the named exports into one normalized file."""
    settings = load_settings()
    exports: list[list[Record]] = []
    for name in args.files:
        path = Path(name)
        try:
            exports.append(ingest_module.read_export(path, settings.unknown_account_label))
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.error("cannot ingest %s: %s; nothing written", path, exc)
            return 2
    out = Path(args.out)
    try:
        count = write_records(ingest_module.merge(exports), out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return 2
    emit(f"wrote={count} to {out}")
    return 0


def _load_records(path: Path) -> list[Record] | None:
    try:
        return read_records(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month, columns separated by semicolons."""
    settings = load_settings()
    records = _load_records(Path(args.records))
    if records is None:
        return 2
    if args.by == "account":
        lines = report_module.account_lines(records, settings.decimals)
    else:
        lines = report_module.month_lines(records, settings.decimals)
    for line in lines:
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree on."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = _load_records(Path(args.records))
    if records is None:
        return 2
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(mismatch.line())
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check exports for malformed rows and print how many were rejected."""
    settings = load_settings()
    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            result = validate_file(path, settings.account_code_pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("%s: cannot be read: %s", path, exc)
            unreadable = True
            continue
        checked += result.checked
        rejected += result.rejected
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code.

    ``--config`` is applied by pointing ``LEDGERKIT_CONFIG`` at the file for the
    length of the run, so every handler's :func:`load_settings` call sees it.
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is None:
        return int(args.handler(args))

    config = Path(args.config).expanduser()
    if not config.is_file():
        _log.error("settings file %s given with --config does not exist", config)
        return 2
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config)
    try:
        return int(args.handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
