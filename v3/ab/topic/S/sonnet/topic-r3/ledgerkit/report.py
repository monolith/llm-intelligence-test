"""Totals by account or by month, read from a normalized records file.

This reads the file :func:`ledgerkit.ingest.write_csv` produces; it never reads
the original exports.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from ledgerkit.log import get_logger

_log = get_logger(__name__)


def read_normalized(path: Path) -> list[dict[str, str]]:
    """Read a normalized records CSV back into raw string rows."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def totals_by_account(rows: list[dict[str, str]]) -> list[tuple[str, str, Decimal]]:
    """Total amount by account code, one entry per code, codes ascending."""
    names: dict[str, str] = {}
    sums: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        code = row["account_code"]
        sums[code] += Decimal(row["amount"])
        names.setdefault(code, row["account_name"])
    return [(code, names[code], sums[code]) for code in sorted(sums)]


def totals_by_month(rows: list[dict[str, str]]) -> list[tuple[str, Decimal]]:
    """Total amount by month (``YYYY-MM``), one entry per month, months ascending."""
    sums: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for row in rows:
        month = row["date"][:7]
        sums[month] += Decimal(row["amount"])
    return [(month, sums[month]) for month in sorted(sums)]


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round ``value`` to ``decimals`` places, half to even, per ``docs/CONVENTIONS.md``."""
    quantum = Decimal(1).scaleb(-decimals)
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)
