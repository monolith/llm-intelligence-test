"""Per-system conversion of raw export fields into typed values.

Each reader in :mod:`ledgerkit.parsers` hands back raw strings; this module is
where those strings become the :class:`datetime.date` and
:class:`decimal.Decimal` values a :class:`~ledgerkit.core.records.Record`
holds. Each function is keyed by source system letter because each system
writes dates and amounts differently.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError
from ledgerkit.parsers import system_b

DATE_FORMATS: dict[str, str] = {
    "A": "%Y-%m-%d",
    "B": "%Y-%m-%d",
    "C": "%d/%m/%Y",
}


def parse_date(system: str, raw: str) -> date:
    """Parse a date field the way ``system`` writes it."""
    fmt = DATE_FORMATS[system]
    try:
        return datetime.strptime(raw.strip(), fmt).date()
    except ValueError as exc:
        raise LedgerParseError(f"{raw!r} is not a date in system {system}'s format") from exc


def parse_amount(system: str, raw: str) -> Decimal:
    """Parse an amount field into dollars, the way ``system`` writes it.

    System B writes integer minor units and goes through
    :func:`ledgerkit.parsers.system_b.to_major_units`; A and C already write
    decimal dollars and are parsed directly.
    """
    if system == "B":
        return system_b.to_major_units(raw)
    text = raw.strip()
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"{raw!r} is not a decimal amount") from exc
