"""Reading and writing the normalized records file.

``ingest`` writes it; ``report`` and ``reconcile`` read it.  It is a plain comma
separated file with :data:`~ledgerkit.core.records.RECORD_COLUMNS` as its header
and no preamble or trailer, so unlike the exports it can be handed to the
standard library ``csv`` module whole, quoting included.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record, parse_decimal
from ledgerkit.log import get_logger

_log = get_logger(__name__)

LINE_TERMINATOR = "\n"


def write_normalized(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` in the order given and return how many were written.

    Parent directories are created when they do not exist.  A description that
    holds a comma, a quote or a line break is quoted as the CSV format requires.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator=LINE_TERMINATOR)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
            count += 1
    _log.info("wrote %d record(s) to %s", count, target)
    return count


def read_normalized(path: Path) -> list[Record]:
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: first line is not the normalized header")
        for row in reader:
            if not row:
                continue
            number = reader.line_num
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(row)}"
                )
            record_id, system, posted, code, name, description, amount = row
            try:
                posted_on = date.fromisoformat(posted)
                value = parse_decimal(amount, "amount")
            except ValueError as exc:
                raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
            records.append(
                Record(
                    record_id=record_id,
                    source_system=system,
                    date=posted_on,
                    account_code=code,
                    account_name=name,
                    description=description,
                    amount=value,
                )
            )
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
