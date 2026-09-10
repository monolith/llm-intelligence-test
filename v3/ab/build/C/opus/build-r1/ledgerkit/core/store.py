"""The normalized records file that ``ingest`` writes and the reports read.

The file is comma separated, with a header line of
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, one posting per line.  A field
that contains the delimiter or a quote character is quoted, with any quote inside
it doubled, so description text survives the round trip exactly.
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
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(
                f"{source.name}: header is not {','.join(RECORD_COLUMNS)}"
            )
        for row in reader:
            if not row:
                continue
            number = reader.line_num
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(row)}"
                )
            values = dict(zip(RECORD_COLUMNS, row, strict=True))
            try:
                posted = date.fromisoformat(values["date"])
                amount = Decimal(values["amount"])
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
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
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
