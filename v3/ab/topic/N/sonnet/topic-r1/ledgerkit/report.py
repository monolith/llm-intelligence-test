"""Totals by account or by month over a normalized file.

See ``SPEC.md``, section 2, for the command this implements.
"""

from __future__ import annotations

from decimal import Decimal

from ledgerkit.core.records import Record


def _filter_refunds(records: list[Record], *, include_refunds: bool) -> list[Record]:
    if include_refunds:
        return records
    return [record for record in records if not record.is_refund()]


def by_account(records: list[Record], *, include_refunds: bool) -> list[tuple[str, str, Decimal]]:
    """Total every posting by account code, ascending by code.

    Returns ``(account_code, account_name, total)`` rows.
    """
    kept = _filter_refunds(records, include_refunds=include_refunds)
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in kept:
        totals[record.account_code] = totals.get(record.account_code, Decimal(0)) + record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def by_month(records: list[Record], *, include_refunds: bool) -> list[tuple[str, Decimal]]:
    """Total every posting by month, ascending by month.

    Returns ``(month, total)`` rows, ``month`` as ``YYYY-MM``.
    """
    kept = _filter_refunds(records, include_refunds=include_refunds)
    totals: dict[str, Decimal] = {}
    for record in kept:
        month = record.month()
        totals[month] = totals.get(month, Decimal(0)) + record.amount
    return [(month, totals[month]) for month in sorted(totals)]
