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
import os
from collections.abc import Sequence
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.convert import system_a_to_records, system_b_to_records, system_c_to_records
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, RECORD_COLUMNS, sort_key
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
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="override settings file for this run (default from LEDGERKIT_CONFIG env var)",
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
    ingest_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to ingest")
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output file")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="input file")
    report_parser.add_argument(
        "--include-refunds", action="store_true", help="include refunds in totals (default: included)"
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="find account/month disagreements")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="input file")
    reconcile_parser.add_argument("--tolerance", type=float, help="tolerance in dollars")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="check files for malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="files to validate")
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
    """Merge export files into normalized CSV."""
    settings = load_settings()
    all_records = []

    for filepath in args.files:
        try:
            path = Path(filepath)
            raw_rows = read_rows(path)
            system = detect_system(path)

            if system == "A":
                records = system_a_to_records(raw_rows, settings.unknown_account_label)
            elif system == "B":
                records = system_b_to_records(raw_rows, settings.unknown_account_label)
            else:  # system == "C"
                records = system_c_to_records(raw_rows, settings.unknown_account_label)

            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot ingest %s: %s", filepath, exc)
            return 1

    # Normalize and sort records
    normalized = normalize(all_records, keep_refunds=True)
    normalized.sort(key=sort_key)

    # Write to output file
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or month."""
    settings = load_settings()

    # Read records from normalized file
    records_path = Path(args.records)
    try:
        with records_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or reader.fieldnames != list(RECORD_COLUMNS):
                _log.warning("invalid normalized file format")
                return 1

            records = []
            for row in reader:
                records.append(
                    _dict_to_record(row)
                )
    except (OSError, ValueError) as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        _report_by_account(records, settings)
    else:  # month
        _report_by_month(records, settings)

    return 0


def _dict_to_record(row: dict[str, str]):
    """Convert CSV row back to Record."""
    from datetime import date, datetime
    from decimal import Decimal

    return __import__("ledgerkit.core.records", fromlist=["Record"]).Record(
        record_id=row["record_id"],
        source_system=row["source_system"],
        date=datetime.fromisoformat(row["date"]).date(),
        account_code=row["account_code"],
        account_name=row["account_name"],
        description=row["description"],
        amount=Decimal(row["amount"]),
    )


def _report_by_account(records, settings):
    """Print totals by account."""
    from decimal import Decimal

    totals = {}
    account_names = {}

    for record in records:
        key = record.account_code
        if key not in totals:
            totals[key] = Decimal(0)
            account_names[key] = record.account_name
        totals[key] += record.amount

    emit("account_code;account_name;total")
    for code in sorted(totals.keys()):
        total = totals[code].quantize(Decimal(10) ** -settings.decimals)
        emit(f"{code};{account_names[code]};{settings.format_amount(total)}")


def _report_by_month(records, settings):
    """Print totals by month."""
    from decimal import Decimal

    totals = {}

    for record in records:
        month = record.month()
        if month not in totals:
            totals[month] = Decimal(0)
        totals[month] += record.amount

    emit("month;total")
    for month in sorted(totals.keys()):
        total = totals[month].quantize(Decimal(10) ** -settings.decimals)
        emit(f"{month};{settings.format_amount(total)}")


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Find account/month combinations where systems disagree."""
    from decimal import Decimal

    settings = load_settings()
    tolerance = Decimal(str(args.tolerance)) if args.tolerance is not None else settings.tolerance

    # Read records
    records_path = Path(args.records)
    try:
        with records_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = [_dict_to_record(row) for row in reader]
    except (OSError, ValueError) as exc:
        _log.warning("cannot read %s: %s", records_path, exc)
        return 1

    # Group by account, month, and system
    groups = {}
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        if key not in groups:
            groups[key] = Decimal(0)
        groups[key] += record.amount

    # Find mismatches
    mismatches = []
    combinations = set()
    for (account, month, system), total in groups.items():
        combinations.add((account, month))

    for account, month in combinations:
        systems_totals = {}
        for (acc, mon, sys), total in groups.items():
            if acc == account and mon == month:
                systems_totals[sys] = total

        if len(systems_totals) < 2:
            continue

        values = sorted(systems_totals.values())
        spread = values[-1] - values[0]

        if spread > tolerance:
            totals_str = []
            for sys in ["A", "B", "C"]:
                if sys in systems_totals:
                    val = systems_totals[sys].quantize(Decimal("0.01"))
                    totals_str.append(f"{sys}={val:.2f}")
                else:
                    totals_str.append(f"{sys}=-")

            spread_fmt = spread.quantize(Decimal("0.01"))
            mismatches.append((account, month, spread_fmt, " ".join(totals_str)))

    mismatches.sort(key=lambda x: (x[0], x[1]))

    for account, month, spread, totals_str in mismatches:
        emit(f"MISMATCH {account} {month} spread={spread:.2f} {totals_str}")

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Check files for malformed rows."""
    import re
    from datetime import date, datetime
    from decimal import Decimal

    settings = load_settings()
    total_checked = 0
    total_rejected = 0

    for filepath in args.files:
        try:
            path = Path(filepath)
            system = detect_system(path)
            raw_rows = read_rows(path)

            # Calculate actual line numbers accounting for headers and comments
            lines_text = path.read_text(encoding="utf-8").splitlines()
            if system == "A":
                data_start = next(i for i, l in enumerate(lines_text) if l and not l.startswith("#")) + 1
            elif system == "B":
                data_start = 2
            else:  # C
                data_start = 3

            for row_idx, raw in enumerate(raw_rows):
                # Find the actual line number
                if system == "A":
                    comment_count = sum(1 for i in range(row_idx + data_start) if i < len(lines_text) and lines_text[i].startswith("#"))
                    line_num = row_idx + data_start + comment_count
                else:
                    line_num = row_idx + data_start

                total_checked += 1

                # Validate date
                try:
                    if system == "A":
                        date_str = raw["posted_on"].strip()
                        datetime.fromisoformat(date_str)
                    elif system == "B":
                        date_str = raw["value_date"].strip()
                        datetime.fromisoformat(date_str)
                    else:  # C
                        date_str = raw["txn_date"].strip()
                        parts = date_str.split("/")
                        if len(parts) != 3:
                            raise ValueError()
                        date(int(parts[2]), int(parts[1]), int(parts[0]))
                except (ValueError, IndexError):
                    _log.warning("%s line %d: bad date", path.name, line_num)
                    total_rejected += 1
                    continue

                # Validate amount
                try:
                    if system == "A":
                        Decimal(raw["amount"].strip())
                    elif system == "B":
                        int(raw["amount"].strip())
                    else:  # C
                        Decimal(raw["gross_amount"].strip())
                except (ValueError, TypeError):
                    _log.warning("%s line %d: bad amount", path.name, line_num)
                    total_rejected += 1
                    continue

                # Validate account code
                if system == "A":
                    account_code = raw["account"].strip()
                elif system == "B":
                    account_code = raw["acct"].strip()
                else:  # C
                    account_code = raw["ledger_acct"].strip()

                if not re.match(settings.account_code_pattern, account_code):
                    _log.warning("%s line %d: bad account code", path.name, line_num)
                    total_rejected += 1
                    continue

        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", filepath, exc)
            return 2

    emit(f"checked={total_checked} rejected={total_rejected}")
    return 2 if total_rejected > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    # Handle --config flag
    if args.config:
        os.environ["LEDGERKIT_CONFIG"] = args.config

    handler = args.handler
    return int(handler(args))
