"""Reading dates and amounts out of raw export fields.

Each reader in :mod:`ledgerkit.parsers` knows how its own system writes a date
and an amount.  These are the strict parsers the readers share, so that
``ingest`` and ``validate`` accept and refuse exactly the same fields.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError

# Dollars with at most two decimal places.  ASCII digits only, and no exponent,
# underscore, NaN or Infinity, all of which ``Decimal`` would otherwise accept.
# More than two places is refused rather than rounded: rounding a posting on the
# way in would move money nobody asked to move.
_DOLLARS = re.compile(r"[+-]?[0-9]+(?:\.[0-9]{1,2})?")


def _format_label(date_format: str) -> str:
    return date_format.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")


def read_date(raw: str, date_format: str) -> date:
    """Read ``raw`` as a date written in ``date_format``, a ``strptime`` format."""
    try:
        return datetime.strptime(raw.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(f"date {raw!r} is not a {_format_label(date_format)} date") from exc


def read_dollars(raw: str) -> Decimal:
    """Read ``raw`` as dollars with at most two decimal places, such as ``-12.50``."""
    text = raw.strip()
    if _DOLLARS.fullmatch(text) is None:
        raise LedgerParseError(f"amount {raw!r} is not a number of dollars")
    return Decimal(text)
