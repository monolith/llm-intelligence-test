"""``reconcile`` — where the systems disagree.

Reads a normalized records file and finds account/month combinations where the
systems that posted to them do not agree on the total.
"""

from __future__ import annotations

from decimal import Decimal

from ledgerkit.core.records import Record

DEFAULT_RECORDS_PATH = "out/records.csv"
SYSTEMS: tuple[str, ...] = ("A", "B", "C")


def group_totals(records: list[Record]) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Total ``records`` by ``(account_code, month, source_system)``.

    Returns a mapping from ``(account_code, month)`` to a mapping of system
    letter to that system's total for the combination.  All postings count,
    refunds included.
    """
    totals: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        per_system = totals.setdefault(key, {})
        per_system[record.source_system] = per_system.get(record.source_system, Decimal(0)) + record.amount
    return totals


def mismatches(
    records: list[Record], tolerance: Decimal
) -> list[tuple[str, str, Decimal, dict[str, Decimal]]]:
    """Find account/month combinations whose system totals spread more than ``tolerance``.

    Only combinations at least two systems posted to are considered.  Returns
    ``(account_code, month, spread, per_system_totals)`` tuples, ordered by
    account code and then month.
    """
    out: list[tuple[str, str, Decimal, dict[str, Decimal]]] = []
    for (account_code, month), per_system in group_totals(records).items():
        if len(per_system) < 2:
            continue
        values = list(per_system.values())
        spread = max(values) - min(values)
        if spread > tolerance:
            out.append((account_code, month, spread, per_system))
    out.sort(key=lambda item: (item[0], item[1]))
    return out
