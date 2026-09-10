"""Check export files for malformed rows without writing anything.

A row is rejected when it has the wrong number of fields for its header, when its
date is not in the format its system writes, when its amount is not a number the
way its system writes one, or when its account code does not match the
``[validate] account_code_pattern`` setting.  Every rejected row gets one warning
through the project logger, naming the file, the line number and what was wrong.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, parser_for, required_columns

_log = get_logger(__name__)


def validate_file(path: Path, account_code_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    source = Path(path)
    parser = parser_for(detect_system(source))
    header, lines = parser.split_lines(source)
    missing = [column for column in required_columns(parser) if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in lines:
        problems = _row_problems(parser, header, values, account_code_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(lines), rejected


def _row_problems(
    parser: ModuleType, header: list[str], values: list[str], pattern: re.Pattern[str]
) -> list[str]:
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    try:
        parser.parse_date(row[parser.DATE_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        parser.parse_amount(row[parser.AMOUNT_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[parser.ACCOUNT_COLUMN]
    if not pattern.search(code):
        problems.append(f"account code {code!r} does not match {pattern.pattern!r}")
    return problems
