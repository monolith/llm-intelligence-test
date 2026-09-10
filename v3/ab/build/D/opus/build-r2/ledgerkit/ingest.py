"""Turn export files from any of the three systems into normalized records.

Every posting in every file becomes one :class:`~ledgerkit.core.records.Record`.
Nothing is filtered, deduplicated or cleaned: the record id, account code and
description are carried over exactly as the source system wrote them.  That is
why this module does not go through :func:`ledgerkit.core.normalize.normalize`,
which drops refunds and collapses whitespace.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit import mapping
from ledgerkit.core.normalized import write_records
from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, parser_for, required_columns

_log = get_logger(__name__)


def records_from_export(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file, whichever system wrote it, into records in file order.

    ``unknown_label`` is the account name given to a code the account map does
    not know.
    """
    source = Path(path)
    system = detect_system(source)
    parser = parser_for(system)
    needed = required_columns(parser)
    records: list[Record] = []

    for row in parser.read_rows(source):
        missing = [column for column in needed if column not in row]
        if missing:
            raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")
        record_id = row[parser.ID_COLUMN]
        code = row[parser.ACCOUNT_COLUMN]
        try:
            posted = parser.parse_date(row[parser.DATE_COLUMN])
            amount = parser.parse_amount(row[parser.AMOUNT_COLUMN])
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} record {record_id}: {exc}") from exc
        records.append(
            Record(
                record_id=record_id,
                source_system=system,
                date=posted,
                account_code=code,
                account_name=mapping.account_name(code, unknown_label),
                description=row[parser.DESCRIPTION_COLUMN],
                amount=amount,
            )
        )

    _log.info("built %d record(s) from %s", len(records), source.name)
    return records


def ingest_files(paths: Iterable[Path], out: Path, unknown_label: str) -> int:
    """Merge the exports in ``paths`` into one normalized file at ``out``.

    Rows are written ordered by date, then source system, then record id.
    Returns the number of rows written.  Every file is read before anything is
    written, so a file that cannot be read leaves ``out`` untouched.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(records_from_export(path, unknown_label))
    records.sort(key=sort_key)
    return write_records(records, out)
