"""The ``python -m ledgerkit`` command line.

The subcommands are ``version``, ``inspect``, ``ingest``, ``report``,
``reconcile`` and ``validate``, and the global ``--config PATH`` option, given
before the subcommand, makes one run read its settings from ``PATH``.
``SPEC.md`` says what each of them does.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
import re
import tomllib
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, config_path, load_settings
from ledgerkit.core.recordfile import read_records, write_records
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.ingest import ingest_files
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reconcile import find_mismatches
from ledgerkit.report import account_report, month_report
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
        value = Decimal(text.strip())
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError(f"not a number of dollars: {text!r}") from exc
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
        "ingest", help="merge export files into one normalized records file"
    )
    ingest_parser.add_argument(
        "files", nargs="+", metavar="FILE", help="export files from any of the three systems"
    )
    ingest_parser.add_argument(
        "--out",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"where to write the records (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument(
        "--by", required=True, choices=("account", "month"), help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"the normalized records file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted so existing scripts keep working; refunds are always counted",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="list account and month totals the systems disagree on"
    )
    reconcile_parser.add_argument(
        "--records",
        default=DEFAULT_RECORDS_PATH,
        metavar="PATH",
        help=f"the normalized records file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance,
        default=None,
        metavar="N",
        help="dollars two systems may differ by and still agree "
        "(default: the [reconcile] tolerance setting)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files and report malformed rows, writing nothing"
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
    """Merge the exports named on the command line into one normalized records file.

    Nothing is written unless every file reads cleanly: a partial file would
    silently leave postings out.
    """
    settings = load_settings()
    try:
        records = ingest_files([Path(name) for name in args.files], settings.unknown_account_label)
    except (LedgerParseError, OSError) as exc:
        _log.error("ingest stopped, nothing written: %s", exc)
        return 1
    try:
        count = write_records(records, Path(args.out))
    except OSError as exc:
        _log.error("cannot write %s: %s", args.out, exc)
        return 1
    emit(f"wrote={count} to {args.out}")
    return 0


def _load_records(name: str) -> list[Record] | None:
    try:
        return read_records(Path(name))
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read records file %s: %s", name, exc)
        return None


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized records file.

    Every posting counts, refunds included, so ``--include-refunds`` changes
    nothing; it is accepted because the operations team's scripts pass it.
    """
    settings = load_settings()
    records = _load_records(args.records)
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
    """Print the account and month combinations whose system totals disagree."""
    settings = load_settings()
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    records = _load_records(args.records)
    if records is None:
        return 1
    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        emit(mismatch.describe())
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check the exports named on the command line; exit 2 if any row or file failed."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error(
            "[validate] account_code_pattern %r is not a regular expression: %s",
            settings.account_code_pattern,
            exc,
        )
        return 2
    summary = validate_files([Path(name) for name in args.files], pattern)
    emit(f"checked={summary.checked} rejected={summary.rejected}")
    return 0 if summary.passed else 2


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code.

    ``--config PATH`` is applied by pointing ``LEDGERKIT_CONFIG`` at ``PATH`` for
    the length of the run, which is the one way ``docs/CONVENTIONS.md`` allows a
    run to choose its settings.  The variable is put back afterwards, so a caller
    that runs :func:`main` in process does not inherit this run's settings.
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config is not None and not Path(args.config).expanduser().is_file():
        parser.error(f"--config {args.config}: no such settings file")

    previous = os.environ.get(CONFIG_ENV_VAR)
    if args.config is not None:
        os.environ[CONFIG_ENV_VAR] = args.config
    try:
        return int(args.handler(args))
    except tomllib.TOMLDecodeError as exc:
        _log.error("cannot read settings from %s: %s", config_path(), exc)
        return 2
    finally:
        if args.config is not None:
            if previous is None:
                os.environ.pop(CONFIG_ENV_VAR, None)
            else:
                os.environ[CONFIG_ENV_VAR] = previous
