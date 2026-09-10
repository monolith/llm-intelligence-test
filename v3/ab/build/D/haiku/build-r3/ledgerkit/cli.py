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
import csv
import re
from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.builders import build_record_a, build_record_b, build_record_c
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, RECORD_COLUMNS
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, read_rows, system_a, system_b, system_c

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
    parser.add_argument("--config", metavar="PATH", help="read settings from this file instead of the default")
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    version_parser = subparsers.add_parser("version", help="print the ledgerkit version")
    version_parser.set_defaults(handler=cmd_version)

    inspect_parser = subparsers.add_parser(
        "inspect", help="report which system wrote an export and how big it is"
    )
    inspect_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to look at")
    inspect_parser.set_defaults(handler=cmd_inspect)

    ingest_parser = subparsers.add_parser("ingest", help="merge exports into one normalized file")
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to ingest")
    ingest_parser.add_argument(
        "--out", metavar="PATH", default="out/records.csv", help="where to write the output"
    )
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument(
        "--by", choices=["account", "month"], required=True, help="which grouping to total by"
    )
    report_parser.add_argument(
        "--records", metavar="PATH", default="out/records.csv", help="the normalized file to read"
    )
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="include refunds in the totals"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser(
        "reconcile", help="where the systems disagree"
    )
    reconcile_parser.add_argument(
        "--records", metavar="PATH", default="out/records.csv", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=float, help="dollars tolerance for agreement"
    )
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
    """Merge multiple exports into one normalized CSV file."""
    settings = load_settings()
    all_records = []

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 1

        if system == "A":
            builder = build_record_a
        elif system == "B":
            builder = build_record_b
        else:
            builder = build_record_c

        for raw_row in raw_rows:
            try:
                record = builder(raw_row, settings.unknown_account_label)
                all_records.append(record)
            except LedgerParseError as exc:
                _log.warning("cannot parse row from %s: %s", path, exc)
                return 1

    records = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())

    emit(f"wrote={len(records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.exists():
        _log.warning("file %s not found", records_path)
        return 1

    records = []
    try:
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(RECORD_COLUMNS):
                _log.warning("invalid header in %s", records_path)
                return 1
            for row in reader:
                if row is None:
                    continue
                record_date = date.fromisoformat(row["date"])
                amount = Decimal(row["amount"])
                if amount < 0 and not args.include_refunds:
                    continue
                record = type("Record", (), {
                    "account_code": row["account_code"],
                    "account_name": row["account_name"],
                    "amount": amount,
                    "date": record_date,
                })()
                records.append(record)
    except OSError as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        totals = defaultdict(lambda: Decimal(0))
        names = {}
        for r in records:
            totals[r.account_code] += r.amount
            names[r.account_code] = r.account_name

        emit("account_code,account_name,total")
        for code in sorted(totals.keys()):
            total = totals[code].quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{code},{names[code]},{settings.format_amount(total)}")
    else:
        totals = defaultdict(lambda: Decimal(0))
        for r in records:
            month = f"{r.date.year:04d}-{r.date.month:02d}"
            totals[month] += r.amount

        emit("month,total")
        for month in sorted(totals.keys()):
            total = totals[month].quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{month},{settings.format_amount(total)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report mismatches between systems for account and month combinations."""
    settings = load_settings()
    if args.tolerance is not None:
        tolerance = Decimal(str(args.tolerance))
    else:
        tolerance = settings.tolerance

    records_path = Path(args.records)

    if not records_path.exists():
        _log.warning("file %s not found", records_path)
        return 1

    records = []
    try:
        with records_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != list(RECORD_COLUMNS):
                _log.warning("invalid header in %s", records_path)
                return 1
            for row in reader:
                if row is None:
                    continue
                from datetime import date as date_class
                record_date = date_class.fromisoformat(row["date"])
                amount = Decimal(row["amount"])
                month = f"{record_date.year:04d}-{record_date.month:02d}"
                record = type("Record", (), {
                    "account_code": row["account_code"],
                    "source_system": row["source_system"],
                    "amount": amount,
                    "month": month,
                })()
                records.append(record)
    except OSError as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    combinations = defaultdict(lambda: defaultdict(lambda: Decimal(0)))
    system_seen = defaultdict(set)

    for r in records:
        key = (r.account_code, r.month)
        combinations[key][r.source_system] += r.amount
        system_seen[key].add(r.source_system)

    mismatches = []
    for (account_code, month), systems_totals in combinations.items():
        if len(systems_totals) < 2:
            continue

        totals = {sys: systems_totals.get(sys, Decimal(0)) for sys in ["A", "B", "C"]}
        values = [totals[sys] for sys in ["A", "B", "C"] if sys in systems_totals]

        if len(values) < 2:
            continue

        min_total = min(values)
        max_total = max(values)
        spread = max_total - min_total

        if spread > tolerance:
            parts = [f"MISMATCH {account_code} {month}"]
            parts.append(f"spread={spread:.2f}")
            for sys in ["A", "B", "C"]:
                if sys in systems_totals:
                    parts.append(f"{sys}={systems_totals[sys]:.2f}")
                else:
                    parts.append(f"{sys}=-")
            mismatches.append(" ".join(parts))

    for mismatch in sorted(mismatches):
        emit(mismatch)

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    account_pattern = re.compile(settings.account_code_pattern)
    total_rows = 0
    rejected_rows = 0

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        try:
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            return 2

        if system == "A":
            builder = build_record_a
        elif system == "B":
            builder = build_record_b
        else:
            builder = build_record_c

        for i, raw_row in enumerate(raw_rows, start=2):
            total_rows += 1
            try:
                record = builder(raw_row, settings.unknown_account_label)
                if not account_pattern.match(record.account_code):
                    _log.warning(
                        "%s line %d: account code %r does not match pattern %r",
                        path.name,
                        i,
                        record.account_code,
                        settings.account_code_pattern,
                    )
                    rejected_rows += 1
            except LedgerParseError as exc:
                _log.warning("%s line %d: %s", path.name, i, exc)
                rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    import os
    from ledgerkit.config import CONFIG_ENV_VAR

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config

    handler = args.handler
    return int(handler(args))
