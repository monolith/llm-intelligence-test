"""Finding account/month combinations where the three systems disagree."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from ledgerkit.core.records import Record

Totals = dict[str, Decimal]


def totals_by_account_month_system(records: Iterable[Record]) -> dict[tuple[str, str], Totals]:
    """Total amount per (account code, month), broken down by source system.

    Every posting counts, refunds included.
    """
    grouped: dict[tuple[str, str], Totals] = {}
    for record in records:
        by_system = grouped.setdefault((record.account_code, record.month()), {})
        by_system[record.source_system] = by_system.get(record.source_system, Decimal(0)) + record.amount
    return grouped


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[tuple[str, str, Totals]]:
    """Account/month combinations whose systems disagree by more than ``tolerance``.

    Only combinations with postings from at least two systems are considered.
    A combination's spread is its largest system total minus its smallest.
    Returns ``(account_code, month, totals_by_system)`` triples, ordered by
    account code and then month.
    """
    grouped = totals_by_account_month_system(records)
    mismatches: list[tuple[str, str, Totals]] = []
    for (code, month), by_system in grouped.items():
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append((code, month, by_system))
    mismatches.sort(key=lambda item: (item[0], item[1]))
    return mismatches
