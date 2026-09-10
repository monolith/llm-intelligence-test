"""Row by row checks on export files, for the ``validate`` command.

Unlike the readers, which stop at the first line they cannot use, validation
looks at every data line and logs one warning per rejected row.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import MODULES, detect_system

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationSummary:
    """What a validation run found."""

    checked: int
    rejected: int
    unreadable: int


def row_problems(system: str, header: list[str], values: list[str], pattern: re.Pattern[str]) -> list[str]:
    """Everything wrong with one data row, or an empty list when it passes."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    module = MODULES[system]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    for parse, column in ((module.parse_date, module.DATE_FIELD), (module.parse_amount, module.AMOUNT_FIELD)):
        try:
            parse(row[column])
        except LedgerParseError as exc:
            problems.append(str(exc))
    code = row[module.ACCOUNT_FIELD]
    if not pattern.search(code):
        problems.append(f"account code {code!r} does not match {pattern.pattern!r}")
    return problems


def validate_file(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export; return ``(checked, rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    source = Path(path)
    system = detect_system(source)
    module = MODULES[system]
    header, body = module.split_body(source)
    missing = [
        column
        for column in (module.DATE_FIELD, module.ACCOUNT_FIELD, module.AMOUNT_FIELD)
        if column not in header
    ]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in body:
        problems = row_problems(system, header, values, pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))
    return len(body), rejected


def validate_files(paths: Sequence[Path], pattern: re.Pattern[str]) -> ValidationSummary:
    """Validate each export in turn, carrying on past files that cannot be read."""
    checked = rejected = unreadable = 0
    for path in paths:
        try:
            file_checked, file_rejected = validate_file(path, pattern)
        except (LedgerParseError, OSError, UnicodeDecodeError) as exc:
            _log.warning("%s: cannot be read: %s", path, exc)
            unreadable += 1
            continue
        checked += file_checked
        rejected += file_rejected
    return ValidationSummary(checked=checked, rejected=rejected, unreadable=unreadable)
