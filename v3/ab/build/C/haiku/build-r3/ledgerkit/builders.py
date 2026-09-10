"""Convert raw export rows into Record objects."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)


def build_record_from_a(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a raw System A row to a Record."""
    try:
        amount = Decimal(row["amount"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System A amount field invalid: {row.get('amount')!r}") from exc

    try:
        posted_on = datetime.strptime(row["posted_on"].strip(), "%Y-%m-%d").date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System A date field invalid: {row.get('posted_on')!r}") from exc

    account_code = row.get("account", "").strip().upper()
    return Record(
        record_id=row.get("entry_id", "").strip(),
        source_system="A",
        date=posted_on,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row.get("memo", "").strip(),
        amount=amount,
    )


def build_record_from_b(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a raw System B row to a Record."""
    try:
        amount = system_b.to_major_units(row["amount"])
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System B amount field invalid: {row.get('amount')!r}") from exc

    try:
        value_date = datetime.strptime(row["value_date"].strip(), "%Y-%m-%d").date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System B date field invalid: {row.get('value_date')!r}") from exc

    account_code = row.get("acct", "").strip().upper()
    return Record(
        record_id=row.get("doc_no", "").strip(),
        source_system="B",
        date=value_date,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row.get("descr", "").strip(),
        amount=amount,
    )


def build_record_from_c(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a raw System C row to a Record."""
    try:
        amount = Decimal(row["gross_amount"].strip())
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System C amount field invalid: {row.get('gross_amount')!r}") from exc

    try:
        txn_date = datetime.strptime(row["txn_date"].strip(), "%d/%m/%Y").date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"System C date field invalid: {row.get('txn_date')!r}") from exc

    account_code = row.get("ledger_acct", "").strip().upper()
    return Record(
        record_id=row.get("ref", "").strip(),
        source_system="C",
        date=txn_date,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row.get("narrative", "").strip(),
        amount=amount,
    )
