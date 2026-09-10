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
import decimal
import os
import re
from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import count_data_lines, detect_system, read_records, system_a, system_b, system_c

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
    parser.add_argument("--config", type=str, metavar="PATH", help="read settings from PATH")

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
    ingest_parser.add_argument("--out", type=str, default="out/records.csv", metavar="PATH", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="print totals by account or month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="group by account or month")
    report_parser.add_argument("--records", type=str, default="out/records.csv", metavar="PATH", help="normalized records file")
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find where systems disagree")
    reconcile_parser.add_argument("--records", type=str, default="out/records.csv", metavar="PATH", help="normalized records file")
    reconcile_parser.add_argument("--tolerance", type=float, metavar="N", help="tolerance in dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check export files for malformed rows")
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
    """Merge export files into one normalized CSV."""
    from ledgerkit.core.fields import join_record
    from ledgerkit.core.normalize import normalize
    from ledgerkit.core.records import RECORD_COLUMNS

    settings = load_settings()
    all_records = []

    for name in args.files:
        path = Path(name)
        try:
            records = read_records(path, settings.unknown_account_label)
            all_records.extend(records)
        except (LedgerParseError, OSError, ValueError) as exc:
            _log.warning("cannot ingest %s: %s", path, exc)
            return 1

    normalized = normalize(all_records, keep_refunds=True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        f.write(",".join(RECORD_COLUMNS) + "\n")
        for record in normalized:
            row = record.to_row()
            f.write(join_record(row) + "\n")

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    from decimal import ROUND_HALF_EVEN

    from ledgerkit.core.fields import split_record

    settings = load_settings()
    records_path = Path(args.records)

    if not records_path.is_file():
        _log.warning("records file %s not found", records_path)
        return 1

    records = []
    with records_path.open("r", encoding="utf-8") as f:
        header = split_record(f.readline().strip())
        for line in f:
            values = split_record(line.rstrip("\n"))
            if len(values) == len(header):
                records.append(dict(zip(header, values)))

    if args.by == "account":
        by_account = {}
        for record in records:
            code = record["account_code"]
            if code not in by_account:
                by_account[code] = {
                    "name": record["account_name"],
                    "total": Decimal("0"),
                }
            by_account[code]["total"] += Decimal(record["amount"])

        emit("account_code;account_name;total")
        for code in sorted(by_account.keys()):
            info = by_account[code]
            total = info["total"].quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{code};{info['name']};{settings.format_amount(total)}")

    elif args.by == "month":
        by_month = {}
        for record in records:
            month = record["date"][:7]
            if month not in by_month:
                by_month[month] = Decimal("0")
            by_month[month] += Decimal(record["amount"])

        emit("month;total")
        for month in sorted(by_month.keys()):
            total = by_month[month].quantize(Decimal(10) ** -settings.decimals, rounding=ROUND_HALF_EVEN)
            emit(f"{month};{settings.format_amount(total)}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account/month combinations where systems disagree."""
    from collections import defaultdict

    from ledgerkit.core.fields import split_record

    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance
    records_path = Path(args.records)

    if not records_path.is_file():
        _log.warning("records file %s not found", records_path)
        return 1

    records = []
    with records_path.open("r", encoding="utf-8") as f:
        header = split_record(f.readline().strip())
        for line in f:
            values = split_record(line.rstrip("\n"))
            if len(values) == len(header):
                records.append(dict(zip(header, values)))

    by_key = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        key = (record["account_code"], record["date"][:7])
        system = record["source_system"]
        by_key[key][system] += Decimal(record["amount"])

    mismatches = []
    for (code, month), systems in sorted(by_key.items()):
        if len(systems) < 2:
            continue

        totals = {sys: amt for sys, amt in systems.items()}
        min_total = min(totals.values())
        max_total = max(totals.values())
        spread = max_total - min_total

        if spread > tolerance:
            spread_rounded = spread.quantize(Decimal("0.01"))
            a = totals.get("A")
            b = totals.get("B")
            c = totals.get("C")

            a_str = f"{a:.2f}" if a is not None else "-"
            b_str = f"{b:.2f}" if b is not None else "-"
            c_str = f"{c:.2f}" if c is not None else "-"

            line = f"MISMATCH {code} {month} spread={spread_rounded} A={a_str} B={b_str} C={c_str}"
            mismatches.append(line)

    for line in mismatches:
        emit(line)
    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files for malformed rows."""
    settings = load_settings()
    pattern = re.compile(settings.account_code_pattern)

    total_rows = 0
    rejected_rows = 0

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
        except LedgerParseError as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            return 2

        if system == "A":
            rows = system_a.read_rows(path)
            for row in rows:
                total_rows += 1
                if not _validate_row(row, pattern, path, total_rows):
                    rejected_rows += 1
        elif system == "B":
            rows = system_b.read_rows(path)
            for row in rows:
                total_rows += 1
                if not _validate_row(row, pattern, path, total_rows):
                    rejected_rows += 1
        elif system == "C":
            rows = system_c.read_rows(path)
            for row in rows:
                total_rows += 1
                if not _validate_row(row, pattern, path, total_rows):
                    rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def _validate_row(row: dict[str, str], pattern: re.Pattern[str], path: Path, line_num: int) -> bool:
    """Validate one row from an export. Return True if valid, False if rejected."""
    system = detect_system(path)
    field_count = len(system_a.COLUMNS) if system == "A" else (len(system_b.COLUMNS) if system == "B" else len(system_c.COLUMNS))

    if len(row) != field_count:
        _log.warning("%s line %d: expected %d fields, found %d", path.name, line_num, field_count, len(row))
        return False

    if system == "A":
        date_str = row.get("posted_on", "")
        amount_str = row.get("amount", "")
        code_str = row.get("account", "")
    elif system == "B":
        date_str = row.get("value_date", "")
        amount_str = row.get("amount", "")
        code_str = row.get("acct", "")
    else:
        date_str = row.get("txn_date", "")
        amount_str = row.get("gross_amount", "")
        code_str = row.get("ledger_acct", "")

    try:
        if system == "A" or system == "B":
            import datetime
            datetime.date.fromisoformat(date_str)
        else:
            day, month, year = date_str.split("/")
            import datetime
            datetime.date(int(year), int(month), int(day))
    except (ValueError, AttributeError):
        _log.warning("%s line %d: cannot parse date %r", path.name, line_num, date_str)
        return False

    try:
        from decimal import Decimal
        Decimal(amount_str)
        if system == "B":
            int(amount_str)
    except (ValueError, decimal.InvalidOperation):
        _log.warning("%s line %d: cannot parse amount %r", path.name, line_num, amount_str)
        return False

    if not pattern.match(code_str.strip()):
        _log.warning("%s line %d: account code %r does not match pattern", path.name, line_num, code_str)
        return False

    return True


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config

    handler = args.handler
    return int(handler(args))
