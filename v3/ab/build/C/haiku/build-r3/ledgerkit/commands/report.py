"""Print totals by account or by month."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from ledgerkit.config import load_settings, Settings
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def read_records(path: str) -> list[Record]:
    """Read records from a normalized CSV file."""
    from ledgerkit.core.records import Record, RECORD_COLUMNS
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


def report(by: str, records_path: str) -> int:
    """Print totals by account or month.

    Args:
        by: Either "account" or "month".
        records_path: Path to the normalized CSV file.

    Returns:
        Exit code (0).
    """
    settings = load_settings()
    records = read_records(records_path)

    if by == "account":
        return report_by_account(records, settings)
    elif by == "month":
        return report_by_month(records, settings)
    else:
        return 1


def report_by_account(records: list[Record], settings: Settings) -> int:
    """Print totals grouped by account code."""
    from ledgerkit.cli import emit

    totals: dict[str, tuple[str, Decimal]] = defaultdict(lambda: ("", Decimal(0)))

    for record in records:
        code = record.account_code
        name = record.account_name
        current_total = totals[code][1] if code in totals else Decimal(0)
        totals[code] = (name, current_total + record.amount)

    emit("account_code;account_name;total")
    for code in sorted(totals.keys()):
        name, total = totals[code]
        formatted_total = settings.format_amount(total)
        emit(f"{code};{name};{formatted_total}")

    return 0


def report_by_month(records: list[Record], settings: Settings) -> int:
    """Print totals grouped by month."""
    from ledgerkit.cli import emit

    totals: dict[str, Decimal] = defaultdict(Decimal)

    for record in records:
        month = record.month()
        totals[month] = totals[month] + record.amount

    emit("month;total")
    for month in sorted(totals.keys()):
        total = totals[month]
        formatted_total = settings.format_amount(total)
        emit(f"{month};{formatted_total}")

    return 0
