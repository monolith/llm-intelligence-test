"""Row checks for the ``validate`` command.

A data row is rejected when any of these is true:

* it does not have as many fields as the file's header;
* its date field is not a date in the format its system writes;
* its amount field cannot be read as a number the way its system writes one
  (for Borough, that means a whole number of cents);
* its account code does not match the ``[validate] account_code_pattern`` setting.

Each rejected row gets one ``WARNING`` through the project logger, naming the
file and line number and every problem found on it.  Checking does not stop at
the first bad row.  Nothing is written anywhere.
"""

from __future__ import annotations

import re
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, reader_for

_log = get_logger(__name__)


def row_problems(
    system: str, header: list[str], parts: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Return what is wrong with one data row written by ``system``; empty when nothing is."""
    if len(parts) != len(header):
        return [f"expected {len(header)} fields, found {len(parts)}"]

    reader = reader_for(system)
    row = dict(zip(header, parts, strict=True))
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
        problems.append(f"account code {code!r} does not match {account_pattern.pattern}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError`, :class:`OSError` or
    :class:`UnicodeDecodeError` when the file cannot be read at all.
    """
    source = Path(path)
    system = detect_system(source)
    reader = reader_for(system)
    header, lines = reader.read_lines(source)
    needed = (reader.DATE_COLUMN, reader.AMOUNT_COLUMN, reader.ACCOUNT_COLUMN)
    missing = [column for column in needed if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, parts in lines:
        problems = row_problems(system, header, parts, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(lines), rejected
