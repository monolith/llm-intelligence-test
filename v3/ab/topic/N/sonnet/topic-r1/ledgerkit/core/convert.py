"""Raw export rows to normalized :class:`Record` values.

Readers in :mod:`ledgerkit.parsers` hand back raw strings keyed by each
system's own column names and do not interpret them.  This module is the
interpreter: it knows which column means what in each system, how each system
writes a date, and that Borough's amount column is minor units while Ardent's
and Calder's are already dollars.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_b


def _parse_iso_date(raw: str, system: str) -> date:
    try:
        return date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise LedgerParseError(f"system {system}: {raw!r} is not an ISO date") from exc


def _parse_day_first_date(raw: str) -> date:
    text = raw.strip()
    parts = text.split("/")
    if len(parts) != 3:
        raise LedgerParseError(f"system C: {raw!r} is not a dd/mm/yyyy date")
    day_str, month_str, year_str = parts
    try:
        return date(int(year_str), int(month_str), int(day_str))
    except ValueError as exc:
        raise LedgerParseError(f"system C: {raw!r} is not a dd/mm/yyyy date") from exc


def _parse_decimal(raw: str, label: str) -> Decimal:
    try:
        return Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"{label}: {raw!r} is not a number") from exc


def from_system_a(row: dict[str, str], unknown_label: str) -> Record:
    """Turn one raw Ardent row into a :class:`Record`."""
    code = row["account"]
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=_parse_iso_date(row["posted_on"], "A"),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["memo"],
        amount=_parse_decimal(row["amount"], "system A amount"),
    )


def from_system_b(row: dict[str, str], unknown_label: str) -> Record:
    """Turn one raw Borough row into a :class:`Record`."""
    code = row["acct"]
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=_parse_iso_date(row["value_date"], "B"),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["descr"],
        amount=system_b.to_major_units(row["amount"]),
    )


def from_system_c(row: dict[str, str], unknown_label: str) -> Record:
    """Turn one raw Calder row into a :class:`Record`."""
    code = row["ledger_acct"]
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=_parse_day_first_date(row["txn_date"]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"],
        amount=_parse_decimal(row["gross_amount"], "system C amount"),
    )


CONVERTERS = {"A": from_system_a, "B": from_system_b, "C": from_system_c}


def to_record(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Turn one raw row from ``system`` into a :class:`Record`."""
    return CONVERTERS[system](row, unknown_label)
