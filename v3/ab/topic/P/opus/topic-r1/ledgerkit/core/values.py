"""Turning raw field text into values, and rounding values for display.

The parsing helpers here are building blocks.  Which one applies to which column
is decided by the reader for each system, in its own ``parse_date`` and
``parse_amount``; nothing here knows which system wrote a field.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError

_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")


def parse_iso_date(raw: str) -> date:
    """Read a zero padded ``YYYY-MM-DD`` date, and nothing looser."""
    text = raw.strip()
    if not _ISO_DATE.fullmatch(text):
        raise LedgerParseError(f"date {raw!r} is not written YYYY-MM-DD")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise LedgerParseError(f"date {raw!r} is not a real calendar date") from exc


def parse_decimal(raw: str) -> Decimal:
    """Read a finite decimal number exactly as written."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value


def round_half_even(value: Decimal, places: int) -> Decimal:
    """Round ``value`` to ``places`` decimal places, a half going to the even digit.

    This is the one rounding ``docs/CONVENTIONS.md`` allows, applied once, at the
    point of display.  A value that rounds to zero comes back as ``0``, never
    ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    return rounded if rounded else abs(rounded)
