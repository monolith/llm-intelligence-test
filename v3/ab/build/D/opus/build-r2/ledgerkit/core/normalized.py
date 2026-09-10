"""Writing and reading the normalized records file.

The normalized file is comma separated, starts with a header line naming
:data:`~ledgerkit.core.records.RECORD_COLUMNS`, and holds one posting per line.
A field that contains the delimiter or a quote is quoted, with any quote inside
it written twice, by :func:`~ledgerkit.core.fields.join_record`.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.fields import join_record, split_record
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write ``records`` to ``path`` in the order given and return how many were written.

    Parent directories are created if they do not exist.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(join_record(list(RECORD_COLUMNS)) + "\n")
        for record in records:
            handle.write(join_record(record.to_row()) + "\n")
            count += 1
    _log.info("wrote %d record(s) to %s", count, target)
    return count


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` values, in file order."""
    source = Path(path)
    header: list[str] | None = None
    records: list[Record] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = split_record(line)
            if header != list(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {number}: not a normalized records header"
                )
            continue

        values = split_record(line)
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
            )
        record_id, system, raw_date, code, name, description, raw_amount = values
        try:
            posted = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise LedgerParseError(f"{source.name} line {number}: bad date {raw_date!r}") from exc
        try:
            amount = Decimal(raw_amount)
        except InvalidOperation as exc:
            raise LedgerParseError(f"{source.name} line {number}: bad amount {raw_amount!r}") from exc
        records.append(
            Record(
                record_id=record_id,
                source_system=system,
                date=posted,
                account_code=code,
                account_name=name,
                description=description,
                amount=amount,
            )
        )

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return records
