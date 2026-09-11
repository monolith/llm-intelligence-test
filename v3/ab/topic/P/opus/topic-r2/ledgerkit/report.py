"""Totals by account or by month, read from a normalized records file.

Every posting counts toward the totals, refunds included.  Totals are summed
exactly and rounded once, half to even, when they are laid out.  The fields on a
report line are separated by a semicolon, which is what the warehouse team's
sheet is set up to read.
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
ACCOUNT_HEADER: tuple[str, ...] = ("account_code", "account_name", "total")
MONTH_HEADER: tuple[str, ...] = ("month", "total")


def _show(total: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_half_even(total, settings.decimals))


def report_lines(records: Iterable[Record], by: str, settings: Settings) -> list[str]:
    """The lines of a report grouped ``by`` ``"account"`` or ``"month"``, header first.

    Accounts come out by code ascending and months ``YYYY-MM`` ascending.  An
    account is named as the records file names it.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    if by == "account":
        header = ACCOUNT_HEADER
        for record in records:
            names.setdefault(record.account_code, record.account_name)
            totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
    elif by == "month":
        header = MONTH_HEADER
        for record in records:
            month = record.month()
            totals[month] = totals.get(month, Decimal(0)) + record.amount
    else:
        raise ValueError(f"cannot group a report by {by!r}; expected one of {', '.join(GROUPINGS)}")

    lines = [join_record(list(header), SEPARATOR)]
    for key in sorted(totals):
        label = [key, names[key]] if by == "account" else [key]
        lines.append(join_record([*label, _show(totals[key], settings)], SEPARATOR))
    return lines
