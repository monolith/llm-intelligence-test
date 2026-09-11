"""Merge exports from all three systems into one normalized set of records."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def read_records(path: Path, *, unknown_account_label: str) -> list[Record]:
    """Read one export file and return its postings as :class:`Record` values."""
    source = Path(path)
    system = detect_system(source)
    if system == "A":
        rows = system_a.read_rows(source)
        records = system_a.build_records(rows, unknown_account_label=unknown_account_label)
    elif system == "B":
        rows = system_b.read_rows(source)
        records = system_b.build_records(rows, unknown_account_label=unknown_account_label)
    else:
        rows = system_c.read_rows(source)
        records = system_c.build_records(rows, unknown_account_label=unknown_account_label)
    _log.info("built %d record(s) from %s", len(records), source.name)
    return records


def load_records(paths: Iterable[str | Path], *, unknown_account_label: str) -> list[Record]:
    """Read and normalize every posting across all given export files.

    Every posting is kept, refunds included, so the result reflects the whole
    ledger rather than a report view of it.
    """
    all_records: list[Record] = []
    for path in paths:
        all_records.extend(read_records(Path(path), unknown_account_label=unknown_account_label))
    return normalize(all_records, keep_refunds=True)
