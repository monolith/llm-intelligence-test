"""Merge export files from any of the three systems into one normalized file.

See ``SPEC.md``, section 1, for the command this implements.
"""

from __future__ import annotations

from pathlib import Path

from ledgerkit.core.convert import to_record
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record, write_normalized
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_READERS = {"A": system_a.read_rows, "B": system_b.read_rows, "C": system_c.read_rows}


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file and turn every row in it into a :class:`Record`."""
    system = detect_system(path)
    raw_rows = _READERS[system](path)
    return [to_record(system, row, unknown_label) for row in raw_rows]


def merge(records: list[Record]) -> list[Record]:
    """Normalize a run of records for output, keeping refunds.

    Every posting is meant to appear in ``ingest``'s output, so this always
    passes ``keep_refunds=True``, unlike :func:`~ledgerkit.report`'s default.
    """
    return normalize(records, keep_refunds=True)


def write(records: list[Record], out_path: Path) -> int:
    """Write ``records`` to ``out_path`` and return how many rows were written."""
    write_normalized(records, out_path)
    return len(records)
