"""Totals by account or by month, over the records in a normalized file.

Every posting counts toward a total, refunds included.  Totals are summed
exactly and rounded once, half to even, when they are laid out.  The lines are
separated by semicolons, because the sheet the warehouse team pulls the report
into is set up for them.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from ledgerkit.config import Settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import Record
from ledgerkit.core.values import round_half_even

BY_ACCOUNT = "account"
BY_MONTH = "month"
GROUPINGS: tuple[str, ...] = (BY_ACCOUNT, BY_MONTH)
SEPARATOR = ";"


def totals_by_account(records: Iterable[Record]) -> dict[str, tuple[str, Decimal]]:
    """Exact total per account code, with the account name, keyed in code order."""
    names: dict[str, str] = {}
    totals: dict[str, Decimal] = {}
    for record in records:
        names.setdefault(record.account_code, record.account_name)
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
    return {code: (names[code], totals[code]) for code in sorted(totals)}


def totals_by_month(records: Iterable[Record]) -> dict[str, Decimal]:
    """Exact total per ``YYYY-MM`` month, keyed in month order."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return {month: totals[month] for month in sorted(totals)}


def report_lines(records: Iterable[Record], by: str, settings: Settings) -> list[str]:
    """The report for grouping ``by``: a header line, then one line per group."""
    if by == BY_ACCOUNT:
        lines = [_line(["account_code", "account_name", "total"])]
        for code, (name, total) in totals_by_account(records).items():
            lines.append(_line([code, name, _show(total, settings)]))
        return lines
    if by == BY_MONTH:
        lines = [_line(["month", "total"])]
        for month, total in totals_by_month(records).items():
            lines.append(_line([month, _show(total, settings)]))
        return lines
    raise ValueError(f"unknown report grouping {by!r}; expected one of {', '.join(GROUPINGS)}")


def _show(total: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_half_even(total, settings.decimals))


def _line(fields: list[str]) -> str:
    return join_record(fields, SEPARATOR)
