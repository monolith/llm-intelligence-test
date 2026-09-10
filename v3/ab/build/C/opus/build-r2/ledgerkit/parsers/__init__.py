"""Readers for the three export formats, and the sniffer that picks between them.

Each reader exposes ``read_rows(path)`` and hands back a list of dictionaries of
**raw strings**, keyed by that system's own column names.  Readers do not convert
amounts or dates; they only get the file's shape right.  Turning raw strings into
:class:`~ledgerkit.core.records.Record` values is the caller's job, because each
system says those things differently and the caller is the one that knows which
system it is holding.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)

SYSTEMS: tuple[str, ...] = ("A", "B", "C")

_READERS: dict[str, ModuleType] = {"A": system_a, "B": system_b, "C": system_c}

__all__ = [
    "LedgerParseError",
    "SYSTEMS",
    "detect_system",
    "missing_columns",
    "read_records",
    "read_rows",
    "reader_for",
    "system_a",
    "system_b",
    "system_c",
    "to_record",
]


def detect_system(path: Path) -> str:
    """Return ``"A"``, ``"B"`` or ``"C"`` for an export file.

    The three formats are told apart by their first line, which is the only part
    of them the three vendors never changed.
    """
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        first = handle.readline().rstrip("\r\n")

    if first.startswith(system_a.BANNER):
        return "A"
    if first.startswith(system_b.HEADER_PREFIX):
        return "B"
    if first.startswith(system_c.BANNER):
        return "C"
    raise LedgerParseError(f"{Path(path).name}: first line does not match any known export format")


def reader_for(system: str) -> ModuleType:
    """Return the reader module for system ``"A"``, ``"B"`` or ``"C"``."""
    try:
        return _READERS[system]
    except KeyError:
        raise LedgerParseError(f"no reader for system {system!r}") from None


def read_rows(path: Path) -> list[dict[str, str]]:
    """Detect the system that wrote ``path`` and read its rows."""
    system = detect_system(path)
    _log.info("reading %s as system %s", Path(path).name, system)
    return reader_for(system).read_rows(path)


def _record_columns(reader: ModuleType) -> tuple[str, ...]:
    return (
        reader.ID_COLUMN,
        reader.DATE_COLUMN,
        reader.ACCOUNT_COLUMN,
        reader.DESCRIPTION_COLUMN,
        reader.AMOUNT_COLUMN,
    )


def missing_columns(system: str, header: list[str]) -> list[str]:
    """The columns a record needs that ``header`` does not have."""
    return [column for column in _record_columns(reader_for(system)) if column not in header]


def to_record(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Build one :class:`Record` out of a raw row from ``system``.

    This is where each system's own way of writing a date and an amount is
    applied.  The record id, account code and description are kept exactly as the
    source system wrote them.
    """
    reader = reader_for(system)
    absent = [column for column in _record_columns(reader) if column not in row]
    if absent:
        raise LedgerParseError(f"row has no {', '.join(absent)} column")
    code = row[reader.ACCOUNT_COLUMN]
    return Record(
        record_id=row[reader.ID_COLUMN],
        source_system=system,
        date=reader.parse_date(row[reader.DATE_COLUMN]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[reader.DESCRIPTION_COLUMN],
        amount=reader.parse_amount(row[reader.AMOUNT_COLUMN]),
    )


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Detect the system that wrote ``path`` and read every posting in it as a record.

    Records come back in file order.  A row that cannot be made into a record
    stops the read with a :class:`LedgerParseError` naming the file and line.
    """
    source = Path(path)
    system = detect_system(source)
    _log.info("reading %s as system %s", source.name, system)
    records: list[Record] = []
    for number, row in reader_for(system).read_numbered_rows(source):
        try:
            records.append(to_record(system, row, unknown_label))
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} line {number}: {exc}") from exc
    return records


def count_data_lines(path: Path) -> int:
    """How many data lines an export holds, without parsing any of their fields."""
    system = detect_system(path)
    text = Path(path).read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if system == "A":
        body = [line for line in lines if not line.startswith(system_a.COMMENT_PREFIX)]
        return max(0, len(body) - 1)
    if system == "B":
        return max(0, len(lines) - 1)
    return max(0, len(lines) - 3)
