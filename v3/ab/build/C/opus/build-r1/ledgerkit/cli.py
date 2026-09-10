"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``, as written up in ``SPEC.md``.  The global ``--config PATH`` option,
given before the subcommand, points one run at another settings file.

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
from ledgerkit.core.store import read_records, write_records
from ledgerkit.log import get_logger
from ledgerkit.parsers import (
    count_data_lines,
    detect_system,
    read_export,
    system_a,
    system_b,
    system_c,
)
from ledgerkit.reports import (
    account_report,
    find_mismatches,
    format_mismatch,
    month_report,
    totals_by_account,
    totals_by_month,
)
from ledgerkit.validate import check_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
VALIDATION_FAILED = 2
BAD_CONFIG = 2

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


def _tolerance_argument(text: str) -> Decimal:
    """Read ``--tolerance`` as a non-negative number of dollars."""
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"not a number of dollars: {text!r}") from None
    if not value.is_finite() or value < 0:
        raise argparse.ArgumentTypeError(f"not a non-negative number of dollars: {text!r}")
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

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge exports from any of the systems into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"where to write the normalized file (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument(
        "--by", required=True, choices=("account", "month"), help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="count refunds in the totals; this is already the default, and the "
        "flag is accepted so existing scripts keep working",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="list account and month combinations the systems disagree on"
    )
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        type=_tolerance_argument,
        default=None,
        help="dollars two system totals may differ by and still agree "
        "(default: the [reconcile] tolerance setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check exports for malformed rows without writing anything"
    )
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

    If any export cannot be read, nothing is written, because a merged file with
    a whole export missing from it would look complete and not be.
    """
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(read_export(path, settings.unknown_account_label))
        except (ValueError, OSError) as exc:
            _log.error("cannot ingest %s: %s; nothing written", path, exc)
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
    """Read the normalized file, or log why not and return ``None``."""
    try:
        return read_records(Path(name))
    except (ValueError, OSError) as exc:
        _log.error("cannot read records from %s: %s", name, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from the normalized file.

    Refunds are counted in the totals whether or not ``--include-refunds`` is
    given.
    """
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1
    if args.by == "account":
        lines = account_report(totals_by_account(records), settings)
    else:
        lines = month_report(totals_by_month(records), settings)
    for line in lines:
        emit(line)
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print the account and month combinations on which the systems disagree."""
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(format_mismatch(mismatch))
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of the named exports and print how many were rejected."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)
    checked = 0
    rejected = 0
    status = 0
    for name in args.files:
        path = Path(name)
        try:
            result = check_file(path, pattern)
        except (ValueError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            status = VALIDATION_FAILED
            continue
        checked += result.checked
        rejected += result.rejected
    if rejected:
        status = VALIDATION_FAILED
    emit(f"checked={checked} rejected={rejected}")
    return status


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    if args.config is None:
        return int(handler(args))

    # load_settings() takes no arguments; the environment is the one place a
    # run says where its settings come from, so --config sets it for this run
    # and puts it back afterwards for callers that run main() in process.
    config_file = Path(args.config).expanduser()
    if not config_file.is_file():
        _log.error("settings file %s does not exist", config_file)
        return BAD_CONFIG
    previous = os.environ.get(CONFIG_ENV_VAR)
    os.environ[CONFIG_ENV_VAR] = str(config_file)
    try:
        return int(handler(args))
    finally:
        if previous is None:
            os.environ.pop(CONFIG_ENV_VAR, None)
        else:
            os.environ[CONFIG_ENV_VAR] = previous
