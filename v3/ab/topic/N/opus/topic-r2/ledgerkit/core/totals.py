"""Totals and reconciliation over normalized records.

Everything here works in exact :class:`~decimal.Decimal` dollars and returns
values rather than text.  Rounding for display happens once, in
:func:`round_total`, and only on a finished total.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination where the systems disagree."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def totals_by_account(records: Iterable[Record]) -> dict[str, tuple[str, Decimal]]:
    """Total ``records`` per account code, keeping the account name the file carries."""
    names: dict[str, str] = {}
    sums: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        names.setdefault(record.account_code, record.account_name)
        sums[record.account_code] += record.amount
    return {code: (names[code], sums[code]) for code in sorted(sums)}


def totals_by_month(records: Iterable[Record]) -> dict[str, Decimal]:
    """Total ``records`` per ``YYYY-MM`` month."""
    sums: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        sums[record.month()] += record.amount
    return {month: sums[month] for month in sorted(sums)}


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a finished total half to even at ``decimals`` places."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    # A small negative total that rounds to nothing should read 0, not -0.
    return rounded.copy_abs() if rounded.is_zero() else rounded


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations where two or more systems differ by more than ``tolerance``.

    Every posting counts, refunds included.  A combination only one system
    posted to is not compared.
    """
    sums: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        sums[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(sums.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches
