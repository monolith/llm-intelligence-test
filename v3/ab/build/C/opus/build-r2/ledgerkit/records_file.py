"""The normalized records file that ``ingest`` writes and the reports read.

It is an ordinary comma separated file whose header is
:data:`~ledgerkit.core.records.RECORD_COLUMNS`.  Fields are quoted only where the
CSV format needs it, so a description comes back exactly as it went in.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEMS

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


def _parse_row(row: list[str]) -> Record:
    record_id, system, date_text, code, name, description, amount_text = row
    if system not in SYSTEMS:
        raise LedgerParseError(f"source_system {system!r} is not one of {', '.join(SYSTEMS)}")
    try:
        posted = date.fromisoformat(date_text)
    except ValueError as exc:
        raise LedgerParseError(f"date {date_text!r} is not an ISO date") from exc
    try:
        amount = Decimal(amount_text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {amount_text!r} is not a number") from exc
    if not amount.is_finite():
        raise LedgerParseError(f"amount {amount_text!r} is not a number")
    return Record(
        record_id=record_id,
        source_system=system,
        date=posted,
        account_code=code,
        account_name=name,
        description=description,
        amount=amount,
    )


def read_records_file(path: Path) -> list[Record]:
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header != list(RECORD_COLUMNS):
            raise LedgerParseError(f"{source}: not a normalized records file (header is {header!r})")
        for row in reader:
            if not row:
                continue
            if len(row) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source} line {reader.line_num}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(row)}"
                )
            try:
                records.append(_parse_row(row))
            except LedgerParseError as exc:
                raise LedgerParseError(f"{source} line {reader.line_num}: {exc}") from exc
    _log.info("read %d record(s) from %s", len(records), source)
    return records
