"""Build Records from raw rows returned by the three parsers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)


def _parse_date_iso(text: str) -> date:
    """Parse an ISO date in YYYY-MM-DD format."""
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise LedgerParseError(f"invalid ISO date {text!r}") from exc


def _parse_date_dmy(text: str) -> date:
    """Parse a date in DD/MM/YYYY format (System C)."""
    try:
        return datetime.strptime(text.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise LedgerParseError(f"invalid DD/MM/YYYY date {text!r}") from exc


def _parse_decimal(text: str) -> Decimal:
    """Parse a decimal amount."""
    try:
        return Decimal(text.strip()).quantize(Decimal("0.01"))
    except Exception as exc:
        raise LedgerParseError(f"invalid amount {text!r}") from exc


def record_from_system_a(row: dict[str, str], unknown_label: str) -> Record:
    """Build a Record from a System A raw row."""
    try:
        parsed_date = _parse_date_iso(row["posted_on"])
        amount = _parse_decimal(row["amount"])
    except LedgerParseError as exc:
        raise LedgerParseError(f"System A row {row['entry_id']}: {exc}") from exc

    return Record(
        record_id=row["entry_id"].strip(),
        source_system="A",
        date=parsed_date,
        account_code=row["account"].strip().upper(),
        account_name=account_name(row["account"], unknown_label),
        description=row["memo"],
        amount=amount,
    )


def record_from_system_b(row: dict[str, str], unknown_label: str) -> Record:
    """Build a Record from a System B raw row."""
    try:
        parsed_date = _parse_date_iso(row["value_date"])
        amount = system_b.to_major_units(row["amount"])
    except LedgerParseError as exc:
        raise LedgerParseError(f"System B row {row['doc_no']}: {exc}") from exc

    return Record(
        record_id=row["doc_no"].strip(),
        source_system="B",
        date=parsed_date,
        account_code=row["acct"].strip().upper(),
        account_name=account_name(row["acct"], unknown_label),
        description=row["descr"],
        amount=amount,
    )


def record_from_system_c(row: dict[str, str], unknown_label: str) -> Record:
    """Build a Record from a System C raw row."""
    try:
        parsed_date = _parse_date_dmy(row["txn_date"])
        amount = _parse_decimal(row["gross_amount"])
    except LedgerParseError as exc:
        raise LedgerParseError(f"System C row {row['ref']}: {exc}") from exc

    return Record(
        record_id=row["ref"].strip(),
        source_system="C",
        date=parsed_date,
        account_code=row["ledger_acct"].strip().upper(),
        account_name=account_name(row["ledger_acct"], unknown_label),
        description=row["narrative"],
        amount=amount,
    )


def read_records_from_file(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file and return Records."""
    from ledgerkit.parsers import detect_system, read_rows

    system = detect_system(path)
    raw_rows = read_rows(path)
    records: list[Record] = []

    for raw_row in raw_rows:
        try:
            if system == "A":
                record = record_from_system_a(raw_row, unknown_label)
            elif system == "B":
                record = record_from_system_b(raw_row, unknown_label)
            else:  # system == "C"
                record = record_from_system_c(raw_row, unknown_label)
            records.append(record)
        except LedgerParseError as exc:
            _log.warning("%s: %s", path.name, exc)
            continue

    return records
