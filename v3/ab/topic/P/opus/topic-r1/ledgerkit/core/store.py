"""The normalized records file: written by ``ingest``, read by the reports.

It is a comma separated file whose header is
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, one
:class:`~ledgerkit.core.records.Record` per row, with fields quoted where the
CSV format needs it.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.core.values import parse_decimal, parse_iso_date
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` and return how many rows were written.

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
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(
                f"{source.name}: header is not {','.join(RECORD_COLUMNS)}; is this an ingest output?"
            )
        for row in reader:
            if not row:
                continue
            records.append(_record_from_row(row, f"{source.name} line {reader.line_num}"))
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records


def _record_from_row(row: list[str], where: str) -> Record:
    if len(row) != len(RECORD_COLUMNS):
        raise LedgerParseError(f"{where}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}")
    record_id, source_system, posted, account_code, account_name, description, amount = row
    try:
        return Record(
            record_id=record_id,
            source_system=source_system,
            date=parse_iso_date(posted),
            account_code=account_code,
            account_name=account_name,
            description=description,
            amount=parse_decimal(amount),
        )
    except LedgerParseError as exc:
        raise LedgerParseError(f"{where}: {exc}") from exc
