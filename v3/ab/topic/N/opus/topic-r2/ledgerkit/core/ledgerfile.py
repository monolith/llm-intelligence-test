"""Reading and writing the normalized records file.

The normalized file is an ordinary comma separated file whose header is
:data:`~ledgerkit.core.records.RECORD_COLUMNS`.  It has no preamble and no
trailer, so the standard library ``csv`` module reads and writes it whole, and
quotes descriptions that contain a delimiter or a quote character.
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
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file")
        for row in reader:
            if not row:
                continue
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {reader.line_num}: expected {len(RECORD_COLUMNS)} "
                    f"fields, found {len(row)}"
                )
            values = dict(zip(RECORD_COLUMNS, row, strict=True))
            try:
                records.append(
                    Record(
                        record_id=values["record_id"],
                        source_system=values["source_system"],
                        date=date.fromisoformat(values["date"]),
                        account_code=values["account_code"],
                        account_name=values["account_name"],
                        description=values["description"],
                        amount=Decimal(values["amount"]),
                    )
                )
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
    return records
