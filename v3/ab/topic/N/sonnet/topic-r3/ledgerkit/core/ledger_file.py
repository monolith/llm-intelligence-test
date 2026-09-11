"""Reading and writing the one normalized ledger file the CLI passes around.

``ingest`` writes this file; ``report`` and ``reconcile`` read it back.  It is
its own small format -- comma separated, quoted where :mod:`ledgerkit.core.fields`
says a field needs it -- so reading and writing it live together here rather
than in either command.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_records(path: Path, records: list[Record]) -> int:
    """Write ``records`` to ``path`` as the normalized CSV.  Returns the row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(records)


def read_records(path: Path) -> list[Record]:
    """Read a normalized ledger file back into :class:`Record` values."""
    source = Path(path)
    lines = [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        raise LedgerParseError(f"{source.name}: empty file")

    header = fields.split_record(lines[0])
    if tuple(header) != RECORD_COLUMNS:
        raise LedgerParseError(f"{source.name}: unexpected header {header!r}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        values = fields.split_record(line)
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
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
