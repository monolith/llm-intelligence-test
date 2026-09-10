"""Grouping and totaling postings for the ``report`` command."""

from __future__ import annotations

from decimal import Decimal

from ledgerkit.core.records import Record

ZERO = Decimal("0")


def totals_by_account(records: list[Record], *, include_refunds: bool) -> dict[str, tuple[str, Decimal]]:
    """Return ``account_code -> (account_name, total)`` for every account code seen.

    A refund (negative amount) posting only contributes to the total when
    ``include_refunds`` is set, but its account still appears in the result,
    with whatever total its non-refund postings add up to (zero if it has
    none).
    """
    totals: dict[str, Decimal] = {}
    names: dict[str, str] = {}
    for record in records:
        totals.setdefault(record.account_code, ZERO)
        names[record.account_code] = record.account_name
        if include_refunds or not record.is_refund():
            totals[record.account_code] += record.amount
    return {code: (names[code], total) for code, total in totals.items()}


def totals_by_month(records: list[Record], *, include_refunds: bool) -> dict[str, Decimal]:
    """Return ``month -> total`` (``YYYY-MM``) for every month seen.

    Same refund handling as :func:`totals_by_account`.
    """
    totals: dict[str, Decimal] = {}
    for record in records:
        totals.setdefault(record.month(), ZERO)
        if include_refunds or not record.is_refund():
            totals[record.month()] += record.amount
    return totals
