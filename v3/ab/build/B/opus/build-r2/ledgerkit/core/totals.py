"""Totals for the ``report`` command.

Totals are summed at full precision and rounded once, at display, half to even,
as ``docs/CONVENTIONS.md`` requires.  Every record counts, refunds included.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even.  A total that rounds to zero is never ``-0``."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    return rounded.copy_abs() if rounded.is_zero() else rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Return ``(account_code, account_name, total)`` per account code, codes ascending.

    The name is the one the records file carries for that code.
    """
    names: dict[str, str] = {}
    totals: dict[str, Decimal] = {}
    for record in records:
        names.setdefault(record.account_code, record.account_name)
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Return ``(month, total)`` per ``YYYY-MM`` month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]
