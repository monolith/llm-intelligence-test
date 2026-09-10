"""``report`` — totals by account or by month.

Reads a normalized records file; does not touch the export files themselves.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.core.records import Record

DEFAULT_RECORDS_PATH = "out/records.csv"


def totals_by_account(records: list[Record], *, include_refunds: bool) -> list[tuple[str, str, Decimal]]:
    """Total ``records`` by account code.

    Returns ``(account_code, account_name, total)`` tuples, account codes
    ascending.
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        if record.is_refund() and not include_refunds:
            continue
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: list[Record], *, include_refunds: bool) -> list[tuple[str, Decimal]]:
    """Total ``records`` by month.

    Returns ``(month, total)`` tuples, months ascending.
    """
    totals: dict[str, Decimal] = {}
    for record in records:
        if record.is_refund() and not include_refunds:
            continue
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round ``value`` to ``decimals`` places, half to even, per ``docs/CONVENTIONS.md``."""
    quantum = Decimal(1).scaleb(-decimals)
    return value.quantize(quantum, rounding=ROUND_HALF_EVEN)
