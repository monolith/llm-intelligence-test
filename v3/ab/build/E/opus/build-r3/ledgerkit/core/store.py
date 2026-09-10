"""Reading and writing the normalized records file.

The normalized file is the one ``ingest`` writes and ``report`` and
``reconcile`` read: a comma separated file whose header is
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, one posting per line, quoted
where the CSV format requires it.  Lines end with ``\\n``, like the exports.
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


def _parse_row(values: list[str], where: str) -> Record:
    if len(values) != len(RECORD_COLUMNS):
        raise LedgerParseError(f"{where}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}")
    row = dict(zip(RECORD_COLUMNS, values, strict=True))
    try:
        posted = date.fromisoformat(row["date"])
    except ValueError as exc:
        raise LedgerParseError(f"{where}: date {row['date']!r} is not YYYY-MM-DD") from exc
    try:
        amount = Decimal(row["amount"])
    except InvalidOperation as exc:
        raise LedgerParseError(f"{where}: amount {row['amount']!r} is not a number") from exc
    if not amount.is_finite():
        raise LedgerParseError(f"{where}: amount {row['amount']!r} is not a number")
    return Record(
        record_id=row["record_id"],
        source_system=row["source_system"],
        date=posted,
        account_code=row["account_code"],
        account_name=row["account_name"],
        description=row["description"],
        amount=amount,
    )


def load_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source}: header is not {','.join(RECORD_COLUMNS)}")
        for values in reader:
            if not values:
                continue
            records.append(_parse_row(values, f"{source} line {reader.line_num}"))
    _log.info("read %d record(s) from %s", len(records), source)
    return records
