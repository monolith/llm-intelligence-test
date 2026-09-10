"""Check export files row by row without writing anything.

The readers in :mod:`ledgerkit.parsers` stop at the first malformed line, which
is right for ingest and wrong here: validation has to look at every row.  So
this module walks each file's lines itself, using the same shape rules as the
readers (preamble, header, trailer, quoting) and the same date and amount
parsers as :mod:`ledgerkit.ingest`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.ingest import LAYOUTS, parse_amount, parse_date
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class FileResult:
    """How many data rows one file held and how many of them were rejected."""

    checked: int
    rejected: int


def _data_lines(system: str, lines: list[str]) -> tuple[int, str, list[tuple[int, str]]]:
    """Split a file into its header line and its numbered data lines."""
    header: tuple[int, str] | None = None
    data: list[tuple[int, str]] = []
    seen_banner = False
    for number, line in enumerate(lines, start=1):
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
            header = (number, line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header[0], header[1], data


def _split(system: str, line: str) -> list[str]:
    # Only Ardent quotes its fields; Borough and Calder never do.
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def row_problems(system: str, header: list[str], values: list[str], pattern: re.Pattern[str]) -> list[str]:
    """Everything wrong with one data row, or an empty list when it is fine."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    layout = LAYOUTS[system]
    problems: list[str] = []
    try:
        parse_date(system, row[layout.date])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        parse_amount(system, row[layout.amount])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[layout.account_code]
    if not pattern.search(code):
        problems.append(f"account code {code!r} does not match {pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_code_pattern: str) -> FileResult:
    """Check every data row of one export, logging a warning for each bad row.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read at all.
    """
    source = Path(path)
    system = detect_system(source)
    lines = source.read_text(encoding="utf-8").splitlines()
    _, header_line, data = _data_lines(system, lines)
    header = _split(system, header_line)
    layout = LAYOUTS[system]
    missing = [
        column
        for column in (layout.date, layout.amount, layout.account_code)
        if column not in header
    ]
    if missing:
        raise LedgerParseError(f"header has no {', '.join(missing)} column")

    pattern = re.compile(account_code_pattern)
    rejected = 0
    for number, line in data:
        problems = row_problems(system, header, _split(system, line), pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source, number, "; ".join(problems))

    if system == "C":
        claimed = system_c.read_trailer_count(source)
        if claimed is not None and claimed != len(data):
            _log.warning("%s: trailer claims %d rows, found %d", source, claimed, len(data))
    return FileResult(checked=len(data), rejected=rejected)
