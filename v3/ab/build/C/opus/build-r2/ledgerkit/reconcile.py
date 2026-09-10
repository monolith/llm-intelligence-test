"""Where the systems disagree, for the ``reconcile`` command.

Postings are grouped by account code, month and source system, and each group is
totalled.  Only the account and month combinations that at least two systems
posted to are compared.  A combination's spread is its largest system total
minus its smallest, and it is a mismatch when that spread is greater than the
tolerance.  Every posting counts, refunds included.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS
from ledgerkit.report import round_half_even

MISSING = "-"


def _money(value: Decimal) -> str:
    return f"{round_half_even(value, 2):.2f}"


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination the systems disagree about."""

    account_code: str
    month: str
    totals: Mapping[str, Decimal]

    @property
    def spread(self) -> Decimal:
        """The largest system total minus the smallest."""
        return max(self.totals.values()) - min(self.totals.values())

    def to_line(self) -> str:
        """Render as ``MISMATCH <code> <month> spread=<n> A=<n> B=<n> C=<n>``."""
        parts = ["MISMATCH", self.account_code, self.month, f"spread={_money(self.spread)}"]
        for system in SYSTEMS:
            total = self.totals.get(system)
            parts.append(f"{system}={MISSING if total is None else _money(total)}")
        return " ".join(parts)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every combination whose spread exceeds ``tolerance``, by account code then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        totals = groups.setdefault((record.account_code, record.month()), {})
        totals[record.source_system] = totals.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in sorted(groups.items()):
        if len(totals) < 2:
            continue
        candidate = Mismatch(account_code=code, month=month, totals=totals)
        if candidate.spread > tolerance:
            mismatches.append(candidate)
    return mismatches
