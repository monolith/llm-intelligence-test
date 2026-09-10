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
import re
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import load_settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import LedgerParseError, Record, RECORD_COLUMNS
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
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
        help="path to a TOML file with settings for this run (overrides LEDGERKIT_CONFIG env var)",
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
    ingest_parser.add_argument("--out", metavar="PATH", default="out/records.csv", help="output file path")
    ingest_parser.set_defaults(handler=cmd_ingest)

    report_parser = subparsers.add_parser("report", help="totals by account or by month")
    report_parser.add_argument("--by", choices=["account", "month"], required=True, help="grouping dimension")
    report_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file to read")
    report_parser.add_argument(
        "--include-refunds",
        action="store_true",
        help="include refunds in totals (note: spec was updated and refunds are now always included)",
    )
    report_parser.set_defaults(handler=cmd_report)

    reconcile_parser = subparsers.add_parser("reconcile", help="where systems disagree")
    reconcile_parser.add_argument("--records", metavar="PATH", default="out/records.csv", help="normalized file to read")
    reconcile_parser.add_argument("--tolerance", type=float, help="tolerance for considering systems as agreeing")
    reconcile_parser.set_defaults(handler=cmd_reconcile)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to validate")
    validate_parser.set_defaults(handler=cmd_validate)

    return parser


def _load_settings_with_config(args: argparse.Namespace) -> object:
    """Load settings, using --config flag if present."""
    if hasattr(args, "config") and args.config:
        old_config = os.environ.get("LEDGERKIT_CONFIG", "")
        os.environ["LEDGERKIT_CONFIG"] = args.config
        try:
            return load_settings()
        finally:
            if old_config:
                os.environ["LEDGERKIT_CONFIG"] = old_config
            else:
                os.environ.pop("LEDGERKIT_CONFIG", None)
    return load_settings()


def cmd_version(args: argparse.Namespace) -> int:
    """Print the package version and the settings file in force."""
    settings = _load_settings_with_config(args)
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


