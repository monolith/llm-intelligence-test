"""Finding the account and month combinations where the systems disagree."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record


@dataclass(frozen=True)
class Mismatch:
    """One account and month whose system totals are further apart than the tolerance."""

    account_code: str
    month: str
    totals: Mapping[str, Decimal]
    spread: Decimal


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return every mismatch, ordered by account code and then month.

    Records are totalled per account code, month and source system, refunds
    included.  Only combinations that at least two systems posted to are
    compared.  The spread is the largest system total minus the smallest, and a
    combination is a mismatch when its spread is greater than ``tolerance``.
    """
    grouped: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = grouped.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(grouped.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, dict(by_system), spread))
    return mismatches
