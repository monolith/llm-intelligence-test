"""Row by row checks on export files.

The readers stop at the first line they cannot shape and do not hand back line
numbers, so validation walks each export's data lines itself, through the
reader's ``read_lines``, and checks every one of them.  Each rejected row is one
``WARNING`` through the project logger.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import READERS, detect_system

_log = get_logger(__name__)


@dataclass(frozen=True)
class FileResult:
    """What validating one export found."""

    checked: int
    rejected: int


def row_problems(
    system: str, header: list[str], values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data line of an export from ``system``.

    An empty list means the row passed.
    """
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]

    reader = READERS[system]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    try:
        reader.parse_date(row[reader.DATE_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        reader.parse_amount(row[reader.AMOUNT_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[reader.ACCOUNT_COLUMN]
    if not account_pattern.search(code):
        problems.append(f"account code {code!r} does not match {account_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> FileResult:
    """Check every data line of one export and log a warning for each bad one.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    source = Path(path)
    system = detect_system(source)
    reader = READERS[system]
    header, lines = reader.read_lines(source)
    required = (reader.DATE_COLUMN, reader.AMOUNT_COLUMN, reader.ACCOUNT_COLUMN)
    missing = [column for column in required if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in lines:
        problems = row_problems(system, header, values, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return FileResult(checked=len(lines), rejected=rejected)
