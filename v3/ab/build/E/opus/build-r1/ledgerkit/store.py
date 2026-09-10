"""The normalized records file that ``ingest`` writes and the reports read.

It is a comma separated file whose header is exactly
:data:`~ledgerkit.core.records.RECORD_COLUMNS`.  Fields are quoted where the CSV
format requires it, so a description keeps any comma or quote it contained.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` in the order given and return how many were written.

    Parent directories are created when they do not exist.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
            count += 1
    return count


def load_records(path: Path) -> list[Record]:
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file (header is {header!r})")
        records: list[Record] = []
        for row in reader:
            if not row:
                continue
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {reader.line_num}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}"
                )
            values = dict(zip(RECORD_COLUMNS, row, strict=True))
            try:
                posted = date.fromisoformat(values["date"])
                amount = Decimal(values["amount"])
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
            records.append(
                Record(
                    record_id=values["record_id"],
                    source_system=values["source_system"],
                    date=posted,
                    account_code=values["account_code"],
                    account_name=values["account_name"],
                    description=values["description"],
                    amount=amount,
                )
            )
    return records
