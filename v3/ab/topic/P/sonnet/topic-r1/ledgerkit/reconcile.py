"""Where the systems disagree; the engine behind SPEC.md's ``reconcile`` command.

All postings count toward reconciliation, refunds included -- there is no
``include_refunds`` switch here the way there is for ``report``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from ledgerkit.core.records import Record

SYSTEMS_IN_ORDER: tuple[str, ...] = ("A", "B", "C")


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination whose systems do not agree on the total."""

    account_code: str
    month: str
    totals: dict[str, Decimal] = field(default_factory=dict)

    def spread(self) -> Decimal:
        """The largest system total minus the smallest, among the systems present."""
        values = list(self.totals.values())
        return max(values) - min(values)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account/month combinations at least two systems posted to, whose spread exceeds ``tolerance``."""
    sums: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        per_system = sums.setdefault(key, {})
        per_system[record.source_system] = per_system.get(record.source_system, Decimal("0")) + record.amount

    mismatches: list[Mismatch] = []
    for (account_code, month), totals in sums.items():
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=account_code, month=month, totals=totals))

    mismatches.sort(key=lambda mismatch: (mismatch.account_code, mismatch.month))
    return mismatches
