"""Totals by account or by month, for the ``report`` command.

Totals are kept exact and rounded once, half to even, when they are laid out
for display.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record

SEPARATOR = ";"
ACCOUNT_HEADER: tuple[str, ...] = ("account_code", "account_name", "total")
MONTH_HEADER: tuple[str, ...] = ("month", "total")


def _included(records: Iterable[Record], include_refunds: bool) -> list[Record]:
    return [record for record in records if include_refunds or not record.is_refund()]


def totals_by_account(
    records: Iterable[Record], *, include_refunds: bool = True
) -> list[tuple[str, str, Decimal]]:
    """Exact totals per account code, codes ascending, as ``(code, name, total)``."""
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in _included(records, include_refunds):
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(
    records: Iterable[Record], *, include_refunds: bool = True
) -> list[tuple[str, Decimal]]:
    """Exact totals per ``YYYY-MM`` month, months ascending, as ``(month, total)``."""
    totals: dict[str, Decimal] = {}
    for record in _included(records, include_refunds):
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def format_total(value: Decimal, decimals: int) -> str:
    """Round ``value`` half to even at ``decimals`` places and lay it out."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded == 0:
        rounded = abs(rounded)  # no "-0" for a small negative total
    return f"{rounded:.{max(decimals, 0)}f}"


def account_lines(
    records: Iterable[Record], decimals: int, *, include_refunds: bool = True
) -> list[str]:
    """The ``report --by account`` output, header first."""
    lines = [SEPARATOR.join(ACCOUNT_HEADER)]
    for code, name, total in totals_by_account(records, include_refunds=include_refunds):
        lines.append(SEPARATOR.join((code, name, format_total(total, decimals))))
    return lines


def month_lines(
    records: Iterable[Record], decimals: int, *, include_refunds: bool = True
) -> list[str]:
    """The ``report --by month`` output, header first."""
    lines = [SEPARATOR.join(MONTH_HEADER)]
    for month, total in totals_by_month(records, include_refunds=include_refunds):
        lines.append(SEPARATOR.join((month, format_total(total, decimals))))
    return lines
