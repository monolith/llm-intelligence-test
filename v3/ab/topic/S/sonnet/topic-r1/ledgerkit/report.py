"""``report`` — totals by account or by month, read from a normalized file.

Refunds are counted into these totals by default.  ``--include-refunds`` is
still accepted on the command line, for scripts that already pass it, but it
no longer changes anything: nothing here is ever filtered out by amount.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

FIELD_SEPARATOR = ";"


@dataclass(frozen=True)
class Posting:
    """The fields a report total needs out of one normalized record."""

    account_code: str
    account_name: str
    month: str
    amount: Decimal


def read_postings(path: Path) -> list[Posting]:
    """Read a normalized records file into the postings a report totals."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            Posting(
                account_code=row["account_code"],
                account_name=row["account_name"],
                month=row["date"][:7],
                amount=Decimal(row["amount"]),
            )
            for row in reader
        ]


def totals_by_account(postings: Iterable[Posting]) -> list[tuple[str, str, Decimal]]:
    """Total every posting by account code, codes ascending."""
    sums: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for posting in postings:
        sums[posting.account_code] = sums.get(posting.account_code, Decimal(0)) + posting.amount
        names.setdefault(posting.account_code, posting.account_name)
    return [(code, names[code], sums[code]) for code in sorted(sums)]


def totals_by_month(postings: Iterable[Posting]) -> list[tuple[str, Decimal]]:
    """Total every posting by month (``YYYY-MM``), months ascending."""
    sums: dict[str, Decimal] = {}
    for posting in postings:
        sums[posting.month] = sums.get(posting.month, Decimal(0)) + posting.amount
    return [(month, sums[month]) for month in sorted(sums)]
