"""Turning export files, from any mix of systems, into one ordered run of records.

Every posting in every file comes through.  Nothing is filtered, deduplicated or
summarized, so this deliberately does not go through
:func:`ledgerkit.core.normalize.normalize`, which drops refunds by default and
rewrites whitespace inside descriptions.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, reader_for

_log = get_logger(__name__)


def read_export(path: Path, unknown_label: str) -> list[Record]:
    """Read one export as records, whichever system wrote it."""
    source = Path(path)
    system = detect_system(source)
    reader = reader_for(system)
    records: list[Record] = []
    for row in reader.read_rows(source):
        try:
            records.append(reader.to_record(row, unknown_label))
        except LedgerParseError as exc:
            record_id = row.get(reader.ID_COLUMN, "?")
            raise LedgerParseError(f"{source.name} record {record_id}: {exc}") from exc
    _log.info("%s: %d record(s) from system %s", source.name, len(records), system)
    return records


def ingest_exports(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Every posting in ``paths``, ordered by date, then system, then record id."""
    records = [record for path in paths for record in read_export(path, unknown_label)]
    records.sort(key=sort_key)
    return records
