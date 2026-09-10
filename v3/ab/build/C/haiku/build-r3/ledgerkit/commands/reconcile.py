"""Report where systems disagree on totals."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from ledgerkit.config import load_settings
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def read_records(path: str) -> list[Record]:
    """Read records from a normalized CSV file."""
    from ledgerkit.core.records import Record
    from ledgerkit.core import fields
    from datetime import date

    records: list[Record] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        header_line = handle.readline().rstrip("\n")
        header = fields.split_record(header_line)
        for line in handle:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            row_fields = fields.split_record(line)
            if len(row_fields) != len(header):
                _log.warning("skipping row with wrong field count")
                continue
            row = dict(zip(header, row_fields))
            try:
                record = Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date.fromisoformat(row["date"]),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]),
                )
                records.append(record)
            except (ValueError, KeyError) as exc:
                _log.warning("skipping malformed record: %s", exc)
                continue
    return records


def reconcile(records_path: str, tolerance: Decimal) -> int:
    """Report account and month combinations where systems disagree.

    Args:
        records_path: Path to the normalized CSV file.
        tolerance: Maximum allowed difference in dollars.

    Returns:
        Exit code (0).
    """
    from ledgerkit.cli import emit

    settings = load_settings()
    records = read_records(records_path)

    # Group by (account, month, system) and total
    groups: dict[tuple[str, str, str], Decimal] = defaultdict(Decimal)
    for record in records:
        key = (record.account_code, record.month(), record.source_system)
        groups[key] += record.amount

    # Find combinations that have 2+ systems posting
    combinations: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(dict)
    for (account, month, system), total in groups.items():
        combinations[(account, month)][system] = total

    # Find mismatches
    mismatches = []
    for (account, month), system_totals in combinations.items():
        if len(system_totals) < 2:
            continue

        totals = [v for v in system_totals.values()]
        spread = max(totals) - min(totals)

        if spread > tolerance:
            mismatches.append((account, month, spread, system_totals))

    mismatches.sort(key=lambda x: (x[0], x[1]))

    for account, month, spread, system_totals in mismatches:
        amounts = []
        for system in ("A", "B", "C"):
            if system in system_totals:
                total = system_totals[system]
                formatted = f"{total:.2f}"
                amounts.append(formatted)
            else:
                amounts.append("-")

        a_str, b_str, c_str = amounts
        emit(f"MISMATCH {account} {month} spread={spread:.2f} A={a_str} B={b_str} C={c_str}")

    emit(f"mismatches={len(mismatches)}")
    return 0
