"""Merging exports from any of the three systems into one normalized file."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_READERS = {"A": system_a, "B": system_b, "C": system_c}


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file and build its (not yet cleaned or ordered) records."""
    source = Path(path)
    system = detect_system(source)
    module = _READERS[system]
    rows = module.read_rows(source)
    records = [module.to_record(row, unknown_label=unknown_label) for row in rows]
    _log.info("built %d record(s) from %s", len(records), source.name)
    return records


def build_records(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Read every export in ``paths`` and merge them into one ordered list of records.

    Every posting is kept, refunds included; the result is cleaned and ordered
    by :func:`~ledgerkit.core.normalize.normalize`.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(read_records(Path(path), unknown_label))
    return normalize(records, keep_refunds=True)
