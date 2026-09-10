"""Totals for the ``report`` command.

Every posting counts toward a total, refunds included.  Totals are summed from
the unrounded amounts and rounded once, for display, half to even, as
``docs/CONVENTIONS.md`` requires.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even.

    A total that rounds to zero comes back as plain zero rather than ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        rounded = rounded.copy_abs()
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Return ``(account_code, account_name, total)`` for each code, codes ascending."""
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Return ``(month, total)`` for each ``YYYY-MM`` month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]
