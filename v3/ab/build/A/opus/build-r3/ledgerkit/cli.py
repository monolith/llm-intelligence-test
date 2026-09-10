"""The ``python -m ledgerkit`` command line.

The subcommands are ``version``, ``inspect``, and the four specified in
``SPEC.md``: ``ingest``, ``report``, ``reconcile`` and ``validate``.  The global
``--config PATH`` option, given before the subcommand, points one run at another
settings file.

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
from ledgerkit.analysis import find_mismatches, round_for_display, totals_by_account, totals_by_month
from ledgerkit.build import read_records as read_export_records
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.normalized import read_records as read_normalized_records
from ledgerkit.normalized import write_records
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

# The warehouse team's sheet reads report output with semicolons.  This is the
# user's amendment to SPEC.md section 2; ingest output stays comma separated.
REPORT_DELIMITER = ";"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

# Errors that mean a file could not be read at all.  UnicodeDecodeError is a
# ValueError, and is listed so that a binary file is reported rather than raised.
_UNREADABLE = (LedgerParseError, OSError, UnicodeDecodeError)


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def _tolerance(text: str) -> Decimal:
    """Parse ``--tolerance`` as exact dollars."""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number of dollars") from None
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number of dollars zero or more")
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by", required=True, choices=("account", "month"), help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree (default: [reconcile] tolerance)",
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
    """Merge every posting in the named exports into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    failed = False
    for name in args.files:
        path = Path(name)
        try:
            records.extend(read_export_records(path, settings.unknown_account_label))
        except _UNREADABLE as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            failed = True
    if failed:
        _log.error("nothing written; every input file has to be readable")
        return 1

    records.sort(key=sort_key)
    try:
        count = write_records(records, Path(args.out))
    except OSError as exc:
        _log.error("cannot write %s: %s", args.out, exc)
        return 1
    emit(f"wrote={count} to {args.out}")
    return 0


def _load_normalized(name: str) -> list[Record] | None:
    """Read the normalized file for a report, or log why not and return ``None``."""
    try:
        return read_normalized_records(Path(name))
    except _UNREADABLE as exc:
        _log.error("cannot read records from %s: %s", name, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file.

    Refunds are counted in the totals whether or not ``--include-refunds`` is
    given; the flag is still accepted because operations scripts pass it.
    """
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1

    def shown(total: Decimal) -> str:
        return settings.format_amount(round_for_display(total, settings.decimals))

    if args.by == "account":
        emit(join_record(["account_code", "account_name", "total"], REPORT_DELIMITER))
        for code, name, total in totals_by_account(records):
            emit(join_record([code, name, shown(total)], REPORT_DELIMITER))
    else:
        emit(join_record(["month", "total"], REPORT_DELIMITER))
        for month, total in totals_by_month(records):
            emit(join_record([month, shown(total)], REPORT_DELIMITER))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree about."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = _load_normalized(args.records)
    if records is None:
        return 1

    def dollars(value: Decimal) -> str:
        return f"{round_for_display(value, 2):.2f}"

    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        per_system = " ".join(
            f"{system}={dollars(mismatch.totals[system]) if system in mismatch.totals else '-'}"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={dollars(mismatch.spread)} {per_system}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row and print how many rows were rejected."""
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
        path = Path(name)
        try:
            file_checked, file_rejected = validate_file(path, pattern)
        except _UNREADABLE as exc:
            _log.warning("cannot read %s: %s", path, exc)
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

    # --config is carried to load_settings() through LEDGERKIT_CONFIG, the one
    # way settings are chosen (docs/CONVENTIONS.md), and put back afterwards so
    # an in-process caller's environment is left as it was.
    config_file = Path(args.config).expanduser().resolve()
    if not config_file.is_file():
        parser.error(f"--config {args.config}: no such file")
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config_file)
    try:
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
