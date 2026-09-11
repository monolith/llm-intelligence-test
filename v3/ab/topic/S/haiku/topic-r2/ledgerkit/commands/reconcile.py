"""Report account and month combinations where systems disagree."""

from __future__ import annotations

import csv
from decimal import Decimal
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def read_normalized_csv(path: Path) -> list[dict[str, str]]:
    """Read the normalized CSV file."""
    records = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames is not None
        for row in reader:
            records.append(row)
    return records


def reconcile(records_path: Path, tolerance: Decimal, settings: Settings) -> int:
    """Find and report account/month combinations where systems disagree.

    Returns exit code 0.
    """
    records = read_normalized_csv(records_path)

    # Group by (account_code, month, source_system)
    groups: dict[tuple[str, str, str], Decimal] = {}
    for record in records:
        code = record["account_code"]
        date_str = record["date"]
        month = date_str[:7]  # YYYY-MM
        system = record["source_system"]
        amount = Decimal(record["amount"])

        key = (code, month, system)
        if key not in groups:
            groups[key] = Decimal(0)
        groups[key] += amount

    # Find mismatches
    mismatches: list[tuple[str, str, dict[str, Decimal]]] = []

    # Group by (account, month) to find which systems posted to it
    account_month_groups: dict[tuple[str, str], dict[str, Decimal]] = {}
    for (code, month, system), total in groups.items():
        key = (code, month)
        if key not in account_month_groups:
            account_month_groups[key] = {}
        account_month_groups[key][system] = total

    # Check for mismatches where at least 2 systems posted
    for (code, month), systems_totals in sorted(account_month_groups.items()):
        if len(systems_totals) < 2:
            continue

        # Calculate spread
        values = list(systems_totals.values())
        spread = max(values) - min(values)

        if spread > tolerance:
            mismatches.append((code, month, systems_totals))

    # Print mismatches
    for code, month, systems_totals in mismatches:
        parts = [f"MISMATCH {code} {month} spread={spread_for_display(systems_totals)}"]
        for system in ["A", "B", "C"]:
            if system in systems_totals:
                amount = systems_totals[system]
                formatted = f"{amount:.2f}"
                parts.append(f"{system}={formatted}")
            else:
                parts.append(f"{system}=-")
        print(" ".join(parts))

    print(f"mismatches={len(mismatches)}")
    return 0


def spread_for_display(systems_totals: dict[str, Decimal]) -> str:
    """Format the spread value."""
    values = list(systems_totals.values())
    spread = max(values) - min(values)
    return f"{spread:.2f}"
