"""Readers for the three export formats, and the sniffer that picks between them.

Each reader exposes ``read_rows(path)`` and hands back a list of dictionaries of
**raw strings**, keyed by that system's own column names.  Readers do not convert
amounts or dates while reading; they only get the file's shape right.  Each reader
module also carries ``parse_date``, ``parse_amount`` and ``to_record``, which know
how that one system writes a date and an amount, and :func:`read_records` uses
them to turn raw rows into :class:`~ledgerkit.core.records.Record` values.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)

SYSTEMS: tuple[str, ...] = ("A", "B", "C")
READERS: dict[str, ModuleType] = {"A": system_a, "B": system_b, "C": system_c}

__all__ = [
    "LedgerParseError",
    "READERS",
    "SYSTEMS",
    "detect_system",
    "read_all_records",
    "read_records",
    "read_rows",
    "reader_for",
    "system_a",
    "system_b",
    "system_c",
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
    """Return the reader module for the system letter ``system``."""
    try:
        return READERS[system]
    except KeyError as exc:
        raise LedgerParseError(f"no reader for system {system!r}") from exc


def read_rows(path: Path) -> list[dict[str, str]]:
    """Detect the system that wrote ``path`` and read its rows."""
    system = detect_system(path)
    _log.info("reading %s as system %s", Path(path).name, system)
    if system == "A":
        return system_a.read_rows(path)
    if system == "B":
        return system_b.read_rows(path)
    return system_c.read_rows(path)


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Read one export, from whichever system wrote it, as records in file order.

    Amounts come back as dollars and dates as :class:`datetime.date`, however
    the source system wrote them.  Account codes the account map does not know
    are named ``unknown_label``.
    """
    source = Path(path)
    reader = reader_for(detect_system(source))
    _log.info("reading %s as system %s", source.name, reader.SYSTEM_LETTER)
    records: list[Record] = []
    for index, row in enumerate(reader.read_rows(source), start=1):
        try:
            records.append(reader.to_record(row, unknown_label))
        except KeyError as exc:
            raise LedgerParseError(f"{source.name}: header has no {exc.args[0]!r} column") from exc
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} data row {index}: {exc}") from exc
    return records


def read_all_records(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Read every export named and return all of their records in one list.

    Nothing is filtered, deduplicated or rewritten.  The list comes back in
    :func:`~ledgerkit.core.records.sort_key` order: date, system, record id.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(read_records(path, unknown_label))
    records.sort(key=sort_key)
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
