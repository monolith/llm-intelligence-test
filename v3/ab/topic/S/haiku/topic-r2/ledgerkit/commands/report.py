"""Print totals by account or month."""

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


def report_by_account(path: Path, settings: Settings) -> None:
    """Print totals by account code."""
    records = read_normalized_csv(path)

    # Group by account code
    totals: dict[str, tuple[str, Decimal]] = {}
    for record in records:
        code = record["account_code"]
        name = record["account_name"]
        amount = Decimal(record["amount"])

        if code not in totals:
            totals[code] = (name, Decimal(0))
        prev_name, prev_total = totals[code]
        totals[code] = (prev_name, prev_total + amount)

    # Print header
    print("account_code;account_name;total")

    # Print sorted by account code
    for code in sorted(totals.keys()):
        name, total = totals[code]
        rounded = total.quantize(Decimal(10) ** -settings.decimals)
        formatted = settings.format_amount(rounded)
        print(f"{code};{name};{formatted}")


def report_by_month(path: Path, settings: Settings) -> None:
    """Print totals by month."""
    records = read_normalized_csv(path)

    # Group by month
    totals: dict[str, Decimal] = {}
    for record in records:
        date_str = record["date"]
        month = date_str[:7]  # YYYY-MM
        amount = Decimal(record["amount"])

        if month not in totals:
            totals[month] = Decimal(0)
        totals[month] += amount

    # Print header
    print("month;total")

    # Print sorted by month
    for month in sorted(totals.keys()):
        total = totals[month]
        rounded = total.quantize(Decimal(10) ** -settings.decimals)
        formatted = settings.format_amount(rounded)
        print(f"{month};{formatted}")


def report(records_path: Path, by: str, settings: Settings) -> int:
    """Generate a report on totals.

    Returns exit code 0.
    """
    if by == "account":
        report_by_account(records_path, settings)
    elif by == "month":
        report_by_month(records_path, settings)

    return 0
