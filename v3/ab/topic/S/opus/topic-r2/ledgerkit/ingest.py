"""Turn export files from any of the three systems into normalized records.

Every posting in every file becomes one :class:`~ledgerkit.core.records.Record`.
Nothing is filtered, deduplicated or summarized, and the id, account code and
description are kept exactly as the source system wrote them, which is why this
does not go through :func:`ledgerkit.core.normalize.normalize`: that drops
refunds by default and collapses whitespace inside descriptions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.formats import ExportFormat, format_for
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)


def record_from_row(export: ExportFormat, row: Mapping[str, str], unknown_label: str) -> Record:
    """Build one record out of one raw row of ``export``'s system."""
    code = row[export.account_column]
    return Record(
        record_id=row[export.id_column],
        source_system=export.system,
        date=export.parse_date(row[export.date_column]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[export.description_column],
        amount=export.parse_amount(row[export.amount_column]),
    )


def read_export(path: Path, unknown_label: str) -> list[Record]:
    """Every posting in one export file, in file order.

    Raises :class:`~ledgerkit.core.records.LedgerParseError` on the first row
    that cannot be turned into a record, naming the file and the row's id.
    """
    source = Path(path)
    export = format_for(source)
    rows = export.read_rows(source)
    if rows:
        missing = export.missing_columns(rows[0])
        if missing:
            raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    records: list[Record] = []
    for row in rows:
        try:
            records.append(record_from_row(export, row, unknown_label))
        except LedgerParseError as exc:
            raise LedgerParseError(
                f"{source.name} {export.id_column} {row[export.id_column]!r}: {exc}"
            ) from exc
    _log.info("%s: %d posting(s) from system %s", source.name, len(records), export.system)
    return records


def read_exports(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Every posting in every export, ordered by date, then system, then record id."""
    records: list[Record] = []
    for path in paths:
        records.extend(read_export(path, unknown_label))
    records.sort(key=sort_key)
    return records
