"""Account and month combinations where the systems disagree.

Every posting counts, refunds included.  Postings are totalled per account code,
month and source system; a combination at least two systems posted to is a
mismatch when its largest system total exceeds its smallest by more than the
tolerance.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination the systems disagree on."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return the mismatches, ordered by account code and then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = groups.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for code, month in sorted(groups):
        by_system = groups[(code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches
