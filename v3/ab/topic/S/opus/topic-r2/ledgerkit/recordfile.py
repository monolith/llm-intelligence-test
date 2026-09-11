"""Writing and reading the normalized records file.

The file is comma separated with a :data:`~ledgerkit.core.records.RECORD_COLUMNS`
header, and goes through the standard library ``csv`` module in both directions
so a description holding commas or quotes survives the round trip exactly.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.core.values import date_from_text, decimal_from_text
from ledgerkit.parsers import SYSTEMS

DATE_FORMAT = "%Y-%m-%d"


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path``, creating parent directories, and return how many."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
            count += 1
    return count


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader, None)
            if header is None or tuple(header) != RECORD_COLUMNS:
                raise LedgerParseError(f"{source}: header is not {','.join(RECORD_COLUMNS)}")
            for row in reader:
                if not row:
                    continue
                records.append(_record_from_row(row, source, reader.line_num))
        except csv.Error as exc:
            raise LedgerParseError(f"{source} line {reader.line_num}: {exc}") from exc
    return records


def _record_from_row(row: list[str], source: Path, line: int) -> Record:
    if len(row) != len(RECORD_COLUMNS):
        raise LedgerParseError(f"{source} line {line}: expected {len(RECORD_COLUMNS)} fields, found {len(row)}")
    record_id, system, day, code, name, description, amount = row
    if system not in SYSTEMS:
        raise LedgerParseError(f"{source} line {line}: source_system {system!r} is not one of {', '.join(SYSTEMS)}")
    try:
        return Record(
            record_id=record_id,
            source_system=system,
            date=date_from_text(day, DATE_FORMAT),
            account_code=code,
            account_name=name,
            description=description,
            amount=decimal_from_text(amount),
        )
    except LedgerParseError as exc:
        raise LedgerParseError(f"{source} line {line}: {exc}") from exc
