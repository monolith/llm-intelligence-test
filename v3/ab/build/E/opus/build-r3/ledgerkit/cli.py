"""The ``python -m ledgerkit`` command line.

Subcommands: ``version``, ``inspect``, ``ingest``, ``report``, ``reconcile`` and
``validate``, as written up in ``SPEC.md``.  The global ``--config PATH`` option,
given before the subcommand, points this run at another settings file by setting
``LEDGERKIT_CONFIG``, which is the one way :func:`~ledgerkit.config.load_settings`
takes to be told where settings come from.

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
from ledgerkit.config import CONFIG_ENV_VAR, Settings, load_settings
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.core.store import load_records, write_records
from ledgerkit.core.totals import find_mismatches, round_for_display, totals_by_account, totals_by_month
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, read_records, system_a, system_b, system_c
from ledgerkit.parsers.validate import validate_file

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = Path("out") / "records.csv"
# The warehouse team's sheet is set up for semicolons.  This is report output
# only; the normalized file ingest writes stays comma separated.
REPORT_DELIMITER = ";"

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
        raise argparse.ArgumentTypeError(f"not a number: {text!r}") from exc
    if not value.is_finite():
        raise argparse.ArgumentTypeError(f"not a number: {text!r}")
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
        help=f"read this run's settings from PATH (sets {CONFIG_ENV_VAR})",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files from any system")
    ingest_parser.add_argument(
        "--out", default=str(DEFAULT_RECORDS_PATH), metavar="PATH", help="where to write (default: %(default)s)"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", required=True, choices=("account", "month"), help="how to group the totals")
    report_parser.add_argument(
        "--records",
        default=str(DEFAULT_RECORDS_PATH),
        metavar="PATH",
        help="normalized file to read (default: %(default)s)",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for existing scripts; refunds are always included in the totals",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="report where the systems disagree")
    reconcile_parser.add_argument(
        "--records",
        default=str(DEFAULT_RECORDS_PATH),
        metavar="PATH",
        help="normalized file to read (default: %(default)s)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=_decimal_argument,
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
        count = write_records(records, out)
    except OSError as exc:
        _log.error("cannot write %s: %s", out, exc)
        return 1
    emit(f"wrote={count} to {out}")
    return 0


def _load_normalized(name: str) -> list[Record] | None:
    path = Path(name)
    try:
        return load_records(path)
    except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
        _log.error("cannot read records file %s: %s", path, exc)
        return None


def _display_total(value: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_for_display(value, settings.decimals))


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account code or by month, refunds included."""
    settings = load_settings()
    records = _load_normalized(args.records)
    if records is None:
        return 1

    if args.by == "account":
        emit(fields.join_record(["account_code", "account_name", "total"], REPORT_DELIMITER))
        for code, name, total in totals_by_account(records):
            emit(fields.join_record([code, name, _display_total(total, settings)], REPORT_DELIMITER))
    else:
        emit(fields.join_record(["month", "total"], REPORT_DELIMITER))
        for month, total in totals_by_month(records):
            emit(fields.join_record([month, _display_total(total, settings)], REPORT_DELIMITER))
    return 0


def _cents(value: Decimal) -> str:
    return f"{round_for_display(value, 2):.2f}"


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print each account and month where the systems' totals differ by more than the tolerance."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = _load_normalized(args.records)
    if records is None:
        return 1

    mismatches = find_mismatches(records, tolerance)
    for mismatch in mismatches:
        systems = " ".join(
            f"{system}={_cents(mismatch.totals[system]) if system in mismatch.totals else '-'}"
            for system in SYSTEMS
        )
        emit(f"MISMATCH {mismatch.account_code} {mismatch.month} spread={_cents(mismatch.spread)} {systems}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of every export named on the command line."""
    settings = load_settings()
    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            result = validate_file(path, settings.account_code_pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError, re.error) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue
        checked += result.checked
        rejected += result.rejected
    emit(f"checked={checked} rejected={rejected}")
    return 2 if rejected or unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
