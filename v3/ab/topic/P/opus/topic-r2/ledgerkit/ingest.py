"""Turn export files from any of the three systems into normalized records.

This is where raw reader output becomes :class:`~ledgerkit.core.records.Record`
values.  Which column holds what, and how its date and amount are written, comes
from the system's own reader module; nothing here knows any one system's format.
Every row becomes a record: nothing is filtered, deduplicated or cleaned up.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import SYSTEM_MODULES, detect_system, read_rows

_log = get_logger(__name__)


def record_from_row(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Build one record from one raw row written by ``system``.

    A code the account map does not know is named ``unknown_label``.
    """
    module = SYSTEM_MODULES[system]
    code = row[module.ACCOUNT_COLUMN]
    return Record(
        record_id=row[module.ID_COLUMN],
        source_system=system,
        date=module.parse_date(row[module.DATE_COLUMN]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[module.DESCRIPTION_COLUMN],
        amount=module.parse_amount(row[module.AMOUNT_COLUMN]),
    )


def records_from_export(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file, from whichever system wrote it, as records in file order."""
    source = Path(path)
    system = detect_system(source)
    records: list[Record] = []
    for row in read_rows(source):
        try:
            records.append(record_from_row(system, row, unknown_label))
        except KeyError as exc:
            raise LedgerParseError(f"{source.name}: no {exc.args[0]!r} column") from exc
        except LedgerParseError as exc:
            record_id = row.get(SYSTEM_MODULES[system].ID_COLUMN, "?")
            raise LedgerParseError(f"{source.name} record {record_id}: {exc}") from exc
    return records


def records_from_exports(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Read every export named, in any order and mixture, into one sorted list.

    Records are ordered by date, then source system, then record id.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(records_from_export(path, unknown_label))
    records.sort(key=sort_key)
    return records
