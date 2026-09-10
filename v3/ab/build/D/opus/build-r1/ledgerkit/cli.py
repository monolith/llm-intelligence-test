"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``.  The global ``--config PATH`` option, given before the subcommand,
makes one run read its settings from ``PATH``.

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

from ledgerkit import __version__, ledger
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches
from ledgerkit.report import round_total, totals_by_account, totals_by_month
from ledgerkit.validate import validate_files

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

# The warehouse team's sheet imports report output with semicolons.
REPORT_DELIMITER = ";"
EXIT_REJECTED = 2


def emit(line: str) -> None:
    """Write one line of program output.

    This is the only place in the package that writes to standard output.
    """
    print(line)


def _dollars(text: str) -> Decimal:
    """argparse type for a non negative dollar amount, read straight to Decimal."""
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is not a non negative number")
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
        default=str(ledger.DEFAULT_RECORDS_PATH),
        help="where to write the normalized file (default: %(default)s)",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"), help="grouping to total by")
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=str(ledger.DEFAULT_RECORDS_PATH),
        help="normalized file to read (default: %(default)s)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always counted in report totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default=str(ledger.DEFAULT_RECORDS_PATH),
        help="normalized file to read (default: %(default)s)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=_dollars,
        default=None,
        help="dollars two systems may differ by and still agree (default: the [reconcile] setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows in export files")
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
    """Merge the named exports into one normalized file."""
    settings = load_settings()
    out = Path(args.out)
    try:
        records = ledger.ingest([Path(name) for name in args.files], settings.unknown_account_label)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("ingest stopped, nothing written: %s", exc)
        return 1
    try:
        count = ledger.write_records(records, out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return 1
    emit(f"wrote={count} to {out}")
    return 0


def _load_normalized(name: str) -> list[Record] | None:
    """Read a normalized file, logging and returning ``None`` when it cannot be read."""
    path = Path(name)
    try:
        return ledger.load_records(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1

    def total(value: Decimal) -> str:
        return settings.format_amount(round_total(value, settings.decimals))

    if args.by == "account":
        emit(join_record(["account_code", "account_name", "total"], REPORT_DELIMITER))
        for code, name, value in totals_by_account(records):
            emit(join_record([code, name, total(value)], REPORT_DELIMITER))
    else:
        emit(join_record(["month", "total"], REPORT_DELIMITER))
        for month, value in totals_by_month(records):
            emit(join_record([month, total(value)], REPORT_DELIMITER))
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
        amounts = [
            f"{system}={round_total(mismatch.totals[system], 2):.2f}" if system in mismatch.totals else f"{system}=-"
            for system in SYSTEMS
        ]
        emit(
            f"MISMATCH {mismatch.account_code} {mismatch.month} "
            f"spread={round_total(mismatch.spread, 2):.2f} " + " ".join(amounts)
        )
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row and report how many rows were rejected."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("[validate] account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return EXIT_REJECTED
    summary = validate_files([Path(name) for name in args.files], pattern)
    emit(f"checked={summary.checked} rejected={summary.rejected}")
    if summary.rejected or summary.unreadable:
        return EXIT_REJECTED
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return int(handler(args))

    # load_settings() takes its override from the environment and nowhere else,
    # so --config is that same override, scoped to this one call.
    config = Path(args.config).expanduser()
    if not config.is_file():
        parser.error(f"--config {args.config}: no such file")
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config)
    try:
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