def _rows_to_records(system: str, raw_rows: list[dict[str, str]], settings: object) -> list[Record]:
    """Convert raw rows from a parser into Record objects."""
    records: list[Record] = []
    for row in raw_rows:
        try:
            if system == "A":
                record = Record(
                    record_id=row["entry_id"],
                    source_system="A",
                    date=datetime.fromisoformat(row["posted_on"]).date(),
                    account_code=row["account"],
                    account_name=account_name(row["account"], settings.unknown_account_label),
                    description=row["memo"],
                    amount=Decimal(row["amount"]),
                )
            elif system == "B":
                record = Record(
                    record_id=row["doc_no"],
                    source_system="B",
                    date=datetime.fromisoformat(row["value_date"]).date(),
                    account_code=row["acct"],
                    account_name=account_name(row["acct"], settings.unknown_account_label),
                    description=row["descr"],
                    amount=system_b.to_major_units(row["amount"]),
                )
            else:  # system == "C"
                date_str = row["txn_date"]
                date_parts = date_str.split("/")
                date_obj = datetime(
                    year=int(date_parts[2]),
                    month=int(date_parts[1]),
                    day=int(date_parts[0]),
                ).date()
                record = Record(
                    record_id=row["ref"],
                    source_system="C",
                    date=date_obj,
                    account_code=row["ledger_acct"],
                    account_name=account_name(row["ledger_acct"], settings.unknown_account_label),
                    description=row["narrative"],
                    amount=Decimal(row["gross_amount"]),
                )
            records.append(record)
        except (ValueError, KeyError) as exc:
            _log.error("cannot convert row: %s", exc)
    return records


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge exports into one normalized CSV file."""
    settings = _load_settings_with_config(args)
    all_records: list[Record] = []

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
            raw_rows = read_rows(path)
            records = _rows_to_records(system, raw_rows, settings)
            all_records.extend(records)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot ingest %s: %s", path, exc)
            return 1

    all_records.sort(key=lambda r: (r.date.isoformat(), r.source_system, r.record_id))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(join_record(list(RECORD_COLUMNS)) + "\n")
        for record in all_records:
            handle.write(join_record(record.to_row()) + "\n")

    emit(f"wrote={len(all_records)} to {out_path}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    """Print totals by account or by month."""
    settings = _load_settings_with_config(args)
    records_path = Path(args.records)

    try:
        records = _read_records_csv(records_path)
    except (OSError, ValueError) as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    if args.by == "account":
        return _report_by_account(records, settings)
    else:
        return _report_by_month(records, settings)


def _read_records_csv(path: Path) -> list[Record]:
    """Read a normalized records CSV file."""
    from ledgerkit.core.fields import split_record

    records: list[Record] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()

    if not lines:
        return records

    header = split_record(lines[0].rstrip("\r\n"))
    for line in lines[1:]:
        fields = split_record(line.rstrip("\r\n"))
        if len(fields) != len(header):
            continue

        row = dict(zip(header, fields, strict=True))
        try:
            record = Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=datetime.fromisoformat(row["date"]).date(),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            records.append(record)
        except (ValueError, KeyError) as exc:
            _log.error("cannot parse record: %s", exc)

    return records


def _report_by_account(records: list[Record], settings: object) -> int:
    """Print account totals."""
    totals: dict[tuple[str, str], Decimal] = {}

    for record in records:
        key = (record.account_code, record.account_name)
        totals[key] = totals.get(key, Decimal("0")) + record.amount

    emit("account_code;account_name;total")
    for (code, name) in sorted(totals.keys()):
        total = settings.format_amount(totals[(code, name)])
        emit(f"{code};{name};{total}")

    return 0


def _report_by_month(records: list[Record], settings: object) -> int:
    """Print monthly totals."""
    totals: dict[str, Decimal] = {}

    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal("0")) + record.amount

    emit("month;total")
    for month in sorted(totals.keys()):
        total = settings.format_amount(totals[month])
        emit(f"{month};{total}")

    return 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month combinations where systems disagree."""
    settings = _load_settings_with_config(args)
    records_path = Path(args.records)

    tolerance = args.tolerance
    if tolerance is None:
        tolerance = settings.tolerance
    else:
        tolerance = Decimal(str(tolerance))

    try:
        records = _read_records_csv(records_path)
    except (OSError, ValueError) as exc:
        _log.error("cannot read %s: %s", records_path, exc)
        return 1

    grouped: dict[tuple[str, str, str], Decimal] = {}
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        grouped[key] = grouped.get(key, Decimal("0")) + record.amount

    combinations: dict[tuple[str, str], dict[str, Decimal]] = {}
    for (code, month, system), total in grouped.items():
        key = (code, month)
        if key not in combinations:
            combinations[key] = {}
        combinations[key][system] = total

    mismatches = []
    for (code, month), systems in combinations.items():
        if len(systems) < 2:
            continue

        values = list(systems.values())
        spread = max(values) - min(values)
        if spread > tolerance:
            line = f"MISMATCH {code} {month}"
            for sys in ["A", "B", "C"]:
                if sys in systems:
                    amount_str = f"{systems[sys]:.2f}"
                    line += f" {sys}={amount_str}"
                else:
                    line += f" {sys}=-"
            mismatches.append((code, month, line))

    for _, _, line in sorted(mismatches):
        emit(line)

    emit(f"mismatches={len(mismatches)}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate export files."""
    settings = _load_settings_with_config(args)
    pattern = re.compile(settings.account_code_pattern)

    total_rows = 0
    rejected_rows = 0

    for file_path in args.files:
        path = Path(file_path)
        try:
            system = detect_system(path)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot read %s: %s", path, exc)
            return 2

        try:
            raw_rows = read_rows(path)
        except (LedgerParseError, OSError) as exc:
            _log.error("cannot read %s: %s", path, exc)
            return 2

        for row in raw_rows:
            total_rows += 1
            rejected = False

            if system == "A":
                date_str = row.get("posted_on", "")
                amount_str = row.get("amount", "")
                code = row.get("account", "")
                try:
                    datetime.fromisoformat(date_str)
                except ValueError:
                    _log.warning("%s: invalid date format", path.name)
                    rejected = True
            elif system == "B":
                date_str = row.get("value_date", "")
                amount_str = row.get("amount", "")
                code = row.get("acct", "")
                try:
                    datetime.fromisoformat(date_str)
                except ValueError:
                    _log.warning("%s: invalid date format", path.name)
                    rejected = True
            else:
                date_str = row.get("txn_date", "")
                amount_str = row.get("gross_amount", "")
                code = row.get("ledger_acct", "")
                try:
                    parts = date_str.split("/")
                    if len(parts) != 3:
                        raise ValueError("invalid date format")
                    datetime(year=int(parts[2]), month=int(parts[1]), day=int(parts[0]))
                except (ValueError, IndexError):
                    _log.warning("%s: invalid date format", path.name)
                    rejected = True

            try:
                Decimal(amount_str)
            except (ValueError, TypeError):
                _log.warning("%s: invalid amount", path.name)
                rejected = True

            if not pattern.match(code):
                _log.warning("%s: account code does not match pattern", path.name)
                rejected = True

            if rejected:
                rejected_rows += 1

    emit(f"checked={total_rows} rejected={rejected_rows}")
    return 2 if rejected_rows > 0 else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    handler = args.handler
    return int(handler(args))
