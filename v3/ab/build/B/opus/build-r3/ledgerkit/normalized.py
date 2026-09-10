"""The normalized records file that ``ingest`` writes and ``report`` and
``reconcile`` read.

It is an ordinary comma separated file with the header in
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, and it has no preamble or
trailer, so the standard library ``csv`` module reads and writes it whole.
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

DEFAULT_RECORDS_PATH = Path("out") / "records.csv"


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write records to ``path``, creating parent directories, and return the row count."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
            count += 1
    _log.info("wrote %d row(s) to %s", count, target)
    return count


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into records."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file (bad header)")
        for row in reader:
            if not row:
                continue
            line = reader.line_num
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {line}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}"
                )
            values = dict(zip(RECORD_COLUMNS, row, strict=True))
            try:
                posted = date.fromisoformat(values["date"])
                amount = Decimal(values["amount"])
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {line}: {exc}") from exc
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
    _log.info("read %d record(s) from %s", len(records), source)
    return records
