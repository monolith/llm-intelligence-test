"""Account and month combinations where the systems disagree, for ``python -m ledgerkit reconcile``.

Every posting counts, refunds included.  Only combinations that at least two
systems posted to are compared; one system on its own has nothing to disagree
with.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

CENT = Decimal("0.01")
MISSING = "-"


def _money(value: Decimal) -> str:
    return f"{value.quantize(CENT, rounding=ROUND_HALF_EVEN):.2f}"


@dataclass(frozen=True)
class Mismatch:
    """One account and month whose system totals are further apart than the tolerance."""

    account_code: str
    month: str
    spread: Decimal
    totals: tuple[tuple[str, Decimal | None], ...]

    def to_line(self) -> str:
        """Render as ``MISMATCH <code> <month> spread=<n> A=<n> B=<n> C=<n>``."""
        parts = ["MISMATCH", self.account_code, self.month, f"spread={_money(self.spread)}"]
        for system, total in self.totals:
            parts.append(f"{system}={MISSING if total is None else _money(total)}")
        return " ".join(parts)


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every account and month where two or more systems posted and their totals differ by more than ``tolerance``.

    The spread is the largest system total minus the smallest.  Results come
    back ordered by account code, then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = groups.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for account_code, month in sorted(groups):
        by_system = groups[(account_code, month)]
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(
                Mismatch(
                    account_code=account_code,
                    month=month,
                    spread=spread,
                    totals=tuple((system, by_system.get(system)) for system in SYSTEMS),
                )
            )
    return mismatches
