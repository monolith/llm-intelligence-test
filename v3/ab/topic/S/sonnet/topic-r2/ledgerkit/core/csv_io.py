"""Reading and writing the package's one normalized CSV shape.

This is the file :mod:`ledgerkit.ingest` writes and :mod:`ledgerkit.report` and
:mod:`ledgerkit.reconcile` read back.  It uses the same quote-aware splitting and
joining as the export readers, so a description that contains a comma or a quote
round-trips exactly.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, Record


def read_records(path: Path) -> list[dict[str, str]]:
    """Read a normalized records file back into raw string rows keyed by column name."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines:
        return []
    header = fields.split_record(lines[0])
    rows: list[dict[str, str]] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        rows.append(dict(zip(header, fields.split_record(line), strict=True)))
    return rows


def render_records(records: Iterable[Record]) -> str:
    """Render normalized records as the ingest output CSV, header included."""
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    return "\n".join(lines) + "\n"


def write_records(records: list[Record], path: Path) -> int:
    """Write ``records`` to ``path`` as the normalized CSV. Returns the row count written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_records(records), encoding="utf-8")
    return len(records)
