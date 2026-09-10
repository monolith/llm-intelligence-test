"""Convert raw system rows to normalized Record objects."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def system_a_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert an Ardent (A) row to a Record."""
    try:
        posted_date = date.fromisoformat(row["posted_on"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"cannot parse date: {row.get('posted_on')!r}") from exc

    try:
        amount = Decimal(row["amount"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"cannot parse amount: {row.get('amount')!r}") from exc

    code = row["account"].strip().upper()
    return Record(
        record_id=row["entry_id"].strip(),
        source_system="A",
        date=posted_date,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["memo"].strip(),
        amount=amount,
    )


def system_b_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a Borough (B) row to a Record."""
    try:
        value_date = date.fromisoformat(row["value_date"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"cannot parse date: {row.get('value_date')!r}") from exc

    try:
        cents = int(row["amount"].strip())
        amount = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"cannot parse amount: {row.get('amount')!r}") from exc

    code = row["acct"].strip().upper()
    return Record(
        record_id=row["doc_no"].strip(),
        source_system="B",
        date=value_date,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["descr"].strip(),
        amount=amount,
    )


def system_c_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a Calder (C) row to a Record."""
    try:
        dt = datetime.strptime(row["txn_date"].strip(), "%d/%m/%Y")
        txn_date = dt.date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"cannot parse date: {row.get('txn_date')!r}") from exc

    try:
        amount = Decimal(row["gross_amount"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"cannot parse amount: {row.get('gross_amount')!r}") from exc

    code = row["ledger_acct"].strip().upper()
    return Record(
        record_id=row["ref"].strip(),
        source_system="C",
        date=txn_date,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"].strip(),
        amount=amount,
    )
