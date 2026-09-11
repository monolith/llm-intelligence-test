"""Row checks on export files, for ``python -m ledgerkit validate``.

A row is rejected when it has the wrong number of fields for its header, when
its date is not written the way its system writes dates, when its amount is not
a number in its system's terms, or when its account code does not match the
``[validate] account_code_pattern`` setting.  Each check uses the same reader
functions ``ingest`` uses, so a file that validates is a file that ingests.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, missing_columns, reader_for

_log = get_logger(__name__)


def row_problems(
    reader: ModuleType, header: list[str], values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """What is wrong with one data row; an empty list when nothing is."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]

    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    for column, parse in ((reader.DATE_COLUMN, reader.parse_date), (reader.AMOUNT_COLUMN, reader.parse_amount)):
        try:
            parse(row[column])
        except LedgerParseError as exc:
            problems.append(str(exc))
    code = row[reader.ACCOUNT_COLUMN]
    if account_pattern.fullmatch(code) is None:
        problems.append(f"account code {code!r} does not match {account_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(rows checked, rows rejected)``.

    Each rejected row is logged as one warning naming the file and the line.
    Raises :class:`OSError`, :class:`UnicodeDecodeError` or
    :class:`LedgerParseError` when the file cannot be read at all.
    """
    source = Path(path)
    reader = reader_for(detect_system(source))
    header, lines = reader.read_fields(source)
    missing = missing_columns(reader, header)
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in lines:
        problems = row_problems(reader, header, values, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(lines), rejected
