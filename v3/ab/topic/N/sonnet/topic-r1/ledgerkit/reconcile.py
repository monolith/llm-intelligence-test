"""Find account/month combinations where the source systems disagree.

See ``SPEC.md``, section 3, for the command this implements.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record

SYSTEMS: tuple[str, ...] = ("A", "B", "C")


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination whose systems disagree by more than tolerance."""

    account_code: str
    month: str
    totals: dict[str, Decimal]
    spread: Decimal


def _totals_by_group(records: list[Record]) -> dict[tuple[str, str], dict[str, Decimal]]:
    grouped: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        by_system = grouped.setdefault(key, {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount
    return grouped


def find_mismatches(records: list[Record], *, tolerance: Decimal) -> list[Mismatch]:
    """Every account/month combination whose systems disagree by more than ``tolerance``.

    Only combinations at least two systems posted to are considered.  Ordered
    by account code, then month.
    """
    grouped = _totals_by_group(records)
    mismatches: list[Mismatch] = []
    for (account_code, month), totals in grouped.items():
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=account_code, month=month, totals=totals, spread=spread))
    mismatches.sort(key=lambda mismatch: (mismatch.account_code, mismatch.month))
    return mismatches
