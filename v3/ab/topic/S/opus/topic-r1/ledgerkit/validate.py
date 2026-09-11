"""``validate``: check export files row by row without writing anything.

A row is rejected when it does not have as many fields as its header, when its
date cannot be read the way its system writes dates, when its amount cannot be
read as a number, or when its account code does not match the
``[validate] account_code_pattern`` setting.  Dates and amounts are read by the
same per-system functions ``ingest`` uses, so a file that validates is a file
that ingests.

Each rejected row gets one ``WARNING`` through the project logger naming the
file, the line and everything that was wrong with it.  Every row is checked, not
just the rows up to the first bad one.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import SYSTEM_MODULES, detect_system

_log = get_logger(__name__)


@dataclass
class ValidationSummary:
    """What one validation run found across all of its files."""

    checked: int = 0
    rejected: int = 0
    unreadable: list[Path] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True when every row of every file was read and accepted."""
        return self.rejected == 0 and not self.unreadable


def row_problems(
    module: ModuleType, header: list[str], values: list[str], pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one data row of a ``module`` export; empty when it is fine.

    The account code must match ``pattern`` in full.
    """
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
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
    if pattern.fullmatch(code) is None:
        problems.append(f"account code {code!r} does not match {pattern.pattern!r}")
    return problems


def validate_file(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError`, :class:`OSError` or
    :class:`UnicodeDecodeError` when the file cannot be read at all.
    """
    source = Path(path)
    module = SYSTEM_MODULES[detect_system(source)]
    header, body = module.read_fields(source)
    needed = (module.DATE_COLUMN, module.AMOUNT_COLUMN, module.ACCOUNT_COLUMN)
    missing = [column for column in needed if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: the header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in body:
        problems = row_problems(module, header, values, pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(body), rejected


def validate_files(paths: Iterable[Path], pattern: re.Pattern[str]) -> ValidationSummary:
    """Check every export in ``paths``, carrying on past bad rows and unreadable files."""
    summary = ValidationSummary()
    for path in paths:
        try:
            checked, rejected = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("cannot read %s: %s", path, exc)
            summary.unreadable.append(Path(path))
            continue
        summary.checked += checked
        summary.rejected += rejected
    return summary
