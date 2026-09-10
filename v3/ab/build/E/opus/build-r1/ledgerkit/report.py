"""Totals and cross-system reconciliation over normalized records.

Everything here sums exact :class:`~decimal.Decimal` amounts and returns them
unrounded.  Rounding happens once, when the caller formats a total for display.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS


@dataclass(frozen=True)
class AccountTotal:
    """The total posted to one account code."""

    account_code: str
    account_name: str
    total: Decimal


@dataclass(frozen=True)
class MonthTotal:
    """The total posted in one ``YYYY-MM`` month."""

    month: str
    total: Decimal


@dataclass(frozen=True)
class Mismatch:
    """One account and month on which the systems that posted to it disagree."""

    account_code: str
    month: str
    spread: Decimal
    by_system: dict[str, Decimal]


def totals_by_account(records: Iterable[Record]) -> list[AccountTotal]:
    """Total every record by account code, codes ascending.

    The name shown for a code is the one the records file carries for it.
    """
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [AccountTotal(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[MonthTotal]:
    """Total every record by posting month, months ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return [MonthTotal(month, totals[month]) for month in sorted(totals)]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations where the posting systems disagree by more than ``tolerance``.

    Only combinations that at least two systems posted to are considered.  The
    spread is the largest system total minus the smallest.  Results are ordered
    by account code, then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        groups[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(groups.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            ordered = {system: by_system[system] for system in SYSTEMS if system in by_system}
            mismatches.append(Mismatch(code, month, spread, ordered))
    return mismatches
