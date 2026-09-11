"""Account and month combinations where the systems disagree on the total.

Every posting counts, refunds included.  Only combinations that at least two
systems posted to are compared, and one is a mismatch when its largest system
total minus its smallest is greater than the tolerance.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.core.values import round_half_even
from ledgerkit.parsers import SYSTEMS


@dataclass(frozen=True)
class Mismatch:
    """One account and month the systems disagree about."""

    account_code: str
    month: str
    totals: Mapping[str, Decimal]
    spread: Decimal


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Every mismatch, ordered by account code and then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        by_system = groups.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in sorted(groups.items()):
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=code, month=month, totals=totals, spread=spread))
    return mismatches


def _money(value: Decimal) -> str:
    return f"{round_half_even(value, 2):.2f}"


def mismatch_line(mismatch: Mismatch) -> str:
    """One ``MISMATCH`` line; a system with no postings in the combination shows as ``-``."""
    systems = " ".join(
        f"{system}={_money(mismatch.totals[system])}" if system in mismatch.totals else f"{system}=-"
        for system in SYSTEMS
    )
    return f"MISMATCH {mismatch.account_code} {mismatch.month} spread={_money(mismatch.spread)} {systems}"


def reconcile_lines(records: Iterable[Record], tolerance: Decimal) -> list[str]:
    """One line per mismatch, then the ``mismatches=<n>`` count line."""
    mismatches = find_mismatches(records, tolerance)
    return [mismatch_line(mismatch) for mismatch in mismatches] + [f"mismatches={len(mismatches)}"]
