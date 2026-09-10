"""Totals by account or by month, for the ``report`` command.

Every posting counts toward the totals, refunds included.  Totals are summed
exactly as :class:`~decimal.Decimal` and rounded once, when they are laid out for
display, half to even as ``docs/CONVENTIONS.md`` requires.

Report lines are separated by :data:`REPORT_DELIMITER`, a semicolon, because
that is what the sheet the warehouse team pulls the report into expects.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import Record

BY_ACCOUNT = "account"
BY_MONTH = "month"
GROUPINGS: tuple[str, ...] = (BY_ACCOUNT, BY_MONTH)
REPORT_DELIMITER = ";"


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even.

    A total that rounds to zero from below comes back as plain zero, so it is
    never shown as ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        return rounded.copy_abs()
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Return ``(account_code, account_name, total)`` for each code, codes ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Return ``(month, total)`` for each ``YYYY-MM`` month, months ascending."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def report_lines(records: Iterable[Record], by: str, settings: Settings) -> list[str]:
    """Return the report's lines, header first, grouped ``by`` account or month."""

    def shown(total: Decimal) -> str:
        return settings.format_amount(round_total(total, settings.decimals))

    rows: list[list[str]]
    if by == BY_ACCOUNT:
        rows = [["account_code", "account_name", "total"]]
        rows += [[code, name, shown(total)] for code, name, total in totals_by_account(records)]
    elif by == BY_MONTH:
        rows = [["month", "total"]]
        rows += [[month, shown(total)] for month, total in totals_by_month(records)]
    else:
        raise ValueError(f"cannot group a report by {by!r}")
    return [fields.join_record(row, REPORT_DELIMITER) for row in rows]
