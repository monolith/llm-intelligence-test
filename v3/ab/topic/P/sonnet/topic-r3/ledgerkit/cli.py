"""The ``python -m ledgerkit`` command line.

Everything this package prints goes through :func:`emit`.  Nothing else in the
package calls ``print``: diagnostics go to the project logger instead, so that a
run can be piped somewhere without warnings landing in the middle of the data.
"""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__, ingest, reconcile, report, validate
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import io as records_io
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS, count_data_lines, detect_system, system_a, system_b, system_c

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
        help="read settings from PATH instead of the usual place, for this run only",
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
    ingest_parser.add_argument("--out", default="out/records.csv", help="where to write the normalized file")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", choices=("account", "month"), required=True, help="how to group totals")
    report_parser.add_argument("--records", default="out/records.csv", help="the normalized file to read")
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="accepted for compatibility; refunds are included in totals by default",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account/month combinations where the systems disagree"
    )
    reconcile_parser.add_argument("--records", default="out/records.csv", help="the normalized file to read")
    reconcile_parser.add_argument("--tolerance", type=Decimal, default=None, help="dollars of allowed spread")
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
    """Merge any number of export files into one normalized CSV."""
    settings = load_settings()
    paths = [Path(name) for name in args.files]
    records = ingest.build_records(paths, settings.unknown_account_label)
    out_path = Path(args.out)
    records_io.write_records_csv(records, out_path)
    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized records file."""
    settings = load_settings()
    records = records_io.read_records_csv(Path(args.records))
    # Refunds are included in totals by default now; --include-refunds is kept
    # so existing scripts that pass it still work, but it has nothing left to do.
    include_refunds = True
    if args.by == "account":
        emit("account_code;account_name;total")
        for code, name, total in report.totals_by_account(records, include_refunds=include_refunds):
            emit(f"{code};{name};{report.format_total(total, settings)}")
    else:
        emit("month;total")
        for month, total in report.totals_by_month(records, include_refunds=include_refunds):
            emit(f"{month};{report.format_total(total, settings)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print account/month combinations where the systems disagree on the total."""
    settings = load_settings()
    records = records_io.read_records_csv(Path(args.records))
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    mismatches = reconcile.find_mismatches(records, tolerance)
    for code, month, by_system in mismatches:
        spread = max(by_system.values()) - min(by_system.values())
        amounts = " ".join(
            f"{letter}={by_system[letter]:.2f}" if letter in by_system else f"{letter}=-" for letter in SYSTEMS
        )
        emit(f"MISMATCH {code} {month} spread={spread:.2f} {amounts}")
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0
    any_unreadable = False
    for name in args.files:
        result = validate.validate_file(Path(name), settings)
        total_checked += result.checked
        total_rejected += result.rejected
        any_unreadable = any_unreadable or result.file_unreadable
    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected or any_unreadable else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
