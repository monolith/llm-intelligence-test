"""Check export files without writing anything.

A row is rejected when it does not have as many fields as its header, when its
date cannot be read in the format its system writes, when its amount cannot be
read as a number, or when its account code does not match the
``[validate] account_code_pattern`` setting.  Each rejected row gets one
``WARNING`` through the project logger, naming the file and the line and listing
everything wrong with it, and checking carries on to the next row.

The date and amount checks use the same ``parse_date`` and ``parse_amount`` that
ingest uses, so a row that passes here is a row ingest can read.  For a Borough
file that means the amount has to be a whole number of cents.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, reader_for

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """What a validation run found across all of its files."""

    checked: int
    rejected: int
    unreadable: int

    @property
    def passed(self) -> bool:
        """True when every row passed and every file could be read."""
        return self.rejected == 0 and self.unreadable == 0


def row_problems(
    reader: ModuleType, header: list[str], values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data row; an empty list means the row passes."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    for column, parse in (
        (reader.DATE_COLUMN, reader.parse_date),
        (reader.AMOUNT_COLUMN, reader.parse_amount),
    ):
        try:
            parse(row[column])
        except LedgerParseError as exc:
            problems.append(str(exc))
    code = row[reader.ACCOUNT_COLUMN]
    if account_pattern.search(code) is None:
        problems.append(f"account code {code!r} does not match {account_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError`, :class:`OSError` or
    :class:`UnicodeDecodeError` when the file cannot be read at all.
    """
    source = Path(path)
    reader = reader_for(detect_system(source))
    header, body = reader.read_table(source)
    needed = (reader.DATE_COLUMN, reader.AMOUNT_COLUMN, reader.ACCOUNT_COLUMN)
    missing = [column for column in needed if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in body:
        problems = row_problems(reader, header, values, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(body), rejected


def validate_files(paths: Iterable[Path], account_pattern: re.Pattern[str]) -> ValidationResult:
    """Check every file named, carrying on past bad rows and unreadable files."""
    checked = rejected = unreadable = 0
    for path in paths:
        try:
            file_checked, file_rejected = validate_file(path, account_pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            unreadable += 1
            _log.error("cannot read %s: %s", path, exc)
            continue
        checked += file_checked
        rejected += file_rejected
    return ValidationResult(checked=checked, rejected=rejected, unreadable=unreadable)
