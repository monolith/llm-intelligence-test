"""Reading and writing the normalized records file that ``ingest`` produces.

The file is an ordinary comma separated file whose header is exactly
:data:`~ledgerkit.core.records.RECORD_COLUMNS`.  Quoting follows the usual CSV
rules, so a description containing a comma or a quote comes back unchanged.
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


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source}: not a normalized records file (unexpected header)")
        for values in reader:
            if not values:
                continue
            if len(values) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source} line {reader.line_num}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(values)}"
                )
            row = dict(zip(RECORD_COLUMNS, values, strict=True))
            try:
                posted = date.fromisoformat(row["date"])
                amount = Decimal(row["amount"])
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source} line {reader.line_num}: {exc}") from exc
            records.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=posted,
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=amount,
                )
            )
    return records
