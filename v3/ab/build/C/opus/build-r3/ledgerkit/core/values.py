"""Turning raw field text into dates and amounts.

Readers hand back raw strings.  Each system module builds its own
``parse_date`` and ``parse_amount`` on the helpers here, supplying the format,
because each system writes those fields its own way and is the only place that
knows how.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError


def _describe(date_format: str) -> str:
    return date_format.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")


def parse_date(raw: str, date_format: str) -> date:
    """Read ``raw`` as a date written in ``date_format`` (a ``strptime`` format)."""
    try:
        return datetime.strptime(raw.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(f"date {raw!r} is not a date in the form {_describe(date_format)}") from exc


def parse_decimal(raw: str) -> Decimal:
    """Read ``raw`` as a finite decimal number."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a finite number")
    return value
