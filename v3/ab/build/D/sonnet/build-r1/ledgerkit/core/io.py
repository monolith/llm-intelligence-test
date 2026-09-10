"""Reading and writing the normalized records CSV.

This is the file :mod:`ledgerkit.ingest` writes and :mod:`ledgerkit.report` and
:mod:`ledgerkit.reconcile` read back.  The header and field order are
:data:`~ledgerkit.core.records.RECORD_COLUMNS`.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, Record


def write_records(records: list[Record], path: Path) -> None:
    """Write ``records`` to ``path`` as the normalized CSV.

    Parent directories are created if they do not exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())


def read_records(path: Path) -> list[Record]:
    """Read the normalized CSV at ``path`` back into :class:`Record` values."""
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            for row in reader
        ]
