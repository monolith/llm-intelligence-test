"""Where the three systems disagree: totals per account, month and system.

All postings count here, refunds included; there is no ``--include-refunds``
switch for this command.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from ledgerkit.log import get_logger

_log = get_logger(__name__)


def totals_by_account_month_system(
    rows: Iterable[dict[str, str]],
) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Total amount per ``(account_code, month)``, broken out by source system."""
    totals: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for row in rows:
        key = (row["account_code"], row["date"][:7])
        totals[key][row["source_system"]] += Decimal(row["amount"])
    return {key: dict(by_system) for key, by_system in totals.items()}


def find_mismatches(
    rows: Iterable[dict[str, str]], *, tolerance: Decimal
) -> list[tuple[str, str, dict[str, Decimal]]]:
    """Account/month combinations where at least two systems' totals disagree.

    Only combinations at least two systems posted to are considered.  A
    combination is reported when its spread — largest system total minus
    smallest — is greater than ``tolerance``.  The result is ordered by account
    code, then month.
    """
    grouped = totals_by_account_month_system(rows)
    mismatches: list[tuple[str, str, dict[str, Decimal]]] = []
    for (code, month), by_system in grouped.items():
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append((code, month, by_system))
    mismatches.sort(key=lambda item: (item[0], item[1]))
    return mismatches
