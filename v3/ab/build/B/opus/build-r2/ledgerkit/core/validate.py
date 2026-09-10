"""Row checks for the ``validate`` command.

A row is rejected when its field count does not match its header, when its date
or amount cannot be read the way its system writes them, or when its account
code does not match the configured pattern.  Each rejected row gets one warning
through the project logger; nothing is printed here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import MODULES_BY_SYSTEM, detect_system

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """How many rows of one file were checked, and how many of them were rejected."""

    checked: int
    rejected: int


def row_problems(
    system: str, header: list[str], parts: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Return what is wrong with one data row, or an empty list when nothing is."""
    if len(parts) != len(header):
        return [f"expected {len(header)} fields, found {len(parts)}"]

    module = MODULES_BY_SYSTEM[system]
    row = dict(zip(header, parts, strict=True))
    problems: list[str] = []
    try:
        module.parse_date(row[module.DATE_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        module.parse_amount(row[module.AMOUNT_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[module.ACCOUNT_COLUMN]
    if not account_pattern.search(code):
        problems.append(f"account code {code!r} does not match {account_pattern.pattern}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> ValidationResult:
    """Check every data row of one export.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read at all, for example when it is not one of the three formats.
    """
    source = Path(path)
    system = detect_system(source)
    header, lines = MODULES_BY_SYSTEM[system].read_lines(source)
    rejected = 0
    for number, parts in lines:
        problems = row_problems(system, header, parts, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d rejected: %s", source, number, "; ".join(problems))
    return ValidationResult(checked=len(lines), rejected=rejected)
