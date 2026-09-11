"""Reading and writing the normalized records file.

``ingest`` writes this file; ``report`` and ``reconcile`` read it back. The
format is the CSV described in ``SPEC.md``: the header in
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, one row per posting, quoted
where :mod:`ledgerkit.core.fields` says a field needs it.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def write_records(path: Path, records: list[Record]) -> int:
    """Write ``records`` as the normalized CSV at ``path``. Returns the row count written."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        handle.write(fields.join_record(list(RECORD_COLUMNS)) + "\n")
        for record in records:
            handle.write(fields.join_record(record.to_row()) + "\n")
    _log.info("wrote %d record(s) to %s", len(records), destination)
    return len(records)


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise LedgerParseError(f"{source.name}: empty file")

    header = fields.split_record(lines[0])
    if tuple(header) != RECORD_COLUMNS:
        raise LedgerParseError(f"{source.name}: unexpected header {header!r}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        values = fields.split_record(line)
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        row = dict(zip(header, values, strict=True))
        records.append(
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
        )
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
