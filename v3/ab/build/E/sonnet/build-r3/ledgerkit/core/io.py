"""Reading and writing the normalized record file ``ingest`` produces.

The normalized file is always comma separated, with the exact header
:data:`~ledgerkit.core.records.RECORD_COLUMNS` spells out, regardless of what
separator ``report`` prints its own totals with.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record

HEADER_LINE = ",".join(RECORD_COLUMNS)


def write_records(records: list[Record], path: Path) -> None:
    """Write ``records`` as the normalized CSV, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [HEADER_LINE]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_records(path: Path) -> list[Record]:
    """Read a normalized CSV back into :class:`Record` values."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        raise LedgerParseError(f"{Path(path).name}: no header row")

    header = fields.split_record(lines[0])
    if tuple(header) != RECORD_COLUMNS:
        raise LedgerParseError(f"{Path(path).name}: unexpected header {header!r}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        values = fields.split_record(line)
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{Path(path).name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
            )
        row = dict(zip(RECORD_COLUMNS, values, strict=True))
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
    return records
