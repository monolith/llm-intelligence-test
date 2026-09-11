"""The normalized records file that ``ingest`` writes and the reports read.

It is an ordinary comma separated file whose header is
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, one posting per row, amounts in
dollars with two places, dates in ISO form.  Unlike the exports it has no
preamble or trailer, so the standard library ``csv`` module reads and writes it
whole, quoting a description only where the format requires it.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from ledgerkit.core import values
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def write_records(path: Path, records: Iterable[Record]) -> int:
    """Write ``records`` to ``path`` in the order given and return how many were written.

    Parent directories are created if they do not exist.
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


def read_records_file(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file (header {header!r})")
        for row in reader:
            if not row:
                continue
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {reader.line_num}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(row)}"
                )
            record_id, system, posted, code, name, description, amount = row
            try:
                records.append(
                    Record(
                        record_id=record_id,
                        source_system=system,
                        date=date.fromisoformat(posted),
                        account_code=code,
                        account_name=name,
                        description=description,
                        amount=values.parse_decimal(amount),
                    )
                )
            except ValueError as exc:
                raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
    _log.info("read %d record(s) from %s", len(records), source)
    return records
