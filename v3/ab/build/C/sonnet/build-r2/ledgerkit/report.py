"""`report --by account|month` (SPEC.md).

Reads an already normalized records file and totals it one of two ways.  It
does not touch the export formats at all.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from ledgerkit.core.records import Record


def totals_by_account(records: list[Record], *, include_refunds: bool) -> list[tuple[str, str, Decimal]]:
    """Total every record by account code.

    Returns ``(account_code, account_name, total)`` tuples, codes ascending.
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    names: dict[str, str] = {}
    for record in records:
        if record.amount < 0 and not include_refunds:
            continue
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: list[Record], *, include_refunds: bool) -> list[tuple[str, Decimal]]:
    """Total every record by posting month.

    Returns ``(month, total)`` tuples, months ascending.
    """
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for record in records:
        if record.amount < 0 and not include_refunds:
            continue
        totals[record.month()] += record.amount
    return [(month, totals[month]) for month in sorted(totals)]
