"""Turning one raw field into a value.

Each system module says which format its own dates are written in and which of
these helpers reads its amounts; the helpers here only do the reading, and raise
:class:`~ledgerkit.core.records.LedgerParseError` when a field cannot be read.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError


def parse_date(raw: str, date_format: str) -> date:
    """Read ``raw`` as a date written in ``date_format`` (a ``strptime`` format)."""
    text = raw.strip()
    try:
        return datetime.strptime(text, date_format).date()
    except ValueError as exc:
        raise LedgerParseError(f"date {raw!r} is not a date in the form {date_format}") from exc


def parse_decimal(raw: str) -> Decimal:
    """Read ``raw`` as a finite decimal number.  Never goes through ``float``."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value
