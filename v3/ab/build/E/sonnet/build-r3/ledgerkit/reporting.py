"""Totals and mismatches computed from a normalized set of records.

``report`` and ``reconcile`` both read every posting; this module is the shared
grouping and summing logic behind both commands. Nothing here prints -- see
``docs/CONVENTIONS.md``, "Program output".
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from ledgerkit.core.records import Record

SYSTEM_ORDER: tuple[str, ...] = ("A", "B", "C")


def totals_by_account(records: list[Record]) -> list[tuple[str, str, Decimal]]:
    """Sum every record's amount by account code, ascending by code."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: list[Record]) -> list[tuple[str, Decimal]]:
    """Sum every record's amount by month, ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return [(month, totals[month]) for month in sorted(totals)]


@dataclass(frozen=True)
class Mismatch:
    """One account/month combination whose systems disagree by more than tolerance."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def find_mismatches(records: list[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account/month combinations at least two systems posted to, where the
    largest and smallest system totals differ by more than ``tolerance``.
    """
    totals: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for record in records:
        group = totals[(record.account_code, record.month())]
        group[record.source_system] = group.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (account_code, month), by_system in totals.items():
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code, month, spread, dict(by_system)))
    mismatches.sort(key=lambda m: (m.account_code, m.month))
    return mismatches
