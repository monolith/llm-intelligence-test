"""Totals over normalized records: the ``report`` and ``reconcile`` commands.

Everything here works on exact :class:`~decimal.Decimal` totals and rounds once,
at the point of display, half to even, as ``docs/CONVENTIONS.md`` requires.
Functions return lines; the command line prints them.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

REPORT_DELIMITER = ";"
RECONCILE_PLACES = 2
GROUPINGS: tuple[str, ...] = ("account", "month")


def round_for_display(value: Decimal, places: int) -> Decimal:
    """Round ``value`` to ``places`` decimals, half to even, never showing ``-0``."""
    rounded = value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        return abs(rounded)
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """``(account_code, account_name, total)`` for every code, codes ascending."""
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """``(YYYY-MM, total)`` for every month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def report_lines(records: Iterable[Record], by: str, settings: Settings) -> list[str]:
    """The header and total lines of ``report --by account|month``.

    Refunds are part of the totals; fields are separated by semicolons.
    """

    def shown(total: Decimal) -> str:
        return settings.format_amount(round_for_display(total, settings.decimals))

    if by == "account":
        lines = [REPORT_DELIMITER.join(("account_code", "account_name", "total"))]
        for code, name, total in totals_by_account(records):
            lines.append(fields.join_record([code, name, shown(total)], REPORT_DELIMITER))
        return lines
    if by == "month":
        lines = [REPORT_DELIMITER.join(("month", "total"))]
        for month, total in totals_by_month(records):
            lines.append(fields.join_record([month, shown(total)], REPORT_DELIMITER))
        return lines
    raise ValueError(f"unknown grouping {by!r}; expected one of {', '.join(GROUPINGS)}")


@dataclass(frozen=True)
class Mismatch:
    """One account and month combination whose system totals disagree."""

    account_code: str
    month: str
    spread: Decimal
    totals: dict[str, Decimal]

    def to_line(self) -> str:
        """Render as ``MISMATCH <code> <month> spread=<n> A=<n> B=<n> C=<n>``."""
        parts = ["MISMATCH", self.account_code, self.month, f"spread={_two_places(self.spread)}"]
        for system in SYSTEMS:
            total = self.totals.get(system)
            parts.append(f"{system}={'-' if total is None else _two_places(total)}")
        return " ".join(parts)


def _two_places(value: Decimal) -> str:
    return f"{round_for_display(value, RECONCILE_PLACES):.{RECONCILE_PLACES}f}"


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Account and month combinations posted by two or more systems whose spread exceeds ``tolerance``.

    Every posting counts, refunds included.  Results are ordered by account code
    and then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        bucket = groups.setdefault((record.account_code, record.month()), {})
        bucket[record.source_system] = bucket.get(record.source_system, Decimal(0)) + record.amount

    mismatches: list[Mismatch] = []
    for (code, month), totals in sorted(groups.items()):
        if len(totals) < 2:
            continue
        spread = max(totals.values()) - min(totals.values())
        if spread > tolerance:
            mismatches.append(Mismatch(account_code=code, month=month, spread=spread, totals=totals))
    return mismatches
