"""`reconcile` (SPEC.md): where the systems disagree.

Reads an already normalized records file, groups postings by account code,
month and source system, and reports the account/month combinations where the
systems that posted to it do not agree on the total.  All postings count,
refunds included; there is no ``--include-refunds`` here.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination whose systems disagree by more than tolerance."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    def spread(self) -> Decimal:
        """The largest system total minus the smallest, for this combination."""
        return max(self.totals.values()) - min(self.totals.values())


def find_mismatches(records: list[Record], tolerance: Decimal) -> list[Mismatch]:
    """Group ``records`` by account, month and system, and total each group.

    Only account/month combinations at least two systems posted to are
    considered.  Returns mismatches ordered by account code, then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for record in records:
        per_system = groups[(record.account_code, record.month())]
        per_system[record.source_system] = per_system.get(record.source_system, Decimal("0")) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in groups.items():
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=code, month=month, totals=totals))

    mismatches.sort(key=lambda mismatch: (mismatch.account_code, mismatch.month))
    return mismatches
