"""Totals and reconciliation over normalized records.

Everything here works in exact :class:`~decimal.Decimal` dollars and returns
unrounded values.  Rounding happens once, at display, through
:func:`round_for_display`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record


def round_for_display(value: Decimal, places: int) -> Decimal:
    """Round ``value`` to ``places`` decimal places, half to even.

    A result that rounds to zero comes back as a plain zero, so it is never shown
    as ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        rounded = rounded.copy_abs()
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Total per account code, codes ascending, as ``(code, name, total)``.

    The name is the one on the first record seen for that code.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Total per ``YYYY-MM`` month, months ascending, as ``(month, total)``."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return sorted(totals.items())


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination the systems disagree about."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations whose system totals spread wider than ``tolerance``.

    Only combinations that at least two systems posted to are considered.  The
    result is ordered by account code and then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        per_system = groups.setdefault((record.account_code, record.month()), {})
        per_system[record.source_system] = (
            per_system.get(record.source_system, Decimal(0)) + record.amount
        )

    found: list[Mismatch] = []
    for (code, month), per_system in sorted(groups.items()):
        if len(per_system) < 2:
            continue
        spread = max(per_system.values()) - min(per_system.values())
        if spread > tolerance:
            found.append(Mismatch(code, month, spread, dict(per_system)))
    return found
