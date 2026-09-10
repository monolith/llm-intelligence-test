"""Where the three systems disagree on an account/month total.

Every posting counts toward reconciliation, refunds included - there is no
`keep_refunds` switch here, unlike `report`.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import NamedTuple

from ledgerkit.core.records import Record

MISSING = "-"
SYSTEMS: tuple[str, ...] = ("A", "B", "C")


class Mismatch(NamedTuple):
    """One account/month combination whose systems disagree by more than tolerance."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def find_mismatches(records: list[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account/month combinations where two or more systems posted and disagree.

    A combination is only considered when at least two systems posted to it.
    Its spread is its largest system total minus its smallest; a combination is
    reported when that spread is greater than ``tolerance``. The result is
    ordered by account code, then month.
    """
    grouped: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    for record in records:
        grouped[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in grouped.items():
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(totals)))

    mismatches.sort(key=lambda item: (item.account_code, item.month))
    return mismatches


def format_mismatch(mismatch: Mismatch) -> str:
    """Render one mismatch as the ``MISMATCH ...`` line SPEC.md shows."""
    system_parts = [
        f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}={MISSING}"
        for system in SYSTEMS
    ]
    return (
        f"MISMATCH {mismatch.account_code} {mismatch.month} "
        f"spread={mismatch.spread:.2f} " + " ".join(system_parts)
    )
