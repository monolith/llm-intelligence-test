"""Finding the account and month combinations where the systems disagree.

Every posting counts, refunds included.  Postings are grouped by account code,
month and source system; only combinations that at least two systems posted to
are compared, and a combination is a mismatch when its largest system total
exceeds its smallest by more than the tolerance.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

_CENTS = Decimal("0.01")


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination the systems disagree on."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    @property
    def spread(self) -> Decimal:
        """Largest system total minus smallest."""
        return max(self.totals.values()) - min(self.totals.values())


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every combination whose spread exceeds ``tolerance``, by account code then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        groups[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in sorted(groups.items()):
        if len(totals) < 2:
            continue
        candidate = Mismatch(account_code=code, month=month, totals=dict(totals))
        if candidate.spread > tolerance:
            mismatches.append(candidate)
    return mismatches


def _dollars(value: Decimal) -> str:
    return f"{value.quantize(_CENTS, rounding=ROUND_HALF_EVEN)}"


def format_mismatch(mismatch: Mismatch) -> str:
    """Lay out one mismatch as a ``MISMATCH`` line; a system with no postings shows ``-``."""
    letters = list(SYSTEMS) + sorted(set(mismatch.totals) - set(SYSTEMS))
    per_system = " ".join(
        f"{letter}={_dollars(mismatch.totals[letter])}" if letter in mismatch.totals else f"{letter}=-"
        for letter in letters
    )
    return f"MISMATCH {mismatch.account_code} {mismatch.month} spread={_dollars(mismatch.spread)} {per_system}"
