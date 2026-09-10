"""Totals for ``report`` and the cross-system comparison for ``reconcile``.

Everything here works on exact :class:`~decimal.Decimal` sums.  The only rounding
is :func:`round_total`, which the command line applies to a total just before it
is shown.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total half to even at ``decimals`` places, as docs/CONVENTIONS.md requires."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        # A small negative total would otherwise show as "-0".
        rounded = abs(rounded)
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """``(account code, account name, total)`` per code, codes ascending.

    The name is the one the records carry for that code.
    """
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """``(YYYY-MM, total)`` per month, months ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return sorted(totals.items())


@dataclass(frozen=True)
class Mismatch:
    """One account and month where the systems that posted to it disagree."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations whose system totals spread by more than ``tolerance``.

    Every posting counts, refunds included.  Only combinations that at least two
    systems posted to are compared.  The result is ordered by code, then month.
    """
    grouped: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        grouped[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(grouped.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches
