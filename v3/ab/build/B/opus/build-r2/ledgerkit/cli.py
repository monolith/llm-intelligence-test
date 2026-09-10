"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, and the four written up in ``SPEC.md``:
``ingest``, ``report``, ``reconcile`` and ``validate``.  The global ``--config``
option points one run at another settings file.

Two things ``report`` does differently from what ``SPEC.md`` says, at the
operations team's request: its fields are separated by semicolons, and refunds
are always counted in its totals.  ``--include-refunds`` is still accepted,
because scripts pass it, but it no longer changes anything.

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
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import recordfile
from ledgerkit.core.fields import join_record
from ledgerkit.core.reconcile import find_mismatches
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.core.totals import round_total, totals_by_account, totals_by_month
from ledgerkit.core.validate import validate_file
from ledgerkit.core.values import parse_decimal
from ledgerkit.log import get_logger
from ledgerkit.parsers import (
    SYSTEMS,
    count_data_lines,
    detect_system,
    read_records,
    system_a,
    system_b,
    system_c,
)

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"
REPORT_DELIMITER = ";"
EXIT_FAILURE = 2

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
        "--config", metavar="PATH", help="read this run's settings from PATH (a TOML file)"
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
        "--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument(
        "--by", required=True, choices=("account", "month"), help="grouping to total by"
    )
    report_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; refunds are always counted in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="list account and month totals the systems disagree on"
    )
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_tolerance_arg,
        default=None,
        metavar="N",
        help="dollars two system totals may differ by and still agree",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files for malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _tolerance_arg(text: str) -> Decimal:
    try:
        value = parse_decimal(text)
    except LedgerParseError as exc:
        raise argparse.ArgumentTypeError(f"{text!r} is not a number") from exc
    if value < 0:
        raise argparse.ArgumentTypeError(f"{text!r} is negative")
    return value


def _load_normalized(path: Path) -> list[Record] | None:
    """Read a normalized file, logging and returning ``None`` when it cannot be read."""
    try:
        return recordfile.read_records(path)
    except (OSError, ValueError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


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
    """Merge every posting from the named exports into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        try:
            records.extend(read_records(Path(name), settings.unknown_account_label))
        except (OSError, ValueError) as exc:
            _log.error("cannot ingest %s: %s", name, exc)
            return EXIT_FAILURE
    records.sort(key=sort_key)

    out = Path(args.out)
    try:
        count = recordfile.write_records(records, out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return EXIT_FAILURE
    emit(f"wrote={count} to {out}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month, fields separated by semicolons."""
    settings = load_settings()
    records = _load_normalized(Path(args.records))
    if records is None:
        return EXIT_FAILURE

    def shown(total: Decimal) -> str:
        return settings.format_amount(round_total(total, settings.decimals))

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
    """Print the account and month combinations where the systems' totals disagree."""
    settings = load_settings()
    records = _load_normalized(Path(args.records))
    if records is None:
        return EXIT_FAILURE
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance

    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        amounts = " ".join(
            f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread:.2f} {amounts}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of the named exports and print how many were rejected."""
    settings = load_settings()
    try:
        pattern = re.compile(settings.account_code_pattern)
    except re.error as exc:
        _log.error("account_code_pattern %r is not a valid pattern: %s", settings.account_code_pattern, exc)
        return EXIT_FAILURE

    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        try:
            result = validate_file(Path(name), pattern)
        except (OSError, ValueError) as exc:
            _log.error("cannot validate %s: %s", name, exc)
            unreadable = True
            continue
        checked += result.checked
        rejected += result.rejected
    emit(f"checked={checked} rejected={rejected}")
    return EXIT_FAILURE if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code.

    ``--config PATH`` is applied by pointing ``LEDGERKIT_CONFIG`` at ``PATH`` for
    the length of the run, so every command reads it through ``load_settings``.
    """
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler

    previous = os.environ.get(CONFIG_ENV_VAR)
    if args.config is not None:
        config = Path(args.config).expanduser()
        if not config.is_file():
            _log.error("settings file %s does not exist", config)
            return EXIT_FAILURE
        os.environ[CONFIG_ENV_VAR] = str(config)
    try:
        return int(handler(args))
    except tomllib.TOMLDecodeError as exc:
        _log.error("cannot read settings: %s", exc)
        return EXIT_FAILURE
    finally:
        if args.config is not None:
            if previous is None:
                os.environ.pop(CONFIG_ENV_VAR, None)
            else:
                os.environ[CONFIG_ENV_VAR] = previous
