"""Cross-system agreement checks for the ``reconcile`` command."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination where two or more systems disagree beyond tolerance."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    @property
    def spread(self) -> Decimal:
        """The largest system total minus the smallest, among systems present here."""
        values = list(self.totals.values())
        return max(values) - min(values)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations at least two systems posted to, that disagree beyond ``tolerance``."""
    grouped: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = grouped.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in grouped.items():
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=code, month=month, totals=dict(totals)))

    mismatches.sort(key=lambda mismatch: (mismatch.account_code, mismatch.month))
    return mismatches
