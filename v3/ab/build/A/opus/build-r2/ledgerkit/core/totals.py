"""Totals over normalized records: report groupings and reconciliation.

Everything here works on exact :class:`~decimal.Decimal` sums.  Rounding happens
once, at display time, through :func:`round_for_display`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_for_display(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even (docs/CONVENTIONS.md)."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded == 0:
        # A total that rounds to zero from below would otherwise print as "-0".
        rounded = abs(rounded)
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Return ``(account code, account name, total)`` per code, codes ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Return ``(YYYY-MM, total)`` per month, months ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return [(month, totals[month]) for month in sorted(totals)]


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination whose systems disagree."""

    account_code: str
    month: str
    spread: Decimal
    system_totals: dict[str, Decimal]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return the combinations posted to by two or more systems whose spread exceeds ``tolerance``.

    Every record counts, refunds included.  Results are ordered by account code
    and then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        groups[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(groups.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches
