"""Grouping and comparing postings across systems for the ``reconcile`` command."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination where the systems posting to it disagree."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    def spread(self) -> Decimal:
        """The largest system total minus the smallest, for this combination."""
        return max(self.totals.values()) - min(self.totals.values())


def find_mismatches(records: list[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return every account/month combination whose systems disagree by more than ``tolerance``.

    Every posting counts, refunds included. Only combinations that at least
    two systems posted to are considered. The result is ordered by account
    code, then month.
    """
    totals: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        totals[(record.account_code, record.month(), record.source_system)] += record.amount

    by_combo: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for (account_code, month, system), total in totals.items():
        by_combo[(account_code, month)][system] = total

    mismatches: list[Mismatch] = []
    for (account_code, month), per_system in by_combo.items():
        if len(per_system) < 2:
            continue
        spread = max(per_system.values()) - min(per_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code, month, dict(per_system)))

    mismatches.sort(key=lambda mismatch: (mismatch.account_code, mismatch.month))
    return mismatches


def format_mismatch(mismatch: Mismatch) -> str:
    """Render one mismatch as its ``MISMATCH ...`` output line."""
    parts = " ".join(
        f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
        for system in SYSTEMS
    )
    return f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread():.2f} {parts}"
