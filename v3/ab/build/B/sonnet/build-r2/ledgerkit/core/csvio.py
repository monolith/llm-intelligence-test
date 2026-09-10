"""Reading and writing the normalized records file that ``ingest`` produces and
that ``report`` and ``reconcile`` consume.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_records(path: Path, records: list[Record]) -> None:
    """Write ``records`` to ``path`` as the comma separated normalized file."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` objects."""
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        raise LedgerParseError(f"{source.name}: empty records file")

    header = fields.split_record(lines[0])
    if tuple(header) != RECORD_COLUMNS:
        raise LedgerParseError(f"{source.name}: unexpected header {header!r}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        values = fields.split_record(line)
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        row = dict(zip(header, values, strict=True))
        try:
            record = Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
        except (ValueError, InvalidOperation) as exc:
            raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
        records.append(record)
    return records
