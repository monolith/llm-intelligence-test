"""Convert raw row dicts from each system into Record objects."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_b


def _parse_iso_date(date_str: str) -> date:
    """Parse ISO date YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise LedgerParseError(f"invalid ISO date: {date_str!r}") from exc


def _parse_decimal(amount_str: str) -> Decimal:
    """Parse decimal amount."""
    try:
        return Decimal(amount_str.strip())
    except Exception as exc:
        raise LedgerParseError(f"invalid amount: {amount_str!r}") from exc


def rows_to_records_a(
    rows: list[dict[str, str]], unknown_label: str
) -> list[Record]:
    """Convert System A rows to records."""
    records: list[Record] = []
    for row in rows:
        record_id = row["entry_id"]
        posted_on = _parse_iso_date(row["posted_on"])
        code = row["account"]
        description = row["memo"]
        amount = _parse_decimal(row["amount"])

        name = account_name(code, unknown_label)
        records.append(Record(
            record_id=record_id,
            source_system="A",
            date=posted_on,
            account_code=code,
            account_name=name,
            description=description,
            amount=amount,
        ))
    return records


def rows_to_records_b(
    rows: list[dict[str, str]], unknown_label: str
) -> list[Record]:
    """Convert System B rows to records."""
    records: list[Record] = []
    for row in rows:
        record_id = row["doc_no"]
        value_date = _parse_iso_date(row["value_date"])
        code = row["acct"]
        description = row["descr"]
        amount_cents = _parse_decimal(row["amount"])
        amount = system_b.to_major_units(row["amount"])

        name = account_name(code, unknown_label)
        records.append(Record(
            record_id=record_id,
            source_system="B",
            date=value_date,
            account_code=code,
            account_name=name,
            description=description,
            amount=amount,
        ))
    return records


def rows_to_records_c(
    rows: list[dict[str, str]], unknown_label: str
) -> list[Record]:
    """Convert System C rows to records."""
    records: list[Record] = []
    for row in rows:
        record_id = row["ref"]
        # Parse DD/MM/YYYY format
        txn_date_str = row["txn_date"].strip()
        try:
            txn_date = datetime.strptime(txn_date_str, "%d/%m/%Y").date()
        except ValueError as exc:
            raise LedgerParseError(f"invalid Calder date: {txn_date_str!r}") from exc

        code = row["ledger_acct"]
        description = row["narrative"]
        amount = _parse_decimal(row["gross_amount"])

        name = account_name(code, unknown_label)
        records.append(Record(
            record_id=record_id,
            source_system="C",
            date=txn_date,
            account_code=code,
            account_name=name,
            description=description,
            amount=amount,
        ))
    return records
