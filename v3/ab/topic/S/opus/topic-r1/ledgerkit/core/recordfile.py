"""The normalized records file: what ``ingest`` writes and ``report`` and ``reconcile`` read.

It is comma separated, starts with the :data:`~ledgerkit.core.records.RECORD_COLUMNS`
header line, and quotes a field only where the format needs it, by the rules in
:mod:`ledgerkit.core.fields`.  A description that holds the delimiter or a quote
character therefore comes back out exactly as it went in.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, SOURCE_SYSTEMS, LedgerParseError, Record
from ledgerkit.core.values import read_date, read_dollars
from ledgerkit.log import get_logger

_log = get_logger(__name__)

ISO_DATE_FORMAT = "%Y-%m-%d"


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` in the order given and return how many there were.

    Parent directories are created if they do not exist.
    """
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    count = len(lines) - 1
    _log.info("wrote %d record(s) to %s", count, target)
    return count


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into records, in file order."""
    source = Path(path)
    header_seen = False
    records: list[Record] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        values = fields.split_record(line)
        if not header_seen:
            if tuple(values) != RECORD_COLUMNS:
                raise LedgerParseError(f"{source.name} line {number}: not a normalized records header")
            header_seen = True
            continue
        records.append(_parse_record(values, source.name, number))

    if not header_seen:
        raise LedgerParseError(f"{source.name}: no header row")
    _log.info("read %d record(s) from %s", len(records), source.name)
    return records


def _parse_record(values: list[str], file_name: str, number: int) -> Record:
    if len(values) != len(RECORD_COLUMNS):
        raise LedgerParseError(
            f"{file_name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
        )
    record_id, system, day, code, name, description, amount = values
    if system not in SOURCE_SYSTEMS:
        raise LedgerParseError(f"{file_name} line {number}: source_system {system!r} is not A, B or C")
    try:
        return Record(
            record_id=record_id,
            source_system=system,
            date=read_date(day, ISO_DATE_FORMAT),
            account_code=code,
            account_name=name,
            description=description,
            amount=read_dollars(amount),
        )
    except LedgerParseError as exc:
        raise LedgerParseError(f"{file_name} line {number}: {exc}") from exc
