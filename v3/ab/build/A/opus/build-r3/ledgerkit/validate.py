"""Row by row checks on export files.

A row is rejected when its field count does not match its header, its date is
not in the format its system writes, its amount is not a number in the unit its
system writes, or its account code does not match the configured pattern.  Each
rejected row gets one warning through the project logger.
"""

from __future__ import annotations

import re
from pathlib import Path

from ledgerkit.build import LAYOUTS, parse_amount, parse_date
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import read_lines

_log = get_logger(__name__)


def row_problems(
    system: str, header: list[str], values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data line, or an empty list when it is fine."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    layout = LAYOUTS[system]
    problems: list[str] = []
    try:
        parse_date(system, row[layout.date_column])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        parse_amount(system, row[layout.amount_column])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[layout.account_column]
    if not account_pattern.search(code):
        problems.append(f"account code {code!r} does not match {account_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data line of one export and return ``(checked, rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    system, header, body = read_lines(path)
    missing = LAYOUTS[system].missing_columns(header)
    if missing:
        raise LedgerParseError(f"{Path(path).name}: header has no {', '.join(missing)} column")

    checked = 0
    rejected = 0
    for number, values in body:
        checked += 1
        problems = row_problems(system, header, values, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", path, number, "; ".join(problems))
    return checked, rejected
