"""Totals by account or by month, from a normalized records file.

Every posting counts toward a total, refunds included.  ``SPEC.md`` still
describes an earlier version that left refunds out unless ``--include-refunds``
was given; the operations team has since asked for them to be counted always, and
the flag is still accepted so their scripts keep working.

Report fields are separated by a semicolon, not a comma, because the sheet the
warehouse team loads the report into is set up for semicolons.

Totals are summed exactly and rounded once, as they are laid out, half to even,
as ``docs/CONVENTIONS.md`` requires.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import Record

DELIMITER = ";"
BY_ACCOUNT = "account"
BY_MONTH = "month"
GROUPINGS: tuple[str, ...] = (BY_ACCOUNT, BY_MONTH)
ACCOUNT_HEADER: tuple[str, ...] = ("account_code", "account_name", "total")
MONTH_HEADER: tuple[str, ...] = ("month", "total")


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even.

    A total that rounds to zero comes back as plain zero, never ``-0``.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        return abs(rounded)
    return rounded


def account_totals(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Exact totals per account code, codes ascending, each with its account name."""
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def month_totals(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Exact totals per ``YYYY-MM`` month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def _shown(total: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_total(total, settings.decimals))


def report_lines(records: Iterable[Record], by: str, settings: Settings) -> list[str]:
    """The lines of a report grouped ``by`` account or month, header line first."""
    if by == BY_ACCOUNT:
        lines = [join_record(list(ACCOUNT_HEADER), DELIMITER)]
        for code, name, total in account_totals(records):
            lines.append(join_record([code, name, _shown(total, settings)], DELIMITER))
        return lines
    if by == BY_MONTH:
        lines = [join_record(list(MONTH_HEADER), DELIMITER)]
        for month, total in month_totals(records):
            lines.append(join_record([month, _shown(total, settings)], DELIMITER))
        return lines
    raise ValueError(f"cannot group a report by {by!r}; expected one of {', '.join(GROUPINGS)}")
