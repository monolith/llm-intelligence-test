"""The normalized records file: writing it, and reading it back.

The file is comma separated, with :data:`~ledgerkit.core.records.RECORD_COLUMNS`
as its header line.  Descriptions are quoted where the CSV format needs it and
otherwise written exactly as the source system wrote them.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.core.values import parse_date, parse_decimal
from ledgerkit.log import get_logger

_log = get_logger(__name__)

ISO_DATE_FORMAT = "%Y-%m-%d"


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
        try:
            header = next(reader, None)
            if header is None or tuple(header) != RECORD_COLUMNS:
                raise LedgerParseError(f"{source.name}: header is not {','.join(RECORD_COLUMNS)}")
            for row in reader:
                if not row:
                    continue
                where = f"{source.name} line {reader.line_num}"
                if len(row) != len(RECORD_COLUMNS):
                    raise LedgerParseError(
                        f"{where}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}"
                    )
                record_id, system, posted, code, name, description, amount = row
                records.append(
                    Record(
                        record_id=record_id,
                        source_system=system,
                        date=parse_date(posted, ISO_DATE_FORMAT, f"{where}: date"),
                        account_code=code,
                        account_name=name,
                        description=description,
                        amount=parse_decimal(amount, f"{where}: amount"),
                    )
                )
        except csv.Error as exc:
            raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
