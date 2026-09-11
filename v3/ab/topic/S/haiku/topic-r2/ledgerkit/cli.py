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

from ledgerkit import __version__
from ledgerkit.commands import ingest as ingest_module
from ledgerkit.commands import reconcile as reconcile_module
from ledgerkit.commands import report as report_module
from ledgerkit.commands import validate as validate_module
from ledgerkit.config import load_settings
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
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


def build_parser() -> argparse.ArgumentParser:
    """Assemble the argument parser for the whole command line."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description="Merge and report on ledger exports from systems A, B and C.",
    )
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="read settings from PATH instead of the usual place",
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
        "ingest", help="merge exports into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out",
        type=str,
        default="out/records.csv",
        help="output file (default: out/records.csv)",
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or month")
    report_parser.add_argument(
        "--by",
        type=str,
        choices=["account", "month"],
        required=True,
        help="group by account or month",
    )
    report_parser.add_argument(
        "--records",
        type=str,
        default="out/records.csv",
        help="normalized records file (default: out/records.csv)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="find account and month combinations where systems disagree"
    )
    reconcile_parser.add_argument(
        "--records",
        type=str,
        default="out/records.csv",
        help="normalized records file (default: out/records.csv)",
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=str,
        help="tolerance in dollars (default from config)",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files for malformed rows"
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
    """Merge export files into a normalized CSV."""
    settings = load_settings()
    out_path = Path(args.out)
    try:
        row_count = ingest_module.ingest(args.files, out_path, settings.unknown_account_label)
        emit(f"wrote={row_count} to {out_path}")
        return 0
    except Exception as exc:
        _log.error("ingest failed: %s", exc)
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    settings = load_settings()
    records_path = Path(args.records)
    if not records_path.exists():
        _log.error("records file not found: %s", records_path)
        return 1
    return report_module.report(records_path, args.by, settings)


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find and report mismatches between systems."""
    settings = load_settings()
    records_path = Path(args.records)
    if not records_path.exists():
        _log.error("records file not found: %s", records_path)
        return 1

    tolerance = settings.tolerance
    if args.tolerance is not None:
        tolerance = Decimal(args.tolerance)

    return reconcile_module.reconcile(records_path, tolerance, settings)


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files."""
    settings = load_settings()
    return validate_module.validate(args.files, settings)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    # Handle --config before parsing other arguments
    argv_list = list(argv) if argv is not None else None
    if argv_list is None:
        argv_list = None
    else:
        # Check for --config in argv and set environment variable
        if "--config" in argv_list:
            config_idx = argv_list.index("--config")
            if config_idx + 1 < len(argv_list):
                os.environ["LEDGERKIT_CONFIG"] = argv_list[config_idx + 1]

    parser = build_parser()
    args = parser.parse_args(argv_list)
    handler = args.handler
    return int(handler(args))
