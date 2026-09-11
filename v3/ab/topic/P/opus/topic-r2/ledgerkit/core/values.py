"""Reading and showing single values: amounts and dates.

The readers decide which format a system writes; the functions here do the
reading once the format is known.  Amounts are :class:`~decimal.Decimal` from
the moment they are read, and :func:`round_half_even` is the one place a total
is rounded for display.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import LedgerParseError

_DECIMAL_PATTERN = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?")


def parse_decimal(raw: str, what: str) -> Decimal:
    """Read a plain decimal number such as ``239.55`` or ``-125.00``.

    Only digits, an optional sign and an optional decimal point are accepted, so
    ``NaN``, ``Infinity`` and ``1_000``, which :class:`~decimal.Decimal` would
    take, are refused.  ``what`` names the field in the error message.
    """
    text = raw.strip()
    if not _DECIMAL_PATTERN.fullmatch(text):
        raise LedgerParseError(f"{what} {raw!r} is not a number")
    return Decimal(text)


def parse_date(raw: str, date_format: str, what: str) -> date:
    """Read a date written in ``date_format``, a :func:`~datetime.datetime.strptime` format."""
    try:
        return datetime.strptime(raw.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(f"{what} {raw!r} is not a date in the form {date_format}") from exc


def round_half_even(value: Decimal, places: int) -> Decimal:
    """Round ``value`` to ``places`` decimal places, half to even.

    This is the display rounding ``docs/CONVENTIONS.md`` requires.  A total that
    rounds to zero comes back as plain zero rather than ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        return rounded.copy_abs()
    return rounded
