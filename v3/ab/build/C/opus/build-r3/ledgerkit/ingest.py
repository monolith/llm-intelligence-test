"""Turn export files from any of the three systems into normalized records.

The readers hand back raw strings keyed by each system's own column names.  This
module is where those strings become :class:`~ledgerkit.core.records.Record`
values, using each system's own ``parse_date`` and ``parse_amount``: Borough
amounts are cents and Calder dates are day first, and the reader modules are the
only places that know it.

Nothing is filtered, deduplicated or cleaned up here.  The record id, account
code and description go into the record exactly as the source system wrote them.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, reader_for

_log = get_logger(__name__)


def record_from_row(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Build one record from one raw row written by ``system``."""
    reader = reader_for(system)
    try:
        record_id = row[reader.ID_COLUMN]
        raw_date = row[reader.DATE_COLUMN]
        code = row[reader.ACCOUNT_COLUMN]
        description = row[reader.DESCRIPTION_COLUMN]
        raw_amount = row[reader.AMOUNT_COLUMN]
    except KeyError as exc:
        raise LedgerParseError(f"no {exc.args[0]!r} column") from exc
    try:
        posted = reader.parse_date(raw_date)
        amount = reader.parse_amount(raw_amount)
    except LedgerParseError as exc:
        raise LedgerParseError(f"record {record_id}: {exc}") from exc
    return Record(
        record_id=record_id,
        source_system=system,
        date=posted,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=description,
        amount=amount,
    )


def records_from_export(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file, whichever system wrote it, into records in file order."""
    source = Path(path)
    system = detect_system(source)
    rows = reader_for(system).read_rows(source)
    try:
        return [record_from_row(system, row, unknown_label) for row in rows]
    except LedgerParseError as exc:
        raise LedgerParseError(f"{source.name}: {exc}") from exc


def ingest_exports(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Read every export in ``paths`` and return all their records in normalized order."""
    records: list[Record] = []
    for path in paths:
        records.extend(records_from_export(path, unknown_label))
    records.sort(key=sort_key)
    return records
