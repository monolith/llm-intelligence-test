"""Totals over normalized records: report groupings and cross system reconciliation.

Every posting counts, refunds included.  Totals are exact ``Decimal`` sums;
rounding happens once, at display, through :func:`round_for_display`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_for_display(value: Decimal, decimals: int) -> Decimal:
    """Round a total half to even at ``decimals`` places, as ``docs/CONVENTIONS.md`` requires.

    A total that rounds to zero comes back as plain zero, never ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        return rounded.copy_abs()
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Sum postings per account code, as ``(code, name, total)`` with codes ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Sum postings per ``YYYY-MM`` month, as ``(month, total)`` with months ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return [(month, totals[month]) for month in sorted(totals)]


@dataclass(frozen=True)
class Mismatch:
    """One account and month where the systems that posted to it disagree."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return the account and month combinations whose spread exceeds ``tolerance``.

    Postings are totalled per account code, month and source system.  Only
    combinations at least two systems posted to are considered.  The spread is
    the largest system total minus the smallest, and a combination is reported
    when its spread is strictly greater than ``tolerance``.  Results are ordered
    by account code, then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        groups[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month) in sorted(groups):
        by_system = groups[(code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches
