"""Turn one raw row from a system reader into a normalized :class:`Record`.

Readers hand back raw strings keyed by their own system's column names; this
module is the code that knows which system it is holding and interprets those
strings into a :class:`Record` -- a date, a decimal amount, and an account name
looked up from :mod:`ledgerkit.mapping`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_b


def _parse_iso_date(raw: str, field: str) -> date:
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise LedgerParseError(f"{field} {raw!r} is not an ISO date") from exc


def _parse_day_first_date(raw: str, field: str) -> date:
    text = raw.strip()
    parts = text.split("/")
    if len(parts) != 3:
        raise LedgerParseError(f"{field} {raw!r} is not a dd/mm/yyyy date")
    day_str, month_str, year_str = parts
    try:
        return date(int(year_str), int(month_str), int(day_str))
    except ValueError as exc:
        raise LedgerParseError(f"{field} {raw!r} is not a dd/mm/yyyy date") from exc


def _parse_decimal(raw: str, field: str) -> Decimal:
    try:
        return Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"{field} {raw!r} is not a number") from exc


def record_from_row(system: str, row: dict[str, str], *, unknown_label: str) -> Record:
    """Interpret one raw row from ``system`` as a :class:`Record`.

    ``row`` is a dict keyed by that system's own column names, exactly as
    ``system_a``/``system_b``/``system_c``'s ``read_rows`` hand it back.
    """
    if system == "A":
        record_id = row["entry_id"]
        posted = _parse_iso_date(row["posted_on"], "posted_on")
        code = row["account"]
        description = row["memo"]
        amount = _parse_decimal(row["amount"], "amount")
    elif system == "B":
        record_id = row["doc_no"]
        posted = _parse_iso_date(row["value_date"], "value_date")
        code = row["acct"]
        description = row["descr"]
        amount = system_b.to_major_units(row["amount"])
    elif system == "C":
        record_id = row["ref"]
        posted = _parse_day_first_date(row["txn_date"], "txn_date")
        code = row["ledger_acct"]
        description = row["narrative"]
        amount = _parse_decimal(row["gross_amount"], "gross_amount")
    else:
        raise LedgerParseError(f"unknown system {system!r}")

    return Record(
        record_id=record_id,
        source_system=system,
        date=posted,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=description,
        amount=amount,
    )
