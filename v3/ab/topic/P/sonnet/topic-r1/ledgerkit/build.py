"""Turn a source system's raw rows into normalized :class:`~ledgerkit.core.records.Record` values.

Each reader in :mod:`ledgerkit.parsers` hands back raw strings keyed by its own
column names; this module is where the differences between the three systems
get resolved into one shape:

* System B writes ``amount`` in integer cents, not dollars; A and C write
  ordinary decimal dollars.
* System C writes its date day first, ``DD/MM/YYYY``; A and B write ISO
  ``YYYY-MM-DD``.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.config import Settings
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_b

_ROW_FIELDS: dict[str, dict[str, str]] = {
    "A": {"id": "entry_id", "date": "posted_on", "code": "account", "description": "memo", "amount": "amount"},
    "B": {"id": "doc_no", "date": "value_date", "code": "acct", "description": "descr", "amount": "amount"},
    "C": {"id": "ref", "date": "txn_date", "code": "ledger_acct", "description": "narrative", "amount": "gross_amount"},
}


def _parse_date(system: str, text: str) -> date:
    if system == "C":
        return datetime.strptime(text.strip(), "%d/%m/%Y").date()
    return date.fromisoformat(text.strip())


def _parse_amount(system: str, text: str) -> Decimal:
    if system == "B":
        return system_b.to_major_units(text)
    return Decimal(text.strip())


def record_from_row(system: str, row: dict[str, str], settings: Settings) -> Record:
    """Build one :class:`Record` from a raw row that :mod:`ledgerkit.parsers` read for ``system``."""
    keys = _ROW_FIELDS[system]

    try:
        posted = _parse_date(system, row[keys["date"]])
    except ValueError as exc:
        raise LedgerParseError(f"bad date {row[keys['date']]!r} for system {system}") from exc

    try:
        amount = _parse_amount(system, row[keys["amount"]])
    except (InvalidOperation, LedgerParseError) as exc:
        raise LedgerParseError(f"bad amount {row[keys['amount']]!r} for system {system}") from exc

    code = row[keys["code"]]
    return Record(
        record_id=row[keys["id"]],
        source_system=system,
        date=posted,
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row[keys["description"]],
        amount=amount,
    )
