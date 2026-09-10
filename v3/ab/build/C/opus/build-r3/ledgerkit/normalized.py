"""The normalized records file that ``ingest`` writes and ``report`` and ``reconcile`` read.

It is an ordinary comma separated file: one header line, exactly
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, then one line per posting, with
fields quoted where the CSV format requires it.  There is no preamble or trailer
to skip, so the standard library ``csv`` module reads and writes it whole.
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


def write_records(records: Iterable[Record], path: Path) -> int:
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


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != list(RECORD_COLUMNS):
            raise LedgerParseError(f"{source.name}: header is not {','.join(RECORD_COLUMNS)}")
        for row in reader:
            if not row:
                continue
            number = reader.line_num
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}"
                )
            record_id, system, raw_date, code, name, description, raw_amount = row
            try:
                posted = date.fromisoformat(raw_date)
                amount = values.parse_decimal(raw_amount)
            except ValueError as exc:
                raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
            records.append(
                Record(
                    record_id=record_id,
                    source_system=system,
                    date=posted,
                    account_code=code,
                    account_name=name,
                    description=description,
                    amount=amount,
                )
            )
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
