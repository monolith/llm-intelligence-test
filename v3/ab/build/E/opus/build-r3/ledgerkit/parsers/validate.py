"""Row by row validation of export files.

The readers stop at the first row they cannot make sense of.  Validation has to
look at every row and say what is wrong with each, so it walks the file itself,
using the same shape rules as the reader for that system: Ardent comment lines,
the Calder banner and trailer, and the header row are skipped, and Ardent lines
are split with the quote aware splitter.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import MODULES, detect_system, system_a, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """How many data rows one file had, and how many of them were rejected."""

    checked: int
    rejected: int


def _split(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _numbered_lines(system: str, path: Path) -> Iterator[tuple[int, list[str]]]:
    """Yield ``(line number, fields)`` for the header and every data line, in file order."""
    seen_banner = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if system == "A" and line.startswith(system_a.COMMENT_PREFIX):
            continue
        if system == "C":
            if not seen_banner:
                seen_banner = True
                continue
            if system_c.TRAILER_PATTERN.match(stripped):
                continue
        yield number, _split(system, line)


def _problems(values: list[str], header: list[str], system: str, pattern: re.Pattern[str]) -> list[str]:
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    module = MODULES[system]
    row = dict(zip(header, values, strict=True))
    found: list[str] = []
    for column, parse in ((module.DATE_COLUMN, module.parse_date), (module.AMOUNT_COLUMN, module.parse_amount)):
        try:
            parse(row[column])
        except LedgerParseError as exc:
            found.append(str(exc))
    code = row[module.ACCOUNT_COLUMN]
    if not pattern.search(code):
        found.append(f"account code {code!r} does not match {pattern.pattern!r}")
    return found


def validate_file(path: Path, account_code_pattern: str) -> ValidationResult:
    """Check every data row of one export and log a warning for each rejected row.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read at all: it is missing, its first line matches no known format, or it
    has no header row or lacks a column validation needs.
    """
    source = Path(path)
    system = detect_system(source)
    module = MODULES[system]
    pattern = re.compile(account_code_pattern)

    header: list[str] | None = None
    checked = 0
    rejected = 0
    for number, values in _numbered_lines(system, source):
        if header is None:
            header = values
            needed = (module.DATE_COLUMN, module.AMOUNT_COLUMN, module.ACCOUNT_COLUMN)
            missing = [column for column in needed if column not in header]
            if missing:
                raise LedgerParseError(f"{source} line {number}: header has no column {', '.join(missing)}")
            continue
        checked += 1
        problems = _problems(values, header, system, pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: rejected: %s", source, number, "; ".join(problems))

    if header is None:
        raise LedgerParseError(f"{source}: no header row")
    return ValidationResult(checked=checked, rejected=rejected)
