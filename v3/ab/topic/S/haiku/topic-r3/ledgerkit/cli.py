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
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import config_path, load_settings
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.operations import ingest, reconcile, report_by_account, report_by_month, validate
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

    # Global --config option
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="config file for this run",
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
    ingest_parser.add_argument("--out", type=str, default="out/records.csv", help="output file")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping")
    report_parser.add_argument("--records", type=str, default="out/records.csv", help="records file")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where the systems disagree")
    reconcile_parser.add_argument("--records", type=str, default="out/records.csv", help="records file")
    reconcile_parser.add_argument("--tolerance", type=float, default=None, help="tolerance in dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to validate")
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
    """Merge exports into one normalized file."""
    settings = load_settings()
    files = [Path(f) for f in args.files]
    out_path = Path(args.out)

    try:
        count = ingest(files, out_path, settings)
        emit(f"wrote={count} to {out_path}")
        return 0
    except (LedgerParseError, OSError) as exc:
        _log.warning("ingest failed: %s", exc)
        return 1


def cmd_report(args: argparse.Namespace) -> int:
    """Generate report by account or month."""
    settings = load_settings()
    records_path = Path(args.records)

    try:
        # Read records from CSV
        records = []
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return 1
            for row in reader:
                from datetime import datetime
                from decimal import Decimal
                records.append({
                    "record_id": row["record_id"],
                    "source_system": row["source_system"],
                    "date": datetime.fromisoformat(row["date"]).date(),
                    "account_code": row["account_code"],
                    "account_name": row["account_name"],
                    "description": row["description"],
                    "amount": Decimal(row["amount"]),
                })

        # Convert dicts to Record objects
        from ledgerkit.core.records import Record
        record_objects = [Record(**r) for r in records]

        # Generate report
        if args.by == "account":
            lines = report_by_account(record_objects, settings)
        else:
            lines = report_by_month(record_objects, settings)

        for line in lines:
            emit(line)
        return 0
    except (OSError, ValueError) as exc:
        _log.warning("report failed: %s", exc)
        return 1


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find mismatched account/month combinations."""
    settings = load_settings()

    # Override tolerance if provided
    if args.tolerance is not None:
        from decimal import Decimal
        settings = settings.__class__(
            decimals=settings.decimals,
            unknown_account_label=settings.unknown_account_label,
            tolerance=Decimal(str(args.tolerance)),
            account_code_pattern=settings.account_code_pattern,
            source_path=settings.source_path,
        )

    records_path = Path(args.records)

    try:
        # Read records from CSV
        records = []
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return 1
            for row in reader:
                from datetime import datetime
                from decimal import Decimal
                records.append({
                    "record_id": row["record_id"],
                    "source_system": row["source_system"],
                    "date": datetime.fromisoformat(row["date"]).date(),
                    "account_code": row["account_code"],
                    "account_name": row["account_name"],
                    "description": row["description"],
                    "amount": Decimal(row["amount"]),
                })

        # Convert dicts to Record objects
        from ledgerkit.core.records import Record
        record_objects = [Record(**r) for r in records]

        # Generate reconciliation
        lines = reconcile(record_objects, settings)
        for line in lines:
            emit(line)
        return 0
    except (OSError, ValueError) as exc:
        _log.warning("reconcile failed: %s", exc)
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files."""
    settings = load_settings()
    files = [Path(f) for f in args.files]

    total, rejected = validate(files, settings)
    emit(f"checked={total} rejected={rejected}")
    return 2 if rejected > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Handle --config option
    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config

    handler = args.handler
    return int(handler(args))
