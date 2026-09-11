"""Totals by account or by month.

Two things here differ from ``SPEC.md``, which was written before they changed:

* Fields on a report line are separated by a semicolon, not a comma, because the
  sheet the warehouse team pulls the report into is set up for semicolons.
* Refunds are counted in every total.  ``--include-refunds`` is still accepted
  so existing scripts keep working, but there is nothing left for it to switch.

Totals are summed at full precision and rounded once, half to even, at display.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from ledgerkit.config import Settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import Record
from ledgerkit.core.values import round_half_even

SEPARATOR = ";"
GROUPINGS: tuple[str, ...] = ("account", "month")


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """``(account code, account name, total)`` per account, codes ascending."""
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """``(YYYY-MM, total)`` per month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def report_lines(records: Iterable[Record], by: str, settings: Settings) -> list[str]:
    """The report's header line and one line per group, ``by`` being ``account`` or ``month``."""

    def show(total: Decimal) -> str:
        return settings.format_amount(round_half_even(total, settings.decimals))

    if by == "account":
        rows = [["account_code", "account_name", "total"]]
        rows += [[code, name, show(total)] for code, name, total in totals_by_account(records)]
    elif by == "month":
        rows = [["month", "total"]]
        rows += [[month, show(total)] for month, total in totals_by_month(records)]
    else:
        raise ValueError(f"cannot total by {by!r}; expected one of {', '.join(GROUPINGS)}")
    return [join_record(row, SEPARATOR) for row in rows]
