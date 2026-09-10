"""The normalized records file: written by ``ingest``, read by ``report`` and ``reconcile``.

It is a comma separated file with :data:`~ledgerkit.core.records.RECORD_COLUMNS`
as its header, ISO dates and two place dollar amounts.  Descriptions are quoted
where they contain the delimiter or a quote, following the same rules as
:mod:`ledgerkit.core.fields`.
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


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` in the order given and return how many were written.

    Parent directories are created when they are missing.
    """
    target = Path(path)
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines) + "\n")
    count = len(lines) - 1
    _log.info("wrote %d record(s) to %s", count, target)
    return count


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values."""
    source = Path(path)
    header: list[str] | None = None
    records: list[Record] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        values = fields.split_record(line)
        if header is None:
            header = values
            if tuple(header) != RECORD_COLUMNS:
                raise LedgerParseError(f"{source.name} line {number}: not a normalized records header")
            continue
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
            )
        row = dict(zip(RECORD_COLUMNS, values, strict=True))
        try:
            posted = date.fromisoformat(row["date"])
            amount = Decimal(row["amount"])
        except (ValueError, InvalidOperation) as exc:
            raise LedgerParseError(f"{source.name} line {number}: bad date or amount") from exc
        records.append(
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=posted,
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=amount,
            )
        )

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return records
