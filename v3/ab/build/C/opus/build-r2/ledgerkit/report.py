"""Totals by account or by month, for the ``report`` command.

Every posting in the normalized file counts toward a total, refunds included.
Totals are summed exactly and rounded once, half to even, when they are laid out
for display (see ``docs/CONVENTIONS.md``, "Rounding").

Report lines separate their fields with a semicolon, which is what the warehouse
team's sheet is set up to read.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core.fields import join_record
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

REPORT_DELIMITER = ";"


def round_half_even(value: Decimal, places: int) -> Decimal:
    """Round ``value`` to ``places`` decimal places, a half going to the even neighbour."""
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)


def totals_by_account(records: Iterable[Record]) -> list[tuple[str, str, Decimal]]:
    """Total every posting by account code, codes ascending.

    Each entry is ``(account_code, account_name, total)``.  The name is the one
    the records file gives the code.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    conflicted: set[str] = set()
    for record in records:
        code = record.account_code
        totals[code] = totals.get(code, Decimal(0)) + record.amount
        name = names.setdefault(code, record.account_name)
        if name != record.account_name and code not in conflicted:
            conflicted.add(code)
            _log.warning(
                "account %s is named both %r and %r in the records file; reporting it as %r",
                code,
                name,
                record.account_name,
                name,
            )
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[tuple[str, Decimal]]:
    """Total every posting by ``YYYY-MM`` month, months ascending."""
    totals: dict[str, Decimal] = {}
    for record in records:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return sorted(totals.items())


def _display(total: Decimal, settings: Settings) -> str:
    return settings.format_amount(round_half_even(total, settings.decimals))


def account_report(records: Iterable[Record], settings: Settings) -> list[str]:
    """The lines of ``report --by account``: a header, then one line per code."""
    lines = [join_record(["account_code", "account_name", "total"], REPORT_DELIMITER)]
    for code, name, total in totals_by_account(records):
        lines.append(join_record([code, name, _display(total, settings)], REPORT_DELIMITER))
    return lines


def month_report(records: Iterable[Record], settings: Settings) -> list[str]:
    """The lines of ``report --by month``: a header, then one line per month."""
    lines = [join_record(["month", "total"], REPORT_DELIMITER)]
    for month, total in totals_by_month(records):
        lines.append(join_record([month, _display(total, settings)], REPORT_DELIMITER))
    return lines
