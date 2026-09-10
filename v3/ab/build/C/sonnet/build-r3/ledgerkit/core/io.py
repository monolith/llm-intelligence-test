"""Reading and writing the normalized records file.

This is the CSV with the ``record_id,source_system,date,account_code,
account_name,description,amount`` header that ``ingest`` produces and that
``report`` and ``reconcile`` read back in.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def write_normalized_csv(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` as the normalized CSV.  Returns the row count.

    Parent directories are created if they do not exist.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = list(records)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in rows:
            writer.writerow(record.to_row())
    _log.info("wrote %d row(s) to %s", len(rows), destination)
    return len(rows)


def read_normalized_csv(path: Path) -> list[Record]:
    """Read a normalized CSV back into :class:`Record` values."""
    source = Path(path)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file")
        out: list[Record] = []
        for line_number, row in enumerate(reader, start=2):
            try:
                out.append(
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
            except (InvalidOperation, ValueError) as exc:
                raise LedgerParseError(f"{source.name} line {line_number}: malformed row") from exc
    _log.info("read %d row(s) from %s", len(out), source)
    return out
