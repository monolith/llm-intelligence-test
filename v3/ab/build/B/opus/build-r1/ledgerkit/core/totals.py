"""Totals over normalized records, for ``report`` and ``reconcile``.

Nothing here rounds a posting.  Totals are exact sums of the postings that go
into them, and :func:`round_for_display` rounds a finished total once, half to
even, as ``docs/CONVENTIONS.md`` requires.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_for_display(value: Decimal, decimals: int) -> Decimal:
    """Round a finished total to ``decimals`` places, half to even."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    # A small negative total can round to -0, which nobody wants to read.
    return abs(rounded) if rounded == 0 else rounded


def totals_by_account(records: Iterable[Record]) -> dict[str, Decimal]:
    """Sum amounts per account code, codes ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
    return dict(sorted(totals.items()))


def totals_by_month(records: Iterable[Record]) -> dict[str, Decimal]:
    """Sum amounts per ``YYYY-MM`` month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return dict(sorted(totals.items()))


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination whose systems disagree."""

    account_code: str
    month: str
    spread: Decimal
    system_totals: dict[str, Decimal]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations posted by two or more systems whose spread exceeds ``tolerance``.

    Every posting counts, refunds included.  Results are ordered by account code
    and then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = groups.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    out: list[Mismatch] = []
    for (code, month), by_system in sorted(groups.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            out.append(Mismatch(code, month, spread, dict(sorted(by_system.items()))))
    return out
