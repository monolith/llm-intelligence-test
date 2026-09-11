"""Reading and writing the normalized records file.

``ingest`` writes this file; ``report`` and ``reconcile`` read it back.  Unlike
the per-system readers in :mod:`ledgerkit.parsers`, this file has no preamble
or trailer to trim, so the standard library ``csv`` module reads and writes it
directly.
"""

from __future__ import annotations

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_records_csv(records: list[Record], path: Path) -> None:
    """Write ``records`` to ``path`` as the normalized CSV.

    Parent directories are created if they do not exist.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())


def read_records_csv(path: Path) -> list[Record]:
    """Read a normalized records CSV, as written by :func:`write_records_csv`."""
    source = Path(path)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file")
        return [_row_to_record(row) for row in reader]


def _row_to_record(row: dict[str, str]) -> Record:
    try:
        amount = Decimal(row["amount"])
    except InvalidOperation as exc:
        raise LedgerParseError(f"bad amount {row['amount']!r} in normalized records file") from exc
    try:
        record_date = date.fromisoformat(row["date"])
    except ValueError as exc:
        raise LedgerParseError(f"bad date {row['date']!r} in normalized records file") from exc
    return Record(
        record_id=row["record_id"],
        source_system=row["source_system"],
        date=record_date,
        account_code=row["account_code"],
        account_name=row["account_name"],
        description=row["description"],
        amount=amount,
    )
