"""Checking export files row by row, without writing anything.

A row is rejected when its field count does not match its header, when its date
cannot be read the way its system writes dates, when its amount is not a number,
or when its account code does not match the ``[validate] account_code_pattern``
setting.  Each rejected row gets one ``WARNING`` through the project logger
naming the file, the line and what was wrong, and checking carries on to the end
of every file.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import ExportReader, detect_system, reader_for

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """What one validation run found."""

    checked: int
    rejected: int
    unreadable: int

    @property
    def passed(self) -> bool:
        """True when every file could be read and every row in them passed."""
        return self.rejected == 0 and self.unreadable == 0


def row_problems(
    reader: ExportReader,
    header: list[str],
    values: list[str],
    account_pattern: re.Pattern[str],
) -> list[str]:
    """Everything wrong with one data row; an empty list when it passes."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
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
    if account_pattern.search(code) is None:
        problems.append(f"account code {code!r} does not match {account_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export; return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError`, :class:`OSError` or :class:`UnicodeError`
    when the file cannot be read at all.
    """
    source = Path(path)
    reader = reader_for(detect_system(source))
    header, lines = reader.read_lines(source)
    rejected = 0
    for number, values in lines:
        problems = row_problems(reader, header, values, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(lines), rejected


def validate_files(paths: Iterable[Path], account_pattern: re.Pattern[str]) -> ValidationResult:
    """Check every row of every file, carrying on past bad rows and bad files."""
    checked = rejected = unreadable = 0
    for path in paths:
        try:
            file_checked, file_rejected = validate_file(path, account_pattern)
        except (LedgerParseError, OSError, UnicodeError) as exc:
            _log.error("%s: cannot be read: %s", path, exc)
            unreadable += 1
            continue
        checked += file_checked
        rejected += file_rejected
    return ValidationResult(checked=checked, rejected=rejected, unreadable=unreadable)
