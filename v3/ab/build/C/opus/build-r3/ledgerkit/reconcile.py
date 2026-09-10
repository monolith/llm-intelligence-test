"""Where the systems disagree, for the ``reconcile`` command.

Every posting is grouped by account code, month and source system, refunds
included, and each group is totalled.  Only the account and month combinations
that at least two systems posted to are compared.  A combination's spread is its
largest system total minus its smallest, taken over the systems that posted to
it; a system with no postings there is not treated as a zero.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

_CENT = Decimal("0.01")


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination whose systems do not agree."""

    account_code: str
    month: str
    totals: Mapping[str, Decimal]
    spread: Decimal


def _money(value: Decimal) -> str:
    return f"{value.quantize(_CENT, rounding=ROUND_HALF_EVEN):.2f}"


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Return the combinations whose spread is greater than ``tolerance``, by account then month."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        groups[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for account_code, month in sorted(groups):
        totals = groups[(account_code, month)]
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code, month, dict(totals), spread))
    return mismatches


def format_mismatch(mismatch: Mismatch) -> str:
    """Render one mismatch as its ``MISMATCH`` line."""
    per_system = " ".join(
        f"{system}={_money(mismatch.totals[system])}" if system in mismatch.totals else f"{system}=-"
        for system in SYSTEMS
    )
    return (
        f"MISMATCH {mismatch.account_code} {mismatch.month} "
        f"spread={_money(mismatch.spread)} {per_system}"
    )


def reconcile_lines(records: Iterable[Record], tolerance: Decimal) -> list[str]:
    """Return the ``reconcile`` output: one line per mismatch, then the count."""
    mismatches = find_mismatches(records, tolerance)
    return [format_mismatch(mismatch) for mismatch in mismatches] + [f"mismatches={len(mismatches)}"]
