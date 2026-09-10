"""Totals for `report`, grouped by account or by month.

Refunds are included in every total. Reports run for the FY-1 close left them
out by default, and `report` used to match that, but the warehouse team's
sheet now needs every posting counted, so the grouping here never drops a
refund - `--include-refunds` still exists as a flag because its name is fixed,
but it has nothing left to switch.

Totals round half to even, at the `[report] decimals` setting, per
`docs/CONVENTIONS.md`. The rounding happens once, here, never on an individual
posting.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit import mapping
from ledgerkit.config import Settings
from ledgerkit.core.records import Record

FIELD_SEPARATOR = ";"


def _round(value: Decimal, decimals: int) -> Decimal:
    exponent = Decimal(1).scaleb(-decimals)
    return value.quantize(exponent, rounding=ROUND_HALF_EVEN)


def totals_by_account(records: list[Record], settings: Settings) -> list[tuple[str, str, Decimal]]:
    """One ``(account_code, account_name, total)`` per account, codes ascending."""
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for record in records:
        totals[record.account_code] += record.amount
    return [
        (code, mapping.account_name(code, settings.unknown_account_label), _round(totals[code], settings.decimals))
        for code in sorted(totals)
    ]


def totals_by_month(records: list[Record], settings: Settings) -> list[tuple[str, Decimal]]:
    """One ``(month, total)`` per month, months ascending."""
    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for record in records:
        totals[record.month()] += record.amount
    return [(month, _round(totals[month], settings.decimals)) for month in sorted(totals)]
