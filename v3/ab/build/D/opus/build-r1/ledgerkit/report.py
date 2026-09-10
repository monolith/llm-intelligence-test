"""Totals by account and by month, for the ``report`` command.

Totals are exact :class:`~decimal.Decimal` sums of every posting, refunds
included.  Nothing here rounds a total; :func:`round_total` does that once, at the
point of display.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even, as CONVENTIONS requires.

    A total that rounds to zero comes back as plain zero, never ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        return rounded.copy_abs()
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """``(account code, account name, total)`` for each account, codes ascending.

    The account name is the one the records file carries for that code.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """``(YYYY-MM, total)`` for each month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]
