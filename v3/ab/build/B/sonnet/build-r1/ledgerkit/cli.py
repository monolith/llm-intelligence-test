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

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, load_settings
from ledgerkit.core import build, io
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, system_a, system_b, system_c
from ledgerkit.validate import validate_file

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
        dest="config_path",
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

    ingest_parser = subparsers.add_parser(
        "ingest", help="merge exports from any of the three systems into one normalized file"
    )
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to merge")
    ingest_parser.add_argument(
        "--out", default="out/records.csv", metavar="PATH", help="where to write the normalized file"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or by month")
    report_parser.add_argument(
        "--by", choices=("account", "month"), required=True, help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="refunds are always included in report totals; this flag is accepted for compatibility",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="report account and month combinations where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", default="out/records.csv", metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance",
        type=Decimal,
        default=None,
        metavar="N",
        help="dollars; default is the [reconcile] tolerance setting",
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser(
        "validate", help="check export files row by row without writing anything"
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
    """Merge exports from any of the three systems into one normalized file."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        path = Path(name)
        try:
            records.extend(build.read_records(path, settings.unknown_account_label))
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            return 1

    merged = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    io.write_records(merged, out_path)
    emit(f"wrote={len(merged)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month from a normalized records file."""
    settings = load_settings()
    records_path = Path(args.records)
    try:
        records = io.read_records(records_path)
    except (LedgerParseError, OSError) as exc:
        _log.error("cannot report on %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        totals: dict[str, Decimal] = {}
        names: dict[str, str] = {}
        for record in records:
            totals[record.account_code] = totals.get(record.account_code, Decimal("0")) + record.amount
            names[record.account_code] = record.account_name
        emit("account_code;account_name;total")
        for code in sorted(totals):
            emit(f"{code};{names[code]};{settings.format_amount(totals[code])}")
    else:
        month_totals: dict[str, Decimal] = {}
        for record in records:
            key = record.month()
            month_totals[key] = month_totals.get(key, Decimal("0")) + record.amount
        emit("month;total")
        for month in sorted(month_totals):
            emit(f"{month};{settings.format_amount(month_totals[month])}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account and month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = settings.tolerance if args.tolerance is None else args.tolerance
    records_path = Path(args.records)
    try:
        records = io.read_records(records_path)
    except (LedgerParseError, OSError) as exc:
        _log.error("cannot reconcile %s: %s", records_path, exc)
        return 1

    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        per_system = groups.setdefault((record.account_code, record.month()), {})
        per_system[record.source_system] = per_system.get(record.source_system, Decimal("0")) + record.amount

    mismatches: list[tuple[str, str, Decimal, dict[str, Decimal]]] = []
    for (code, month), per_system in groups.items():
        if len(per_system) < 2:
            continue
        spread = max(per_system.values()) - min(per_system.values())
        if spread > tolerance:
            mismatches.append((code, month, spread, per_system))
    mismatches.sort(key=lambda item: (item[0], item[1]))

    for code, month, spread, per_system in mismatches:
        parts = [f"MISMATCH {code} {month}", f"spread={spread:.2f}"]
        for system in ("A", "B", "C"):
            value = per_system.get(system)
            parts.append(f"{system}={value:.2f}" if value is not None else f"{system}=-")
        emit(" ".join(parts))
    emit(f"mismatches={len(mismatches)}")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
    settings = load_settings()
    total_checked = 0
    total_rejected = 0
    any_unreadable = False

    for name in args.files:
        path = Path(name)
        try:
            checked, rejected = validate_file(path, settings)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            any_unreadable = True
            continue
        total_checked += checked
        total_rejected += rejected

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if any_unreadable or total_rejected else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config_path:
        os.environ[CONFIG_ENV_VAR] = args.config_path
    handler = args.handler
    return int(handler(args))
