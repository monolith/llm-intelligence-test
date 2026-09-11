"""Totals by account or by month, for ``python -m ledgerkit report``.

Every posting counts toward the totals, refunds included.  Fields on a report
line are separated by :data:`REPORT_DELIMITER`, a semicolon, because the sheet
the warehouse team loads the report into is set up for semicolons.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import Record

REPORT_DELIMITER = ";"
GROUPINGS: tuple[str, ...] = ("account", "month")


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total for display, half to even, as ``docs/CONVENTIONS.md`` requires."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    # A negative total that rounds to nothing would otherwise print as "-0".
    return rounded.copy_abs() if rounded.is_zero() else rounded


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
    """The report's header line and one line per group, ready to print.

    ``by`` is ``"account"`` or ``"month"``.  Totals are summed exactly and
    rounded once, here, to ``settings.decimals`` places.
    """

    def line(*values: str) -> str:
        return fields.join_record(list(values), REPORT_DELIMITER)

    def shown(total: Decimal) -> str:
        return settings.format_amount(round_total(total, settings.decimals))

    if by == "account":
        return [line("account_code", "account_name", "total")] + [
            line(code, name, shown(total)) for code, name, total in totals_by_account(records)
        ]
    if by == "month":
        return [line("month", "total")] + [
            line(month, shown(total)) for month, total in totals_by_month(records)
        ]
    raise ValueError(f"cannot group a report by {by!r}; expected one of {', '.join(GROUPINGS)}")
