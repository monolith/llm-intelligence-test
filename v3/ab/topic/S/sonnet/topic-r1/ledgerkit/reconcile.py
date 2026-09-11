"""``reconcile`` — account and month combinations where the systems disagree.

All postings count, refunds included; there is no filtering here at all.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import csv

SYSTEMS: tuple[str, ...] = ("A", "B", "C")


@dataclass(frozen=True)
class Posting:
    """The fields reconcile needs out of one normalized record."""

    account_code: str
    source_system: str
    month: str
    amount: Decimal


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination whose systems do not agree."""

    account_code: str
    month: str
    totals: dict[str, Decimal]
    spread: Decimal


def read_postings(path: Path) -> list[Posting]:
    """Read a normalized records file into the postings reconcile groups."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            Posting(
                account_code=row["account_code"],
                source_system=row["source_system"],
                month=row["date"][:7],
                amount=Decimal(row["amount"]),
            )
            for row in reader
        ]


def find_mismatches(postings: Iterable[Posting], *, tolerance: Decimal) -> list[Mismatch]:
    """Account/month combinations where two or more systems' totals spread past tolerance."""
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for posting in postings:
        totals = groups.setdefault((posting.account_code, posting.month), {})
        totals[posting.source_system] = totals.get(posting.source_system, Decimal(0)) + posting.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in groups.items():
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=code, month=month, totals=totals, spread=spread))

    mismatches.sort(key=lambda mismatch: (mismatch.account_code, mismatch.month))
    return mismatches


def format_mismatch(mismatch: Mismatch) -> str:
    """Render one mismatch as the ``MISMATCH ...`` output line."""
    systems = " ".join(
        f"{system}={mismatch.totals[system]:.2f}" if system in mismatch.totals else f"{system}=-"
        for system in SYSTEMS
    )
    return f"MISMATCH {mismatch.account_code} {mismatch.month} spread={mismatch.spread:.2f} {systems}"
