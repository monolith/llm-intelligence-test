"""The normalized records file that ``ingest`` writes and the reports read.

It is a comma separated file with a :data:`~ledgerkit.core.records.RECORD_COLUMNS`
header, quoted by the standard library ``csv`` module wherever a field needs it.
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
    _log.info("wrote %d record(s) to %s", count, target)
    return count


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != list(RECORD_COLUMNS):
            raise LedgerParseError(f"{source.name}: header is not {','.join(RECORD_COLUMNS)}")
        for values in reader:
            if not values:
                continue
            if len(values) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {reader.line_num}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(values)}"
                )
            record_id, system, day, code, name, description, amount = values
            try:
                posted = date.fromisoformat(day)
                value = Decimal(amount)
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
            if not value.is_finite():
                raise LedgerParseError(f"{source.name} line {reader.line_num}: amount {amount!r} is not a number")
            records.append(Record(record_id, system, posted, code, name, description, value))
    return records
