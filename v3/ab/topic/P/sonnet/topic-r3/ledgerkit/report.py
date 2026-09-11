"""Totals by account or by month, read from an already normalized file."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core.records import Record


def totals_by_account(records: Iterable[Record], *, include_refunds: bool) -> list[tuple[str, str, Decimal]]:
    """Total amount per account code, codes ascending.

    Returns ``(account_code, account_name, total)`` triples with unrounded
    totals; round once, at the point of display.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        if record.is_refund() and not include_refunds:
            continue
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record], *, include_refunds: bool) -> list[tuple[str, Decimal]]:
    """Total amount per month (``YYYY-MM``), months ascending.

    Returns unrounded totals; round once, at the point of display.
    """
    totals: dict[str, Decimal] = {}
    for record in records:
        if record.is_refund() and not include_refunds:
            continue
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def format_total(total: Decimal, settings: Settings) -> str:
    """Round ``total`` half to even at the configured decimals and lay it out."""
    exponent = Decimal(1).scaleb(-settings.decimals) if settings.decimals > 0 else Decimal(1)
    rounded = total.quantize(exponent, rounding=ROUND_HALF_EVEN)
    return settings.format_amount(rounded)
