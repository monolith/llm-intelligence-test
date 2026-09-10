"""Find account and month combinations where the source systems disagree.

Every posting counts, refunds included.  Postings are totalled per account code,
month and source system.  A combination that at least two systems posted to is a
mismatch when its spread, the largest system total minus the smallest, is
greater than the tolerance.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination whose system totals disagree."""

    account_code: str
    month: str
    spread: Decimal
    totals: Mapping[str, Decimal]

    def to_line(self) -> str:
        """Render as ``MISMATCH <code> <month> spread=<n> A=<n> B=<n> C=<n>``.

        A system with no postings in the combination is written as ``-``.
        """
        parts = [f"MISMATCH {self.account_code} {self.month} spread={self.spread:.2f}"]
        for system in SYSTEMS:
            total = self.totals.get(system)
            parts.append(f"{system}=-" if total is None else f"{system}={total:.2f}")
        return " ".join(parts)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return the mismatched combinations, ordered by account code and then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = groups.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(groups.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=code, month=month, spread=spread, totals=by_system))
    return mismatches
