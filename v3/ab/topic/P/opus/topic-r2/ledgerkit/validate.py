"""Check export files row by row without writing anything.

A row is rejected when it has the wrong number of fields for its header, when
its date or amount cannot be read the way its system writes them, or when its
account code does not match the configured pattern.  Dates and amounts are read
by the same functions ``ingest`` uses, so a row that passes here is a row ingest
can read.  Every rejected row gets one warning through the project logger;
nothing is printed.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEM_MODULES, detect_system

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """What a validation run found across all of its files."""

    checked: int
    rejected: int
    unreadable: int

    def passed(self) -> bool:
        """True when every row of every file was read and none was rejected."""
        return self.rejected == 0 and self.unreadable == 0


def row_problems(
    module: ModuleType, header: Sequence[str], row_values: Sequence[str], pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data row of the system ``module`` reads; empty when it is fine."""
    if len(row_values) != len(header):
        return [f"expected {len(header)} fields, found {len(row_values)}"]
    row = dict(zip(header, row_values, strict=True))
    problems: list[str] = []
    for column, parse in ((module.DATE_COLUMN, module.parse_date), (module.AMOUNT_COLUMN, module.parse_amount)):
        try:
            parse(row[column])
        except LedgerParseError as exc:
            problems.append(str(exc))
    code = row[module.ACCOUNT_COLUMN]
    if not pattern.fullmatch(code):
        problems.append(f"account code {code!r} does not match {pattern.pattern}")
    return problems


def validate_file(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(checked, rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read at all.
    """
    source = Path(path)
    module = SYSTEM_MODULES[detect_system(source)]
    header, lines = module.read_fields(source)
    needed = (module.DATE_COLUMN, module.AMOUNT_COLUMN, module.ACCOUNT_COLUMN)
    missing = [column for column in needed if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    checked = 0
    rejected = 0
    for number, row_values in lines:
        checked += 1
        problems = row_problems(module, header, row_values, pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return checked, rejected


def validate_files(paths: Iterable[Path], account_code_pattern: str) -> ValidationResult:
    """Check every export named and total up what was found.

    A file that cannot be read gets a warning and is counted as unreadable; the
    rest of the files are still checked.
    """
    pattern = re.compile(account_code_pattern)
    checked = 0
    rejected = 0
    unreadable = 0
    for path in paths:
        try:
            file_checked, file_rejected = validate_file(Path(path), pattern)
        except (ValueError, OSError) as exc:
            _log.warning("%s: cannot be read: %s", path, exc)
            unreadable += 1
            continue
        checked += file_checked
        rejected += file_rejected
    return ValidationResult(checked=checked, rejected=rejected, unreadable=unreadable)
