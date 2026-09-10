"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import csv
import os
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.checks import validate_file
from ledgerkit.config import CONFIG_ENV_VAR, Settings, load_settings
from ledgerkit.core.convert import records_from_export
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.reporting import (
    MISSING_SYSTEM,
    mismatches,
    read_records,
    round_total,
    totals_by_account,
    totals_by_month,
)

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

# The report command separates its columns with this.  The normalized records
# file is an ordinary comma separated CSV and is not affected.
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


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        default=None,
        help="read settings for this run from PATH instead of the usual settings file",
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
        "ingest", help="merge exports into one normalized records file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"where to write the normalized records (default {DEFAULT_RECORDS_PATH})",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="total the normalized records")
    report_parser.add_argument(
        "--by", choices=("account", "month"), required=True, help="what to total by"
    )
    report_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized records file to read (default {DEFAULT_RECORDS_PATH})",
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include refunds in the totals; they are included by default and this is accepted for compatibility",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations the systems disagree about"
    )
    reconcile_parser.add_argument(
        "--records",
        metavar="PATH",
        default=DEFAULT_RECORDS_PATH,
        help=f"the normalized records file to read (default {DEFAULT_RECORDS_PATH})",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        metavar="N",
        default=None,
        help="dollars of disagreement to allow (default comes from the settings file)",
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


def write_records(records: Sequence[Record], out_path: Path) -> None:
    """Write normalized records to a comma separated file."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge every named export into one normalized records file."""
    settings = load_settings()
    collected: list[Record] = []
    for name in args.files:
        try:
            collected.extend(records_from_export(Path(name), settings))
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", name, exc)
            return 1

    # keep_refunds is on because the normalized file is the whole ledger; the
    # default would silently leave every negative posting out of it.
    records = normalize(collected, keep_refunds=True)
    out_path = Path(args.out)
    write_records(records, out_path)
    emit(f"wrote={len(records)} to {out_path}")
    return 0


def _report_line(parts: Sequence[str]) -> str:
    return REPORT_DELIMITER.join(parts)


def cmd_report(args: argparse.Namespace) -> int:
    """Total the normalized records by account or by month."""
    settings = load_settings()
    try:
        records = read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot report: %s", exc)
        return 1

    if args.by == "account":
        emit(_report_line(("account_code", "account_name", "total")))
        totals = totals_by_account(records)
        for code in sorted(totals):
            name, total = totals[code]
            emit(_report_line((code, name, _format_total(total, settings))))
        return 0

    emit(_report_line(("month", "total")))
    months = totals_by_month(records)
    for month in sorted(months):
        emit(_report_line((month, _format_total(months[month], settings))))
    return 0


def _format_total(total: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_total(total, settings.decimals))


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    try:
        records = read_records(Path(args.records))
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot reconcile: %s", exc)
        return 1

    tolerance = settings.tolerance if args.tolerance is None else Decimal(str(args.tolerance))
    found = mismatches(records, tolerance)
    for code, month, spread, per_system in found:
        columns = " ".join(
            f"{letter}=" + (f"{per_system[letter]:.2f}" if letter in per_system else MISSING_SYSTEM)
            for letter in ("A", "B", "C")
        )
        emit(f"MISMATCH {code} {month} spread={spread:.2f} {columns}")
    emit(f"mismatches={len(found)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check every row of every named export."""
    settings = load_settings()
    checked = 0
    rejected = 0
    unreadable = False
    for name in args.files:
        path = Path(name)
        try:
            file_checked, file_rejected = validate_file(path, settings)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue
        checked += file_checked
        rejected += file_rejected

    emit(f"checked={checked} rejected={rejected}")
    if rejected or unreadable:
        return 2
    return 0


def apply_config_option(config: str | None) -> None:
    """Point this run's settings at ``config`` when the option was given.

    The settings loader takes no arguments; the environment is the one place a
    run says where its settings come from, so the flag sets it here.  Nothing
    under ``config/`` is touched.
    """
    if config is None:
        return
    os.environ[CONFIG_ENV_VAR] = str(Path(config).expanduser())


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    apply_config_option(args.config)
    handler = args.handler
    return int(handler(args))
