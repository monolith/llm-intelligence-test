"""Totals for the ``report`` command.

Totals are summed at full precision and rounded once, when they are laid out for
display, half to even (``docs/CONVENTIONS.md``, "Rounding").  Report lines are
separated by semicolons, which is what the warehouse team's sheet expects.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core.records import Record
from ledgerkit.mapping import account_name

SEPARATOR = ";"
ACCOUNT_HEADER: tuple[str, ...] = ("account_code", "account_name", "total")
MONTH_HEADER: tuple[str, ...] = ("month", "total")


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even."""
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded.is_zero():
        # A small negative total would otherwise show as "-0".
        rounded = rounded.copy_abs()
    return rounded


def _totals(
    records: Iterable[Record], key: Callable[[Record], str], include_refunds: bool
) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        if record.is_refund() and not include_refunds:
            continue
        totals[key(record)] += record.amount
    return dict(sorted(totals.items()))


def totals_by_account(records: Iterable[Record], *, include_refunds: bool = True) -> dict[str, Decimal]:
    """Unrounded totals keyed by account code, codes ascending."""
    return _totals(records, lambda record: record.account_code, include_refunds)


def totals_by_month(records: Iterable[Record], *, include_refunds: bool = True) -> dict[str, Decimal]:
    """Unrounded totals keyed by ``YYYY-MM``, months ascending."""
    return _totals(records, Record.month, include_refunds)


def account_lines(
    records: Iterable[Record], settings: Settings, *, include_refunds: bool = True
) -> list[str]:
    """The ``report --by account`` output: a header line, then one line per account."""
    lines = [SEPARATOR.join(ACCOUNT_HEADER)]
    for code, total in totals_by_account(records, include_refunds=include_refunds).items():
        shown = settings.format_amount(round_total(total, settings.decimals))
        lines.append(SEPARATOR.join((code, account_name(code, settings.unknown_account_label), shown)))
    return lines


def month_lines(
    records: Iterable[Record], settings: Settings, *, include_refunds: bool = True
) -> list[str]:
    """The ``report --by month`` output: a header line, then one line per month."""
    lines = [SEPARATOR.join(MONTH_HEADER)]
    for month, total in totals_by_month(records, include_refunds=include_refunds).items():
        lines.append(SEPARATOR.join((month, settings.format_amount(round_total(total, settings.decimals)))))
    return lines
