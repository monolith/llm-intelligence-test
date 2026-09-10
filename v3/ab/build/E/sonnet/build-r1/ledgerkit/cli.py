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
import re
from collections.abc import Callable, Sequence
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import __version__
from ledgerkit.config import CONFIG_ENV_VAR, Settings, load_settings
from ledgerkit.core import fields
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import count_data_lines, detect_system, read_rows, system_a, system_b, system_c

_log = get_logger(__name__)

PROGRAM_NAME = "ledgerkit"
DEFAULT_RECORDS_PATH = "out/records.csv"

COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}

DATE_FIELD_BY_SYSTEM: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
AMOUNT_FIELD_BY_SYSTEM: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}
ACCOUNT_FIELD_BY_SYSTEM: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}

DATE_PARSERS: dict[str, Callable[[str], date]] = {
    "A": date.fromisoformat,
    "B": date.fromisoformat,
    "C": lambda text: datetime.strptime(text, "%d/%m/%Y").date(),
}

SPLIT_BY_SYSTEM: dict[str, Callable[[str], list[str]]] = {
    "A": fields.split_record,
    "B": lambda line: line.split(","),
    "C": lambda line: line.split(","),
}

ITER_LINES_BY_SYSTEM: dict[str, Callable[[Path], list[tuple[int, str]]]] = {
    "A": system_a.iter_data_lines,
    "B": system_b.iter_data_lines,
    "C": system_c.iter_data_lines,
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
        "--config", metavar="PATH", help="read settings from PATH instead of the usual place"
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
    ingest_parser.add_argument("--out", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="where to write")
    ingest_parser.set_defaults(handler=cmd_ingest)

    validate_parser = subparsers.add_parser("validate", help="reject malformed rows")
    validate_parser.add_argument("files", nargs="+", metavar="FILE", help="export files to check")
    validate_parser.set_defaults(handler=cmd_validate)

    reconcile_parser = subparsers.add_parser("reconcile", help="report account/month totals systems disagree on")
    reconcile_parser.add_argument(
        "--records", default=DEFAULT_RECORDS_PATH, metavar="PATH", help="the normalized file to read"
    )
    reconcile_parser.add_argument(
        "--tolerance", type=Decimal, default=None, metavar="N", help="dollars of allowed spread"
    )
    reconcile_parser.set_defaults(handler=cmd_reconcile)

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


def _record_from_row(system: str, row: dict[str, str], settings: Settings) -> Record:
    """Turn one raw row from a reader into a normalized :class:`Record`."""
    account_code = row[ACCOUNT_FIELD_BY_SYSTEM[system]].strip()
    if system == "A":
        record_id, amount = row["entry_id"], Decimal(row["amount"].strip())
        source_date, description = date.fromisoformat(row["posted_on"].strip()), row["memo"]
    elif system == "B":
        record_id, amount = row["doc_no"], system_b.to_major_units(row["amount"])
        source_date, description = date.fromisoformat(row["value_date"].strip()), row["descr"]
    else:
        record_id, amount = row["ref"], Decimal(row["gross_amount"].strip())
        source_date, description = DATE_PARSERS["C"](row["txn_date"].strip()), row["narrative"]
    return Record(
        record_id=record_id,
        source_system=system,
        date=source_date,
        account_code=account_code,
        account_name=account_name(account_code, settings.unknown_account_label),
        description=description,
        amount=amount,
    )


def _read_export_records(path: Path, settings: Settings) -> list[Record]:
    """Detect the system that wrote ``path`` and read it as normalized records."""
    system = detect_system(path)
    return [_record_from_row(system, row, settings) for row in read_rows(path)]


def _write_records_csv(records: list[Record], path: Path) -> None:
    """Write ``records`` to ``path`` as the normalized CSV format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())


def _read_records_csv(path: Path) -> list[Record]:
    """Read a normalized CSV file back into :class:`Record` values."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            for row in csv.DictReader(handle)
        ]


def cmd_ingest(args: argparse.Namespace) -> int:
    """Merge any number of export files into one normalized CSV."""
    settings = load_settings()
    records: list[Record] = []
    for name in args.files:
        records.extend(_read_export_records(Path(name), settings))
    normalized = normalize(records, keep_refunds=True)
    out_path = Path(args.out)
    _write_records_csv(normalized, out_path)
    emit(f"wrote={len(normalized)} to {out_path}")
    return 0


def _row_problem(values: list[str], system: str, settings: Settings) -> str | None:
    """Return why a validate row is bad, or ``None`` when it is fine."""
    columns = COLUMNS_BY_SYSTEM[system]
    if len(values) != len(columns):
        return f"expected {len(columns)} fields, found {len(values)}"
    row = dict(zip(columns, values, strict=True))

    date_text = row[DATE_FIELD_BY_SYSTEM[system]].strip()
    try:
        DATE_PARSERS[system](date_text)
    except ValueError:
        return f"invalid date {date_text!r}"

    amount_text = row[AMOUNT_FIELD_BY_SYSTEM[system]].strip()
    try:
        Decimal(amount_text)
    except InvalidOperation:
        return f"invalid amount {amount_text!r}"

    account_code = row[ACCOUNT_FIELD_BY_SYSTEM[system]].strip()
    if re.match(settings.account_code_pattern, account_code) is None:
        return f"invalid account code {account_code!r}"

    return None


def cmd_validate(args: argparse.Namespace) -> int:
    """Check export files row by row without writing anything."""
    settings = load_settings()
    checked = 0
    rejected = 0
    unreadable = False

    for name in args.files:
        path = Path(name)
        try:
            system = detect_system(path)
            lines = ITER_LINES_BY_SYSTEM[system](path)
        except (LedgerParseError, OSError) as exc:
            _log.warning("cannot validate %s: %s", path, exc)
            unreadable = True
            continue

        split = SPLIT_BY_SYSTEM[system]
        for number, line in lines:
            checked += 1
            problem = _row_problem(split(line), system, settings)
            if problem is not None:
                _log.warning("%s line %d: %s", path.name, number, problem)
                rejected += 1

    emit(f"checked={checked} rejected={rejected}")
    return 2 if (rejected or unreadable) else 0


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report account/month combinations where the systems disagree."""
    settings = load_settings()
    tolerance = args.tolerance if args.tolerance is not None else settings.tolerance
    records = _read_records_csv(Path(args.records))

    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = totals.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal("0")) + record.amount

    mismatches = 0
    for account_code, month in sorted(totals):
        by_system = totals[(account_code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread <= tolerance:
            continue
        mismatches += 1
        parts = " ".join(
            f"{system}={by_system[system]:.2f}" if system in by_system else f"{system}=-"
            for system in ("A", "B", "C")
        )
        emit(f"MISMATCH {account_code} {month} spread={spread:.2f} {parts}")

    emit(f"mismatches={mismatches}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.config:
        os.environ[CONFIG_ENV_VAR] = args.config
    handler = args.handler
    return int(handler(args))
