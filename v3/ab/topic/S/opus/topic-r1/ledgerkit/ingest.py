"""``ingest``: merge exports from any of the three systems into one ordered list of records.

Every posting in every file comes through.  Nothing is filtered, deduplicated or
tidied, which is why this does not go through
:func:`ledgerkit.core.normalize.normalize`: that drops refunds by default and
rewrites whitespace in descriptions, and the normalized file has to carry both
exactly as the source systems wrote them.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEM_MODULES, detect_system

_log = get_logger(__name__)


def read_export(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file, from whichever system wrote it, into records in file order.

    ``unknown_label`` is the account name given to a code the account map lacks.
    Raises :class:`LedgerParseError`, naming the file and line, for the first row
    that cannot be made into a record.
    """
    source = Path(path)
    try:
        system = detect_system(source)
        module = SYSTEM_MODULES[system]
        rows = module.read_numbered_rows(source)
    except UnicodeDecodeError as exc:
        raise LedgerParseError(f"{source}: not UTF-8 text ({exc.reason})") from exc

    records: list[Record] = []
    for number, row in rows:
        try:
            records.append(module.to_record(row, unknown_label))
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
        except KeyError as exc:
            raise LedgerParseError(
                f"{source.name} line {number}: the header has no {exc.args[0]!r} column"
            ) from exc
    _log.info("%s: %d record(s) from system %s", source.name, len(records), system)
    return records


def ingest_files(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Read every export in ``paths`` and return all of their records.

    Records come back ordered by date, then source system, then record id.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(read_export(path, unknown_label))
    records.sort(key=sort_key)
    return records
