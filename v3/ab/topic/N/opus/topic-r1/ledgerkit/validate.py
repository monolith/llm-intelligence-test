"""Row by row validation of export files: the ``validate`` command.

The readers stop at the first row they cannot make sense of, which is right for
``ingest`` and wrong here.  This module walks every physical line itself, splits
each row the same way that system's reader does, and checks every row, logging
one warning per rejected row with its file and line number.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_MODULES: dict[str, ModuleType] = {"A": system_a, "B": system_b, "C": system_c}


def _split_plain(line: str) -> list[str]:
    return line.split(",")


# Ardent quotes memo text; Borough and Calder never quote, and their readers
# split on every comma.
_SPLITTERS: dict[str, Callable[[str], list[str]]] = {
    "A": fields.split_record,
    "B": _split_plain,
    "C": _split_plain,
}


@dataclass(frozen=True)
class FileResult:
    """How many data rows one file held and how many were rejected."""

    checked: int
    rejected: int


def _header_and_rows(path: Path, system: str) -> tuple[list[str], list[tuple[int, str]]]:
    """Separate the header from the data lines, keeping physical line numbers."""
    split = _SPLITTERS[system]
    header: list[str] | None = None
    rows: list[tuple[int, str]] = []
    seen_banner = False
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
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
        if header is None:
            header = split(line)
            continue
        rows.append((number, line))
    if header is None:
        raise LedgerParseError(f"{Path(path).name}: no header row")
    return header, rows


def row_problems(
    values: list[str], header: list[str], module: ModuleType, code_pattern: re.Pattern[str]
) -> list[str]:
    """Everything wrong with one split row, or an empty list when it is fine."""
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
    if not code_pattern.search(code):
        problems.append(f"account code {code!r} does not match {code_pattern.pattern!r}")
    return problems


def validate_file(path: Path, code_pattern: re.Pattern[str]) -> FileResult:
    """Check every data row of one export.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    source = Path(path)
    system = detect_system(source)
    module = _MODULES[system]
    header, rows = _header_and_rows(source, system)
    needed = (module.DATE_COLUMN, module.AMOUNT_COLUMN, module.ACCOUNT_COLUMN)
    missing = [column for column in needed if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    split = _SPLITTERS[system]
    rejected = 0
    for number, line in rows:
        problems = row_problems(split(line), header, module, code_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d rejected: %s", source, number, "; ".join(problems))
    return FileResult(checked=len(rows), rejected=rejected)
