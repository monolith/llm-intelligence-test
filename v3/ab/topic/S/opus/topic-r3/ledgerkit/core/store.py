"""The normalized records file: what ``ingest`` writes and ``report`` and ``reconcile`` read.

It is a comma separated file whose header is exactly :data:`RECORD_COLUMNS`, one
row per :class:`Record`, quoted only where a field needs it.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.core.values import read_date, read_dollars

ISO_DATE_FORMAT = "%Y-%m-%d"


def write_normalized(records: Iterable[Record], path: Path) -> int:
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


def read_normalized(path: Path) -> list[Record]:
    """Read a file :func:`write_normalized` wrote, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader, None)
            if header is None or tuple(header) != RECORD_COLUMNS:
                raise LedgerParseError(
                    f"{source.name}: first line is not the header {','.join(RECORD_COLUMNS)}"
                )
            for row in reader:
                if not row:
                    continue
                records.append(_to_record(row, f"{source.name} line {reader.line_num}"))
        except csv.Error as exc:
            raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
    return records


def _to_record(row: list[str], where: str) -> Record:
    if len(row) != len(RECORD_COLUMNS):
        raise LedgerParseError(f"{where}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}")
    record_id, source_system, day, account_code, account_name, description, amount = row
    try:
        return Record(
            record_id=record_id,
            source_system=source_system,
            date=read_date(day, ISO_DATE_FORMAT, "YYYY-MM-DD"),
            account_code=account_code,
            account_name=account_name,
            description=description,
            amount=read_dollars(amount),
        )
    except LedgerParseError as exc:
        raise LedgerParseError(f"{where}: {exc}") from exc
