"""Readers for the three export formats, and the sniffer that picks between them.

Each reader exposes ``read_rows(path)`` and hands back a list of dictionaries of
**raw strings**, keyed by that system's own column names.  Readers do not convert
amounts or dates while reading; they only get the file's shape right.

Turning raw strings into :class:`~ledgerkit.core.records.Record` values happens
in the same module, in ``to_record(row, unknown_label)`` and the ``parse_date``
and ``parse_amount`` it uses, because each system says those things differently
and its own module is the one place that knows how.
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import SOURCE_SYSTEMS, LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)

SYSTEMS: tuple[str, ...] = SOURCE_SYSTEMS

SYSTEM_MODULES: dict[str, ModuleType] = {"A": system_a, "B": system_b, "C": system_c}

__all__ = [
    "LedgerParseError",
    "SYSTEMS",
    "SYSTEM_MODULES",
    "detect_system",
    "read_rows",
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


def read_rows(path: Path) -> list[dict[str, str]]:
    """Detect the system that wrote ``path`` and read its rows."""
    system = detect_system(path)
    _log.info("reading %s as system %s", Path(path).name, system)
    return SYSTEM_MODULES[system].read_rows(path)


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
