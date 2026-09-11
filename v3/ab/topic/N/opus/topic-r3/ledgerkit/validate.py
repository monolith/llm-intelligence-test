"""Checking export files row by row without writing anything.

A row is rejected when it has the wrong number of fields for its header, when its
date is not a date in the form its system writes, when its amount is not a number
in the form its system writes (Borough: whole cents), or when its account code
does not match the configured pattern.  Each rejected row gets one ``WARNING``
naming the file, the line number and every problem found on it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import MODULES, detect_system, missing_columns

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """How many rows one file had, and how many of them were rejected."""

    checked: int
    rejected: int


def _row_problems(
    module: ModuleType, header: list[str], row_values: list[str], pattern: re.Pattern[str]
) -> list[str]:
    if len(row_values) != len(header):
        return [f"expected {len(header)} fields, found {len(row_values)}"]
    row = dict(zip(header, row_values, strict=True))
    problems: list[str] = []
    try:
        module.parse_date(row[module.DATE_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        module.parse_amount(row[module.AMOUNT_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[module.ACCOUNT_COLUMN].strip()
    if not pattern.search(code):
        problems.append(f"account code {code!r} does not match {pattern.pattern}")
    return problems


def validate_file(path: Path, account_code_pattern: re.Pattern[str]) -> ValidationResult:
    """Check every data row of one export and log a warning for each rejected row.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    source = Path(path)
    system = detect_system(source)
    module = MODULES[system]
    header, lines = module.numbered_lines(source)
    missing = missing_columns(header, system)
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, row_values in lines:
        problems = _row_problems(module, header, row_values, account_code_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d rejected: %s", source, number, "; ".join(problems))
    return ValidationResult(checked=len(lines), rejected=rejected)
