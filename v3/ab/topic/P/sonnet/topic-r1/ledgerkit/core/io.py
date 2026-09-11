"""Reading and writing the normalized records file every command but ``ingest`` reads.

``ingest`` is the only command that writes this file; ``report`` and
``reconcile`` only read it back.  Both directions go through
:mod:`ledgerkit.core.fields` so a quoted, comma-bearing description round trips
exactly, the same way the three export readers already handle quoting.
"""

from __future__ import annotations

from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record


def write_records(path: Path, records: list[Record]) -> None:
    """Write ``records`` to ``path`` as the normalized CSV, creating parent directories."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    lines = [",".join(RECORD_COLUMNS)]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_records(path: Path) -> list[Record]:
    """Read a normalized CSV written by :func:`write_records` back into records."""
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
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
            )
        records.append(Record.from_row(values))
    return records
