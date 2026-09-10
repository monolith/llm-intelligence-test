"""Reading and writing the normalized records file.

This is the CSV `ingest` writes and `report` and `reconcile` read back: the
header line from :data:`~ledgerkit.core.records.RECORD_COLUMNS`, then one row
per :class:`~ledgerkit.core.records.Record` in :func:`~ledgerkit.core.records.sort_key`
order. It uses the same quote-aware splitting and joining the export readers
use, since a description carried over from an export can still hold a comma or
a quote.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import fields as fieldutil
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_records(path: Path, records: list[Record]) -> None:
    """Write ``records`` to ``path`` as the normalized CSV, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(RECORD_COLUMNS)]
    lines.extend(fieldutil.join_record(record.to_row()) for record in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_records(path: Path) -> list[Record]:
    """Read the normalized CSV at ``path`` back into :class:`Record` values."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise LedgerParseError(f"{source.name}: empty records file")

    header = fieldutil.split_record(lines[0])
    if tuple(header) != RECORD_COLUMNS:
        raise LedgerParseError(f"{source.name}: expected header {list(RECORD_COLUMNS)}, found {header}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        values = fieldutil.split_record(line)
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
            )
        row = dict(zip(RECORD_COLUMNS, values, strict=True))
        records.append(
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
        )
    return records
