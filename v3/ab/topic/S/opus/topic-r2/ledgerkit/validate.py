"""Check export files row by row without writing anything.

A row is rejected when its field count does not match its header, its date is
not in the format its system writes, its amount cannot be read, or its account
code does not match the configured pattern.  Each rejected row gets one warning
through the project logger naming the file, the line and every problem found.

Amounts are read the way ingest reads them, so a Borough amount has to be a
whole number of cents: ``12.50`` in a Borough file is exactly the unit mistake
:func:`ledgerkit.parsers.system_b.to_major_units` exists to catch.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.formats import ExportFormat, format_for
from ledgerkit.log import get_logger

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """What a validation run found."""

    checked: int
    rejected: int
    unreadable: int

    def passed(self) -> bool:
        """True when every row passed and every file could be read."""
        return self.rejected == 0 and self.unreadable == 0


def row_problems(
    export: ExportFormat, header: list[str], values: list[str], account_code_pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data line; an empty list when it is fine."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    try:
        export.parse_date(row[export.date_column])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        export.parse_amount(row[export.amount_column])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[export.account_column]
    if not account_code_pattern.search(code):
        problems.append(f"account code {code!r} does not match {account_code_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_code_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data line of one export and return ``(checked, rejected)``.

    Raises when the file cannot be read at all: it is missing, it is not UTF-8,
    it is not an export of a known system, or its header lacks a needed column.
    """
    source = Path(path)
    export = format_for(source)
    header, lines = export.read_fields(source)
    missing = export.missing_columns(header)
    if missing:
        raise LedgerParseError(f"header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in lines:
        problems = row_problems(export, header, values, account_code_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(lines), rejected


def validate_files(paths: Iterable[Path], account_code_pattern: str) -> ValidationResult:
    """Check every row of every file, carrying on past bad rows and unreadable files.

    Raises :class:`re.error` when ``account_code_pattern`` is not a valid pattern.
    """
    pattern = re.compile(account_code_pattern)
    checked = rejected = unreadable = 0
    for path in paths:
        try:
            file_checked, file_rejected = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            unreadable += 1
            _log.warning("%s: cannot be read: %s", path, exc)
            continue
        checked += file_checked
        rejected += file_rejected
    return ValidationResult(checked=checked, rejected=rejected, unreadable=unreadable)
