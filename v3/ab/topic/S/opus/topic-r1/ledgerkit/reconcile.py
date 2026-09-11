"""``reconcile``: account and month combinations where the systems disagree.

Every posting is totalled by account code, month and source system, refunds
included.  Only combinations that at least two systems posted to are compared.
The spread of a combination is its largest system total minus its smallest, and
a combination is a mismatch when that spread is greater than the tolerance.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import SOURCE_SYSTEMS, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

CENT = Decimal("0.01")
ABSENT = "-"


@dataclass(frozen=True)
class Mismatch:
    """One account and month whose system totals differ by more than the tolerance."""

    account_code: str
    month: str
    spread: Decimal
    totals: tuple[tuple[str, Decimal], ...]

    def describe(self) -> str:
        """The ``MISMATCH`` line for this combination, one amount per system."""
        by_system = dict(self.totals)
        shown = " ".join(
            f"{system}={_money(by_system[system]) if system in by_system else ABSENT}"
            for system in SOURCE_SYSTEMS
        )
        return f"MISMATCH {self.account_code} {self.month} spread={_money(self.spread)} {shown}"


def system_totals(records: Iterable[Record]) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Total the records by ``(account code, month)`` and then by source system."""
    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        group = totals.setdefault((record.account_code, record.month()), {})
        group[record.source_system] = group.get(record.source_system, Decimal(0)) + record.amount
    return totals


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every mismatched account and month, ordered by account code and then month."""
    mismatches: list[Mismatch] = []
    compared = 0
    for (code, month), by_system in sorted(system_totals(records).items()):
        if len(by_system) < 2:
            continue
        compared += 1
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, tuple(sorted(by_system.items()))))
    _log.info("compared %d account/month combination(s), %d mismatched", compared, len(mismatches))
    return mismatches


def _money(value: Decimal) -> str:
    return f"{value.quantize(CENT, rounding=ROUND_HALF_EVEN):.2f}"
