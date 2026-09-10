"""Build Record objects from raw rows returned by parsers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name


def build_record_a(raw: dict[str, str], unknown_label: str) -> Record:
    """Convert a System A (Ardent) raw row to a Record."""
    try:
        posted_on = datetime.fromisoformat(raw["posted_on"]).date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"invalid date: {raw.get('posted_on')!r}") from exc

    try:
        amount = Decimal(raw["amount"]).quantize(Decimal("0.01"))
    except (ValueError, KeyError, Exception) as exc:
        raise LedgerParseError(f"invalid amount: {raw.get('amount')!r}") from exc

    code = raw.get("account", "").strip().upper()
    return Record(
        record_id=raw.get("entry_id", ""),
        source_system="A",
        date=posted_on,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=raw.get("memo", ""),
        amount=amount,
    )


def build_record_b(raw: dict[str, str], unknown_label: str) -> Record:
    """Convert a System B (Borough) raw row to a Record."""
    try:
        value_date = datetime.fromisoformat(raw["value_date"]).date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"invalid date: {raw.get('value_date')!r}") from exc

    try:
        cents = int(raw["amount"])
        amount = (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))
    except (ValueError, KeyError, Exception) as exc:
        raise LedgerParseError(f"invalid amount: {raw.get('amount')!r}") from exc

    code = raw.get("acct", "").strip().upper()
    return Record(
        record_id=raw.get("doc_no", ""),
        source_system="B",
        date=value_date,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=raw.get("descr", ""),
        amount=amount,
    )


def build_record_c(raw: dict[str, str], unknown_label: str) -> Record:
    """Convert a System C (Calder) raw row to a Record."""
    try:
        date_str = raw["txn_date"].strip()
        posted_on = datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"invalid date: {raw.get('txn_date')!r}") from exc

    try:
        amount = Decimal(raw["gross_amount"]).quantize(Decimal("0.01"))
    except (ValueError, KeyError, Exception) as exc:
        raise LedgerParseError(f"invalid amount: {raw.get('gross_amount')!r}") from exc

    code = raw.get("ledger_acct", "").strip().upper()
    return Record(
        record_id=raw.get("ref", ""),
        source_system="C",
        date=posted_on,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=raw.get("narrative", ""),
        amount=amount,
    )
