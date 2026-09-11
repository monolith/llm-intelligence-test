"""``ingest`` — merge exports from any of the three systems into one file.

Every posting is kept, refunds included; nothing here filters, deduplicates or
summarizes.  Field text coming out of a reader's ``to_record`` is written on
exactly as read, so a description's delimiter or quote characters survive
into the output unchanged.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core.records import RECORD_COLUMNS, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_READERS = {"A": system_a, "B": system_b, "C": system_c}


def read_records(path: Path, *, unknown_label: str) -> list[Record]:
    """Read one export file and return its postings as normalized records."""
    system = detect_system(path)
    module = _READERS[system]
    rows = module.read_rows(path)
    records = [module.to_record(row, unknown_label=unknown_label) for row in rows]
    _log.info("built %d record(s) from %s", len(records), path.name)
    return records


def build_records(paths: Sequence[Path], *, settings: Settings) -> list[Record]:
    """Read every export file named and return them as one ordered list.

    Ordering matches :func:`~ledgerkit.core.records.sort_key`: date, then
    source system, then record id.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(read_records(path, unknown_label=settings.unknown_account_label))
    records.sort(key=sort_key)
    return records


def write_records(records: Sequence[Record], path: Path) -> int:
    """Write ``records`` as the normalized CSV at ``path``. Returns the row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
    return len(records)
