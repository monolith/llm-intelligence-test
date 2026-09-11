"""Totals by account or by month, computed from a normalized records file.

Refunds are counted in every total; there is no filtering here. ``report``'s
``--include-refunds`` flag is accepted on the command line for compatibility
with callers that already pass it, but it has nothing left to turn on.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from ledgerkit.log import get_logger

_log = get_logger(__name__)


def totals_by_account(rows: Iterable[dict[str, str]]) -> dict[str, tuple[str, Decimal]]:
    """Total amount per account code, paired with that code's account name."""
    names: dict[str, str] = {}
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        code = row["account_code"]
        names.setdefault(code, row["account_name"])
        totals[code] += Decimal(row["amount"])
    return {code: (names[code], totals[code]) for code in totals}


def totals_by_month(rows: Iterable[dict[str, str]]) -> dict[str, Decimal]:
    """Total amount per ``YYYY-MM`` month."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        month = row["date"][:7]
        totals[month] += Decimal(row["amount"])
    return dict(totals)
