"""Totals for the ``report`` command.

Refunds are always part of these totals; see ``cli.cmd_report`` for the note
on ``--include-refunds``.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Sum amounts per account code. Returns ``(code, name, total)`` sorted by code."""
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Sum amounts per month. Returns ``(month, total)`` sorted by month."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round ``value`` to ``decimals`` places, half to even, per docs/CONVENTIONS.md."""
    quantum = Decimal(1).scaleb(-decimals)
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)
