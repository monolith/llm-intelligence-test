"""Turning raw field text into dates and amounts.

Readers hand back raw strings.  The system modules decide which format a field is
in and call these helpers to do the conversion, so every system rejects a bad
value the same way: with a :class:`~ledgerkit.core.records.LedgerParseError`
that says what the text was.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError


def parse_date(raw: str, date_format: str) -> date:
    """Read ``raw`` as a date written in ``date_format`` (a ``strptime`` format)."""
    try:
        return datetime.strptime(raw.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(f"date {raw!r} is not in the format {date_format}") from exc


def parse_decimal(raw: str) -> Decimal:
    """Read ``raw`` as a finite decimal number."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value
