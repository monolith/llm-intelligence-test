"""Where the systems disagree.

Postings are grouped by account code, month and source system, and each group is
totalled exactly.  Only account and month combinations that at least two systems
posted to are compared.  The spread of a combination is its largest system total
minus its smallest, and a combination is a mismatch when its spread is greater
than the tolerance.  Every posting counts, refunds included.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

MISSING = "-"


@dataclass(frozen=True)
class Mismatch:
    """One account and month whose system totals are further apart than the tolerance."""

    account_code: str
    month: str
    totals: Mapping[str, Decimal]

    @property
    def spread(self) -> Decimal:
        """Largest system total minus smallest."""
        return max(self.totals.values()) - min(self.totals.values())

    def to_line(self) -> str:
        """Render as ``MISMATCH <code> <month> spread=... A=... B=... C=...``."""
        parts = [f"MISMATCH {self.account_code} {self.month} spread={self.spread:.2f}"]
        for system in SYSTEMS:
            total = self.totals.get(system)
            shown = MISSING if total is None else f"{total:.2f}"
            parts.append(f"{system}={shown}")
        return " ".join(parts)


def group_totals(records: Iterable[Record]) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Exact totals keyed by ``(account code, month)`` and then by system letter."""
    grouped: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = grouped.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = (
            by_system.get(record.source_system, Decimal(0)) + record.amount
        )
    return grouped


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every combination whose spread exceeds ``tolerance``, by account code then month."""
    found: list[Mismatch] = []
    for (code, month), totals in sorted(group_totals(records).items()):
        if len(totals) < 2:
            continue
        candidate = Mismatch(account_code=code, month=month, totals=totals)
        if candidate.spread > tolerance:
            found.append(candidate)
    return found


def reconcile_lines(records: Iterable[Record], tolerance: Decimal) -> list[str]:
    """One line per mismatch, then the ``mismatches=<n>`` count line."""
    mismatches = find_mismatches(records, tolerance)
    lines = [mismatch.to_line() for mismatch in mismatches]
    lines.append(f"mismatches={len(mismatches)}")
    return lines
