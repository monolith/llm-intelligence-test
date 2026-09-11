"""Reading amounts and dates out of raw export fields, and rounding totals.

Readers hand fields on as strings.  The per system ``parse_date`` and
``parse_amount`` functions in :mod:`ledgerkit.parsers` build on the helpers
here, so every system refuses a bad field the same way.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError


def decimal_from_text(raw: str) -> Decimal:
    """Read a decimal number, refusing anything that is not a finite number."""
    text = raw.strip()
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise LedgerParseError(f"amount {raw!r} is not a number") from None
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value


def date_from_text(raw: str, fmt: str) -> date:
    """Read a date written exactly the way ``fmt`` lays it out, zero padding included."""
    text = raw.strip()
    shape = fmt.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
    try:
        parsed = datetime.strptime(text, fmt).date()
    except ValueError:
        raise LedgerParseError(f"date {raw!r} is not a {shape} date") from None
    # strptime accepts unpadded fields such as 2026-1-3; the systems never write those.
    if parsed.strftime(fmt) != text:
        raise LedgerParseError(f"date {raw!r} is not a {shape} date")
    return parsed


def round_half_even(value: Decimal, places: int) -> Decimal:
    """Round ``value`` to ``places`` decimal places, a half going to the even neighbour.

    This is the rounding ``docs/CONVENTIONS.md`` fixes for report totals.  A
    result of zero comes back unsigned, so a total never shows as ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    return rounded.copy_abs() if rounded.is_zero() else rounded
