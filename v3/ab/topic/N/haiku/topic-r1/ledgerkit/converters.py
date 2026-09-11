"""Convert raw reader rows to normalized Records."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name


def row_to_record_a(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System A row to a Record."""
    try:
        date_obj = datetime.fromisoformat(row["posted_on"]).date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System A invalid date: {row.get('posted_on')}") from exc

    try:
        amount = Decimal(row["amount"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System A invalid amount: {row.get('amount')}") from exc

    account_code = row["account"].strip()
    return Record(
        record_id=row["entry_id"].strip(),
        source_system="A",
        date=date_obj,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row["memo"],
        amount=amount,
    )


def row_to_record_b(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System B row to a Record."""
    try:
        date_obj = datetime.fromisoformat(row["value_date"]).date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System B invalid date: {row.get('value_date')}") from exc

    try:
        cents = int(row["amount"].strip())
        amount = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System B invalid amount: {row.get('amount')}") from exc

    account_code = row["acct"].strip()
    return Record(
        record_id=row["doc_no"].strip(),
        source_system="B",
        date=date_obj,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row["descr"],
        amount=amount,
    )


def row_to_record_c(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System C row to a Record."""
    try:
        date_str = row["txn_date"].strip()
        date_obj = datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System C invalid date: {row.get('txn_date')}") from exc

    try:
        amount = Decimal(row["gross_amount"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System C invalid amount: {row.get('gross_amount')}") from exc

    account_code = row["ledger_acct"].strip()
    return Record(
        record_id=row["ref"].strip(),
        source_system="C",
        date=date_obj,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row["narrative"],
        amount=amount,
    )
