"""Reading and writing the normalized records file ``ingest`` produces.

The file is always comma separated, with the header from
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, regardless of what delimiter a
command that reports on it chooses for its own output.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def write_records(records: list[Record], path: Path) -> None:
    """Write ``records`` as the normalized CSV ``ingest`` produces."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _log.info("wrote %d record(s) to %s", len(records), destination)


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
        row = fields.split_record(line)
        if len(row) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}"
            )
        record_id, source_system, date_text, account_code, name, description, amount_text = row
        try:
            parsed_date = date.fromisoformat(date_text)
        except ValueError as exc:
            raise LedgerParseError(f"{source.name} line {number}: bad date {date_text!r}") from exc
        try:
            amount = Decimal(amount_text)
        except InvalidOperation as exc:
            raise LedgerParseError(f"{source.name} line {number}: bad amount {amount_text!r}") from exc
        records.append(
            Record(
                record_id=record_id,
                source_system=source_system,
                date=parsed_date,
                account_code=account_code,
                account_name=name,
                description=description,
                amount=amount,
            )
        )
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records
