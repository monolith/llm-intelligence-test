"""The ``python -m ledgerkit`` command line.

Only two subcommands are wired up so far, ``version`` and ``inspect``.  The rest
of the commands the operations team has asked for are written up in ``SPEC.md``
and are not implemented yet.

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

from ledgerkit import __version__, ingest as ingest_
from ledgerkit import reconcile as reconcile_
from ledgerkit import report as report_
from ledgerkit import validate as validate_
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core.io import read_records
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
        dest="config",
        metavar="PATH",
        default=None,
        help="read settings from PATH instead of config/settings.toml for this run",
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
        "--out", default=str(ingest_.DEFAULT_OUT_PATH), metavar="PATH", help="where to write the normalized CSV"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="which grouping to total by")
    report_parser.add_argument(
        "--records", default=report_.DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="include postings with a negative amount in the totals"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="report where the systems disagree")
    reconcile_parser.add_argument(
        "--records", default=reconcile_.DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=Decimal, default=None, metavar="N", help="dollars two systems may differ by and still agree"
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
    """Merge the named export files into one normalized CSV."""
    settings = load_settings()
    paths = [Path(name) for name in args.files]
    out_path = Path(args.out)
    try:
        count = ingest_.ingest(paths, out_path, settings)
    except (LedgerParseError, OSError) as exc:
        _log.warning("ingest failed: %s", exc)
        return 1
    emit(f"wrote={count} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized file."""
    settings = load_settings()
    records = read_records(Path(args.records))
    if args.by == "account":
        emit("account_code,account_name,total")
        for code, name, total in report_.totals_by_account(records, include_refunds=args.include_refunds):
            rounded = report_.round_total(total, settings.decimals)
            emit(f"{code},{name},{settings.format_amount(rounded)}")
    else:
        emit("month,total")
        for month, total in report_.totals_by_month(records, include_refunds=args.include_refunds):
            rounded = report_.round_total(total, settings.decimals)
            emit(f"{month},{settings.format_amount(rounded)}")
    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Print account/month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = read_records(Path(args.records))
    results = reconcile_.mismatches(records, tolerance)
    for account_code, month, spread, per_system in results:
        parts = " ".join(
            f"{system}={per_system[system]:.2f}" if system in per_system else f"{system}=-"
            for system in reconcile_.SYSTEMS
        )
        emit(f"MISMATCH {account_code} {month} spread={spread:.2f} {parts}")
    emit(f"mismatches={len(results)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows without writing anything."""
    settings = load_settings()
    paths = [Path(name) for name in args.files]
    result = validate_.validate_files(paths, settings)
    emit(f"checked={result.checked} rejected={result.rejected}")
    if result.rejected > 0 or result.unreadable:
        return 2
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if getattr(args, "config", None):
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
