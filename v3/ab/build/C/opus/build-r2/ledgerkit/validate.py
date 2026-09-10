"""Checking export files row by row, for the ``validate`` command.

A row is rejected when it does not have as many fields as its header, when its
date is not in the format its system writes, when its amount is not a number, or
when its account code does not match the ``[validate] account_code_pattern``
setting.  Every rejected row gets one warning through the project logger; the
check carries on to the end of the file.
"""

from __future__ import annotations

import re
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, missing_columns, reader_for

_log = get_logger(__name__)


def row_problems(
    system: str, header: list[str], values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data row from ``system``; empty when it is fine."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]

    reader = reader_for(system)
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


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(checked, rejected)``.

    Raises :class:`LedgerParseError`, :class:`OSError` or
    :class:`UnicodeDecodeError` when the file cannot be read at all.
    """
    source = Path(path)
    system = detect_system(source)
    header, lines = reader_for(system).read_lines(source)
    absent = missing_columns(system, header)
    if absent:
        raise LedgerParseError(f"header has no {', '.join(absent)} column")

    rejected = 0
    for number, values in lines:
        problems = row_problems(system, header, values, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: rejected: %s", source, number, "; ".join(problems))
    _log.info("checked %d row(s) in %s, rejected %d", len(lines), source, rejected)
    return len(lines), rejected
