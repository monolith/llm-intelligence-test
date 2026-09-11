"""Readers for the three export formats, and the sniffer that picks between them.

Each reader exposes ``read_rows(path)`` and hands back a list of dictionaries of
**raw strings**, keyed by that system's own column names.  Readers do not convert
amounts or dates; they only get the file's shape right.  Turning raw strings into
:class:`~ledgerkit.core.records.Record` values is the caller's job, because each
system says those things differently and the caller is the one that knows which
system it is holding.

That caller is the reader module's own ``to_record``, ``parse_date`` and
``parse_amount``: each system module is the one place that knows how its system
writes a date and what unit its amounts are in.  :func:`reader_for` hands back
the module for a system letter, typed as :class:`ExportReader`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)

SYSTEMS: tuple[str, ...] = ("A", "B", "C")

__all__ = [
    "ExportReader",
    "LedgerParseError",
    "SYSTEMS",
    "detect_system",
    "read_rows",
    "reader_for",
    "system_a",
    "system_b",
    "system_c",
]


class ExportReader(Protocol):
    """What every system module offers: the file's shape, and its values."""

    SYSTEM_LETTER: str
    COLUMNS: tuple[str, ...]
    ID_COLUMN: str
    DATE_COLUMN: str
    ACCOUNT_COLUMN: str
    AMOUNT_COLUMN: str

    def read_lines(self, path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]: ...

    def read_rows(self, path: Path) -> list[dict[str, str]]: ...

    def parse_date(self, raw: str) -> date: ...

    def parse_amount(self, raw: str) -> Decimal: ...

    def to_record(self, row: dict[str, str], unknown_label: str) -> Record: ...


_READERS: dict[str, ExportReader] = {"A": system_a, "B": system_b, "C": system_c}


def reader_for(system: str) -> ExportReader:
    """Return the reader module for system letter ``system``."""
    try:
        return _READERS[system]
    except KeyError:
        raise LedgerParseError(f"no reader for system {system!r}") from None


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


def read_rows(path: Path) -> list[dict[str, str]]:
    """Detect the system that wrote ``path`` and read its rows."""
    system = detect_system(path)
    _log.info("reading %s as system %s", Path(path).name, system)
    if system == "A":
        return system_a.read_rows(path)
    if system == "B":
        return system_b.read_rows(path)
    return system_c.read_rows(path)


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
