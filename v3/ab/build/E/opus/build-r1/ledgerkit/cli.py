"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``.  The global ``--config PATH`` option, given before the subcommand,
points this run's settings at another TOML file.

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
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.ingest import read_export
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.report import find_mismatches, totals_by_account, totals_by_month
from ledgerkit.store import load_records, write_records
from ledgerkit.validate import check_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
REPORT_SEPARATOR = ";"

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
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from exc
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"must be a non-negative number: {text!r}")
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"), help="how to group the totals")
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; refunds are always included in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="report where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree (default: the [reconcile] tolerance setting)",
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
    """Merge every posting in the named exports into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(read_export(path, settings.unknown_account_label))
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot ingest %s: %s; nothing written", path, exc)
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


def _load_records_or_log(name: str) -> list[Record] | None:
    path = Path(name)
    try:
        return load_records(path)
    except (LedgerParseError, OSError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month, refunds included."""
    settings = load_settings()
    records = _load_records_or_log(args.records)
    if records is None:
        return 1
    sep = REPORT_SEPARATOR
    if args.by == "account":
        emit(sep.join(("account_code", "account_name", "total")))
        for account in totals_by_account(records):
            emit(sep.join((account.account_code, account.account_name, settings.format_amount(account.total))))
    else:
        emit(sep.join(("month", "total")))
        for month in totals_by_month(records):
            emit(sep.join((month.month, settings.format_amount(month.total))))
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations the systems disagree on."""
    settings = load_settings()
    records = _load_records_or_log(args.records)
    if records is None:
        return 1
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        amounts = " ".join(
            f"{system}={mismatch.by_system[system]:.2f}" if system in mismatch.by_system else f"{system}=-"
            for system in COLUMNS_BY_SYSTEM
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread:.2f} {amounts}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of the named exports and count the rejected ones."""
    settings = load_settings()
    try:
        re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return 2

    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            result = check_file(path, settings.account_code_pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue
        checked += result.checked
        rejected += len(result.rejections)
        for rejection in result.rejections:
            _log.warning("%s line %d: rejected: %s", path, rejection.line, rejection.reason)
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return int(handler(args))

    config_file = Path(args.config).expanduser()
    if not config_file.is_file():
        parser.error(f"--config: settings file {config_file} does not exist")
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config_file)
    try:
        try:
            load_settings()
        except ValueError as exc:
            parser.error(f"--config: cannot use settings file {config_file}: {exc}")
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
