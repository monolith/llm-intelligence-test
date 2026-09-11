"""Strict readers for the two kinds of value every export carries: dates and money.

The date *format* is not decided here.  Each system's reader knows how that
system writes a date and passes the format in; this module only applies it, and
applies it strictly, so a date that is not written exactly the way the system
writes dates is an error rather than a guess.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError


def read_date(raw: str, date_format: str, shown_as: str) -> date:
    """Read ``raw`` as a date written in ``date_format``.

    ``shown_as`` is how the format is described in the error, such as
    ``YYYY-MM-DD``.  Surrounding whitespace is ignored; anything else that does
    not round trip through ``date_format``, such as a missing leading zero, is
    rejected.
    """
    text = raw.strip()
    try:
        parsed = datetime.strptime(text, date_format).date()
    except ValueError:
        raise LedgerParseError(f"date {raw!r} is not a {shown_as} date") from None
    if parsed.strftime(date_format) != text:
        raise LedgerParseError(f"date {raw!r} is not a {shown_as} date")
    return parsed


def read_dollars(raw: str) -> Decimal:
    """Read ``raw`` as a decimal number of dollars."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise LedgerParseError(f"amount {raw!r} is not a number") from None
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value
