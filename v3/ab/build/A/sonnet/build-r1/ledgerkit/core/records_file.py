"""Reading and writing the one normalized CSV that ``ingest`` produces and that
``report`` and ``reconcile`` read back.

This is a plain, self-produced CSV file, not one of the three export formats,
so it is read and written with the standard library's ``csv`` module rather
than the line-at-a-time splitter the export readers use.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_normalized(path: Path, records: list[Record]) -> None:
    """Write ``records`` to ``path`` as the normalized CSV, creating parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())


def read_normalized(path: Path) -> list[Record]:
    """Read a normalized CSV back into :class:`Record` values."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != list(RECORD_COLUMNS):
            raise LedgerParseError(f"{path}: not a normalized records file")
        records: list[Record] = []
        for row in reader:
            record_id, source_system, iso_date, account_code, account_name, description, amount = row
            records.append(
                Record(
                    record_id=record_id,
                    source_system=source_system,
                    date=date.fromisoformat(iso_date),
                    account_code=account_code,
                    account_name=account_name,
                    description=description,
                    amount=Decimal(amount),
                )
            )
    return records
