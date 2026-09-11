"""Reading export files from any of the three systems into normalized records.

This is the library half of the ``ingest`` command.  It does not print or write
anything itself; :mod:`ledgerkit.cli` handles the output and the file write.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_READERS = {"A": system_a.read_rows, "B": system_b.read_rows, "C": system_c.read_rows}
_CONVERTERS = {"A": system_a.to_record, "B": system_b.to_record, "C": system_c.to_record}


def read_records(path: Path, unknown_account_label: str) -> list[Record]:
    """Read one export file, whichever of the three systems wrote it, into records."""
    source = Path(path)
    system = detect_system(source)
    _log.info("ingesting %s as system %s", source.name, system)
    rows = _READERS[system](source)
    to_record = _CONVERTERS[system]
    return [to_record(row, unknown_account_label) for row in rows]


def read_all(paths: Sequence[Path], unknown_account_label: str) -> list[Record]:
    """Read every export file named in ``paths`` into one list of records, file order preserved."""
    records: list[Record] = []
    for path in paths:
        records.extend(read_records(Path(path), unknown_account_label))
    return records


def write_csv(records: Sequence[Record], out_path: Path) -> None:
    """Write ``records`` to ``out_path`` as the normalized CSV, creating parent directories."""
    destination = Path(out_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
