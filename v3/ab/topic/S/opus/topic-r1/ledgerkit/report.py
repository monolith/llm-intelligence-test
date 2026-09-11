"""``report``: totals by account or by month, read from a normalized records file.

Every posting counts toward a total, refunds included.  Totals are summed
exactly and rounded once, half to even, at the point of display, as
``docs/CONVENTIONS.md`` requires.  The fields on a report line are separated by
semicolons, which is what the warehouse team's sheet is set up to read.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

DELIMITER = ";"
ACCOUNT_HEADER: tuple[str, ...] = ("account_code", "account_name", "total")
MONTH_HEADER: tuple[str, ...] = ("month", "total")


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even, for display.

    A total that rounds to zero comes back as zero, never as negative zero.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    return rounded.copy_abs() if rounded.is_zero() else rounded


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Total the records by account code, codes ascending.

    Each code is reported with the account name the records carry for it.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    warned: set[str] = set()
    for record in records:
        code = record.account_code
        totals[code] = totals.get(code, Decimal(0)) + record.amount
        name = names.setdefault(code, record.account_name)
        if name != record.account_name and code not in warned:
            warned.add(code)
            _log.warning(
                "account %s is named both %r and %r in the records; reporting it as %r",
                code,
                name,
                record.account_name,
                name,
            )
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Total the records by posting month, ``YYYY-MM``, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def account_report(records: Iterable[Record], settings: Settings) -> list[str]:
    """The ``report --by account`` lines: a header, then one line per account code."""
    lines = [_line(ACCOUNT_HEADER)]
    for code, name, total in totals_by_account(records):
        lines.append(_line((code, name, _show(total, settings))))
    return lines


def month_report(records: Iterable[Record], settings: Settings) -> list[str]:
    """The ``report --by month`` lines: a header, then one line per month."""
    lines = [_line(MONTH_HEADER)]
    for month, total in totals_by_month(records):
        lines.append(_line((month, _show(total, settings))))
    return lines


def _show(total: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_total(total, settings.decimals))


def _line(values: Sequence[str]) -> str:
    return fields.join_record(list(values), delimiter=DELIMITER)
