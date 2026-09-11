"""Core operations: ingest, report, reconcile, validate."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.converters import rows_to_records_a, rows_to_records_b, rows_to_records_c
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import RECORD_COLUMNS, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import LedgerParseError, detect_system, read_rows

_log = get_logger(__name__)


def ingest(
    input_files: list[Path],
    output_path: Path,
    settings: Settings,
) -> int:
    """Merge exports into one normalized file.

    Returns the number of records written.
    """
    all_records: list[Record] = []

    for filepath in input_files:
        system = detect_system(filepath)
        raw_rows = read_rows(filepath)

        if system == "A":
            records = rows_to_records_a(raw_rows, settings.unknown_account_label)
        elif system == "B":
            records = rows_to_records_b(raw_rows, settings.unknown_account_label)
        else:  # system == "C"
            records = rows_to_records_c(raw_rows, settings.unknown_account_label)

        all_records.extend(records)

    # Normalize: clean, sort, and keep all records (including refunds)
    normalized = normalize(all_records, keep_refunds=True)

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(RECORD_COLUMNS)
        for record in normalized:
            writer.writerow(record.to_row())

    return len(normalized)


def report_by_account(
    records: list[Record],
    settings: Settings,
) -> list[str]:
    """Generate account totals report."""
    totals: dict[str, tuple[str, Decimal]] = {}

    for record in records:
        key = record.account_code
        if key not in totals:
            totals[key] = (record.account_name, Decimal(0))
        name, total = totals[key]
        totals[key] = (name, total + record.amount)

    # Sort by account code
    lines = ["account_code;account_name;total"]
    for code in sorted(totals.keys()):
        name, total = totals[code]
        # Round half-to-even
        rounded = total.quantize(Decimal(10) ** -settings.decimals)
        formatted = settings.format_amount(rounded)
        lines.append(f"{code};{name};{formatted}")

    return lines


def report_by_month(
    records: list[Record],
    settings: Settings,
) -> list[str]:
    """Generate monthly totals report."""
    totals: dict[str, Decimal] = defaultdict(Decimal)

    for record in records:
        month = record.month()
        totals[month] += record.amount

    # Sort by month
    lines = ["month;total"]
    for month in sorted(totals.keys()):
        total = totals[month]
        # Round half-to-even
        rounded = total.quantize(Decimal(10) ** -settings.decimals)
        formatted = settings.format_amount(rounded)
        lines.append(f"{month};{formatted}")

    return lines


def reconcile(
    records: list[Record],
    settings: Settings,
) -> list[str]:
    """Find mismatched account/month combinations."""
    # Group by account, month, and system
    groups: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)

    for record in records:
        month = record.month()
        key = (record.account_code, month, record.source_system)
        groups[key] += record.amount

    # Find account/month combinations with 2+ systems
    account_months: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for (code, month, system), total in groups.items():
        account_months[(code, month)][system] = total

    # Find mismatches
    mismatches: list[tuple[str, str, dict[str, Decimal], Decimal]] = []
    for (code, month), system_totals in account_months.items():
        if len(system_totals) < 2:
            continue

        # Calculate spread
        amounts = list(system_totals.values())
        spread = max(amounts) - min(amounts)

        if spread > settings.tolerance:
            mismatches.append((code, month, system_totals, spread))

    # Sort by account code, then month
    mismatches.sort(key=lambda x: (x[0], x[1]))

    # Format output
    lines = []
    for code, month, system_totals, spread in mismatches:
        parts = [f"MISMATCH {code} {month}", f"spread={spread:.2f}"]

        for system in ["A", "B", "C"]:
            if system in system_totals:
                amount = system_totals[system]
                parts.append(f"{system}={amount:.2f}")
            else:
                parts.append(f"{system}=-")

        lines.append(" ".join(parts))

    lines.append(f"mismatches={len(lines)}")
    return lines


def validate(
    input_files: list[Path],
    settings: Settings,
) -> tuple[int, int]:
    """Validate export files.

    Returns (total_rows_checked, rejected_rows).
    """
    total_rows = 0
    rejected = 0
    account_pattern = re.compile(settings.account_code_pattern)

    for filepath in input_files:
        try:
            system = detect_system(filepath)
            raw_rows = read_rows(filepath)
        except LedgerParseError as exc:
            _log.warning("cannot read %s: %s", filepath.name, exc)
            return (0, 1)  # File read error

        # Get expected column count for this system
        if system == "A":
            from ledgerkit.parsers import system_a
            expected_cols = len(system_a.COLUMNS)
            col_map = {"code": "account", "date": "posted_on", "amount": "amount"}
        elif system == "B":
            from ledgerkit.parsers import system_b
            expected_cols = len(system_b.COLUMNS)
            col_map = {"code": "acct", "date": "value_date", "amount": "amount"}
        else:
            from ledgerkit.parsers import system_c
            expected_cols = len(system_c.COLUMNS)
            col_map = {"code": "ledger_acct", "date": "txn_date", "amount": "gross_amount"}

        # Validate each row
        for idx, row in enumerate(raw_rows, start=1):
            total_rows += 1
            issues = []

            # Check field count
            if len(row) != expected_cols:
                issues.append(f"expected {expected_cols} fields, found {len(row)}")

            if not issues:
                # Check account code format
                code = row.get(col_map["code"], "")
                if not account_pattern.match(code.strip()):
                    issues.append(f"account code {code!r} does not match pattern")

            if not issues:
                # Check date format
                date_str = row.get(col_map["date"], "")
                try:
                    from datetime import datetime
                    if system == "C":
                        datetime.strptime(date_str.strip(), "%d/%m/%Y")
                    else:
                        datetime.strptime(date_str.strip(), "%Y-%m-%d")
                except ValueError:
                    issues.append(f"invalid date: {date_str!r}")

            if not issues:
                # Check amount format
                amount_str = row.get(col_map["amount"], "")
                try:
                    from decimal import Decimal
                    if system == "B":
                        # Must be integer cents
                        int(amount_str.strip())
                    else:
                        Decimal(amount_str.strip())
                except (ValueError, TypeError):
                    issues.append(f"invalid amount: {amount_str!r}")

            if issues:
                _log.warning(
                    "%s line %d: %s",
                    filepath.name,
                    idx + 1,  # +1 for header line
                    issues[0],
                )
                rejected += 1

    return (total_rows, rejected)
