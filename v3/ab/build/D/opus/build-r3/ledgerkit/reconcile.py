"""Finding the account and month combinations where the systems disagree.

Postings are grouped by account code, month and source system.  Only the
account and month combinations that at least two systems posted to are
compared.  All postings count, refunds included.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

_CENTS = Decimal("0.01")


def format_money(value: Decimal) -> str:
    """Render ``value`` with two decimal places, rounding half to even."""
    rounded = value.quantize(_CENTS, rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        rounded = rounded.copy_abs()
    return f"{rounded:.2f}"


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination whose system totals are too far apart."""

    account_code: str
    month: str
    spread: Decimal
    totals: Mapping[str, Decimal]

    def to_line(self) -> str:
        """Render as ``MISMATCH <code> <month> spread=<n> A=<n> B=<n> C=<n>``."""
        parts = [f"MISMATCH {self.account_code} {self.month} spread={format_money(self.spread)}"]
        for system in SYSTEMS:
            total = self.totals.get(system)
            parts.append(f"{system}={format_money(total) if total is not None else '-'}")
        return " ".join(parts)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return the combinations whose spread is greater than ``tolerance``.

    The spread is the largest system total minus the smallest.  Results are
    ordered by account code and then month.
    """
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
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches
