"""Turning raw field text into dates and amounts.

The readers hand back raw strings.  The helpers here do the conversions that are
the same whatever system wrote the field; each reader module decides which of
them applies to its own columns and with which date format.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError


def describe_date_format(date_format: str) -> str:
    """Spell a ``strptime`` format the way a person would, e.g. ``DD/MM/YYYY``."""
    return date_format.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")


def parse_date(raw: str, date_format: str) -> date:
    """Read ``raw`` as a date written in ``date_format``."""
    try:
        return datetime.strptime(raw.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(
            f"date {raw!r} is not a {describe_date_format(date_format)} date"
        ) from exc


def parse_dollars(raw: str) -> Decimal:
    """Read ``raw`` as a decimal number of dollars."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value
