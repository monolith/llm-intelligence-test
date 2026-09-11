"""Find the account and month combinations where the systems disagree.

Every posting counts, refunds included.  Postings are totalled by account code,
month and source system; a combination that at least two systems posted to is a
mismatch when its largest system total exceeds its smallest by more than the
tolerance.  The comparison uses the exact totals; rounding to cents happens only
when a line is laid out.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.core.values import round_half_even
from ledgerkit.parsers import SYSTEMS


@dataclass(frozen=True)
class Mismatch:
    """One account and month on which the systems that posted to it disagree."""

    account_code: str
    month: str
    totals: dict[str, Decimal]

    def spread(self) -> Decimal:
        """The largest system total minus the smallest."""
        return max(self.totals.values()) - min(self.totals.values())


def _cents(value: Decimal) -> str:
    return f"{round_half_even(value, 2):.2f}"


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every combination whose spread exceeds ``tolerance``, by account code and then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = groups.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in sorted(groups.items()):
        if len(totals) < 2:
            continue
        candidate = Mismatch(account_code=code, month=month, totals=totals)
        if candidate.spread() > tolerance:
            mismatches.append(candidate)
    return mismatches


def mismatch_line(mismatch: Mismatch) -> str:
    """Lay one mismatch out as a ``MISMATCH`` line; a system with no postings shows ``-``."""
    parts = [f"MISMATCH {mismatch.account_code} {mismatch.month} spread={_cents(mismatch.spread())}"]
    for system in SYSTEMS:
        total = mismatch.totals.get(system)
        parts.append(f"{system}=-" if total is None else f"{system}={_cents(total)}")
    return " ".join(parts)


def reconcile_lines(records: Iterable[Record], tolerance: Decimal) -> list[str]:
    """One line per mismatch, then the ``mismatches=<n>`` count line."""
    mismatches = find_mismatches(records, tolerance)
    return [mismatch_line(mismatch) for mismatch in mismatches] + [f"mismatches={len(mismatches)}"]
