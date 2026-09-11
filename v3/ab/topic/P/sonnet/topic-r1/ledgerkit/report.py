"""Grouping and totals for SPEC.md's ``report`` command.

Totals are summed as :class:`~decimal.Decimal` and left unrounded here; rounding
happens once, at display time, per ``docs/CONVENTIONS.md``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


@dataclass(frozen=True)
class AccountTotal:
    """One account code's running total."""

    account_code: str
    account_name: str
    total: Decimal


@dataclass(frozen=True)
class MonthTotal:
    """One month's running total."""

    month: str
    total: Decimal


def _postings(records: Iterable[Record], *, include_refunds: bool) -> Iterable[Record]:
    for record in records:
        if include_refunds or not record.is_refund():
            yield record


def totals_by_account(records: Iterable[Record], *, include_refunds: bool) -> list[AccountTotal]:
    """Total every account code that appears, ascending by code."""
    sums: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in _postings(records, include_refunds=include_refunds):
        sums[record.account_code] = sums.get(record.account_code, Decimal("0")) + record.amount
        names[record.account_code] = record.account_name
    return [AccountTotal(account_code=code, account_name=names[code], total=sums[code]) for code in sorted(sums)]


def totals_by_month(records: Iterable[Record], *, include_refunds: bool) -> list[MonthTotal]:
    """Total every month that appears, ascending."""
    sums: dict[str, Decimal] = {}
    for record in _postings(records, include_refunds=include_refunds):
        month = record.month()
        sums[month] = sums.get(month, Decimal("0")) + record.amount
    return [MonthTotal(month=month, total=sums[month]) for month in sorted(sums)]


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round ``value`` to ``decimals`` places, half to even, per docs/CONVENTIONS.md."""
    quantum = Decimal(1).scaleb(-decimals)
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)
