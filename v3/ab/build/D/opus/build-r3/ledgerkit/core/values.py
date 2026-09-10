"""Turning raw field text into dates and dollar amounts.

The readers hand back raw strings.  These helpers are what the per-system code
uses to interpret them; each system module still decides which date format it
passes in, because each system is the only place that knows how it writes one.
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
        raise LedgerParseError(f"date {raw!r} is not in the format {date_format}") from exc


def parse_dollars(raw: str) -> Decimal:
    """Read ``raw`` as a decimal number of dollars."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value
