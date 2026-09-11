"""Readers for the three export formats, and the sniffer that picks between them.

Each reader exposes ``read_rows(path)`` and hands back a list of dictionaries of
**raw strings**, keyed by that system's own column names.  Readers do not convert
amounts or dates; they only get the file's shape right.  Turning raw strings into
:class:`~ledgerkit.core.records.Record` values is the caller's job, because each
system says those things differently and the caller is the one that knows which
system it is holding.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)

SYSTEMS: tuple[str, ...] = ("A", "B", "C")

MODULES: dict[str, ModuleType] = {"A": system_a, "B": system_b, "C": system_c}

__all__ = [
    "LedgerParseError",
    "MODULES",
    "SYSTEMS",
    "detect_system",
    "missing_columns",
    "read_records",
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
    if system == "A":
        return system_a.read_rows(path)
    if system == "B":
        return system_b.read_rows(path)
    return system_c.read_rows(path)


def missing_columns(header: Sequence[str], system: str) -> list[str]:
    """The columns a record needs that ``header`` does not have, for ``system``."""
    module = MODULES[system]
    needed = (
        module.ID_COLUMN,
        module.DATE_COLUMN,
        module.ACCOUNT_COLUMN,
        module.DESCRIPTION_COLUMN,
        module.AMOUNT_COLUMN,
    )
    return [column for column in needed if column not in header]


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Read an export of any of the three systems as :class:`Record` values.

    Dates and amounts are read the way the system that wrote the file writes
    them, so every record comes back with a :class:`datetime.date` and an amount
    in dollars.  ``unknown_label`` names accounts the account map does not know.
    Records come back in file order.
    """
    source = Path(path)
    system = detect_system(source)
    module = MODULES[system]
    rows = module.read_rows(source)
    if rows:
        missing = missing_columns(list(rows[0]), system)
        if missing:
            raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    records: list[Record] = []
    for row in rows:
        record_id = row[module.ID_COLUMN]
        try:
            posted = module.parse_date(row[module.DATE_COLUMN])
            amount = module.parse_amount(row[module.AMOUNT_COLUMN])
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} {record_id}: {exc}") from exc
        code = row[module.ACCOUNT_COLUMN].strip()
        records.append(
            Record(
                record_id=record_id,
                source_system=system,
                date=posted,
                account_code=code,
                account_name=account_name(code, unknown_label),
                description=row[module.DESCRIPTION_COLUMN],
                amount=amount,
            )
        )
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
