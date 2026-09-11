"""Where the three systems disagree, read from a normalized records file.

Like :mod:`ledgerkit.report`, this reads the normalized file only; it never
reads the original exports.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from ledgerkit.log import get_logger

_log = get_logger(__name__)

SYSTEMS: tuple[str, ...] = ("A", "B", "C")

Mismatch = tuple[str, str, dict[str, Decimal]]


def read_normalized(path: Path) -> list[dict[str, str]]:
    """Read a normalized records CSV back into raw string rows."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def totals_by_group(rows: list[dict[str, str]]) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Sum amounts by (account code, month, source system)."""
    totals: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for row in rows:
        key = (row["account_code"], row["date"][:7])
        by_system = totals[key]
        system = row["source_system"]
        by_system[system] = by_system.get(system, Decimal("0")) + Decimal(row["amount"])
    return totals


def find_mismatches(rows: list[dict[str, str]], tolerance: Decimal) -> list[Mismatch]:
    """Account/month combinations at least two systems posted to, whose spread exceeds ``tolerance``.

    Ordered by account code, then month.
    """
    grouped = totals_by_group(rows)
    mismatches: list[Mismatch] = []
    for (code, month), by_system in grouped.items():
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append((code, month, by_system))
    mismatches.sort(key=lambda item: (item[0], item[1]))
    return mismatches
