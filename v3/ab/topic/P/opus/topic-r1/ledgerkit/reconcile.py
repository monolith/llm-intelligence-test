"""Where the systems disagree about an account's total for a month.

Postings are totalled by account code, month and source system, refunds
included.  An account and month that at least two systems posted to is a
mismatch when its largest system total minus its smallest is more than the
tolerance.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.core.values import round_half_even
from ledgerkit.parsers import SYSTEMS

ABSENT = "-"


@dataclass(frozen=True)
class Mismatch:
    """One account and month on which the systems that posted to it disagree."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    @property
    def spread(self) -> Decimal:
        """The largest system total minus the smallest."""
        return max(self.totals.values()) - min(self.totals.values())


def system_totals(records: Iterable[Record]) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Exact totals per ``(account code, month)``, then per source system."""
    grouped: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        per_system = grouped.setdefault((record.account_code, record.month()), {})
        per_system[record.source_system] = (
            per_system.get(record.source_system, Decimal(0)) + record.amount
        )
    return grouped


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every multi-system account and month whose spread exceeds ``tolerance``.

    The result is ordered by account code and then month.
    """
    grouped = system_totals(records)
    mismatches: list[Mismatch] = []
    for account_code, month in sorted(grouped):
        per_system = grouped[(account_code, month)]
        if len(per_system) < 2:
            continue
        candidate = Mismatch(account_code=account_code, month=month, totals=dict(per_system))
        if candidate.spread > tolerance:
            mismatches.append(candidate)
    return mismatches


def format_mismatch(mismatch: Mismatch) -> str:
    """One ``MISMATCH`` line, every amount at two places, ``-`` for a silent system."""
    cells = [
        f"{system}={_money(mismatch.totals[system])}" if system in mismatch.totals else f"{system}={ABSENT}"
        for system in SYSTEMS
    ]
    return (
        f"MISMATCH {mismatch.account_code} {mismatch.month} "
        f"spread={_money(mismatch.spread)} " + " ".join(cells)
    )


def _money(value: Decimal) -> str:
    return f"{round_half_even(value, 2):.2f}"
