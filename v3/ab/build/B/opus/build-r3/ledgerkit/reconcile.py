"""Find account and month combinations where the systems disagree.

Every posting counts, refunds included.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

MISSING = "-"


@dataclass(frozen=True)
class Mismatch:
    """One account and month whose system totals spread wider than the tolerance."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    @property
    def spread(self) -> Decimal:
        """Largest system total minus smallest."""
        return max(self.totals.values()) - min(self.totals.values())

    def line(self) -> str:
        """The ``MISMATCH`` output line for this combination."""
        parts = [f"MISMATCH {self.account_code} {self.month} spread={self.spread:.2f}"]
        for system in SYSTEMS:
            total = self.totals.get(system)
            parts.append(f"{system}={MISSING if total is None else f'{total:.2f}'}")
        return " ".join(parts)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Combinations posted to by two or more systems whose spread exceeds ``tolerance``.

    Ordered by account code, then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        totals = groups.setdefault((record.account_code, record.month()), {})
        totals[record.source_system] = totals.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in sorted(groups.items()):
        if len(totals) < 2:
            continue
        candidate = Mismatch(code, month, totals)
        if candidate.spread > tolerance:
            mismatches.append(candidate)
    return mismatches
