"""Reading and writing the normalized records file.

``ingest`` writes it; ``report`` and ``reconcile`` read it back.  It is a comma
separated file with a :data:`~ledgerkit.core.records.RECORD_COLUMNS` header, one
posting per line, quoted with :func:`~ledgerkit.core.fields.join_record` where a
field needs it.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

HEADER_LINE = ",".join(RECORD_COLUMNS)


def write_records_file(path: Path, records: Iterable[Record]) -> int:
    """Write ``records`` to ``path`` in the order given and return how many were written.

    Parent directories are created when they do not exist.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(HEADER_LINE + "\n")
        for record in records:
            handle.write(fields.join_record(record.to_row()) + "\n")
            count += 1
    _log.info("wrote %d record(s) to %s", count, target)
    return count


def _parse_line(source: Path, number: int, line: str) -> Record:
    values = fields.split_record(line)
    if len(values) != len(RECORD_COLUMNS):
        raise LedgerParseError(
            f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
        )
    row = dict(zip(RECORD_COLUMNS, values, strict=True))
    try:
        posted = date.fromisoformat(row["date"])
        amount = Decimal(row["amount"])
    except (ValueError, InvalidOperation) as exc:
        raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
    return Record(
        record_id=row["record_id"],
        source_system=row["source_system"],
        date=posted,
        account_code=row["account_code"],
        account_name=row["account_name"],
        description=row["description"],
        amount=amount,
    )


def read_records_file(path: Path) -> list[Record]:
    """Read a normalized records file written by :func:`write_records_file`."""
    source = Path(path)
    records: list[Record] = []
    seen_header = False
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if not seen_header:
            if line != HEADER_LINE:
                raise LedgerParseError(f"{source.name} line {number}: not a normalized records header")
            seen_header = True
            continue
        records.append(_parse_line(source, number, line))
    if not seen_header:
        raise LedgerParseError(f"{source.name}: no header row")
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
