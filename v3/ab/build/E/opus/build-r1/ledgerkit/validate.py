"""Row by row checks on export files.

The readers stop at the first row they cannot shape, which is right for a read
and wrong for a check.  :func:`check_file` walks the file itself, using each
reader's constants and splitter, and looks at every row, so one run reports
every bad row a file holds.

A row is rejected when its field count differs from the header's, when its date
is not in its system's format, when its amount is not a number in its system's
units, or when its account code does not match the configured pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.ingest import FIELD_COLUMNS, parse_amount, parse_date
from ledgerkit.parsers import detect_system, system_a, system_c


@dataclass(frozen=True)
class Rejection:
    """One rejected row: its physical line number and what was wrong with it."""

    line: int
    reason: str


@dataclass(frozen=True)
class FileCheck:
    """The outcome of checking one export file."""

    system: str
    checked: int
    rejections: tuple[Rejection, ...]


def _data_lines(system: str, text: str) -> list[tuple[int, str]]:
    """Every non-blank line after the preamble, with its physical line number.

    The first entry is the header.  System A's comment lines and system C's
    banner and trailer are left out, just as the readers leave them out.
    """
    out: list[tuple[int, str]] = []
    seen_banner = system != "C"
    for number, raw in enumerate(text.split("\n"), start=1):
        line = raw.rstrip("\r")
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
        out.append((number, line))
    return out


def _split(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def check_row(system: str, row: dict[str, str], account_code_pattern: re.Pattern[str]) -> list[str]:
    """Everything wrong with one correctly shaped row; empty when it passes."""
    _, date_column, account_column, _, amount_column = FIELD_COLUMNS[system]
    problems: list[str] = []
    for column, parse in ((date_column, parse_date), (amount_column, parse_amount)):
        try:
            parse(system, row[column])
        except LedgerParseError as exc:
            problems.append(f"{column}: {exc}")
    code = row[account_column]
    if not account_code_pattern.fullmatch(code):
        problems.append(f"{account_column}: {code!r} does not match {account_code_pattern.pattern!r}")
    return problems


def check_file(path: Path, account_code_pattern: str) -> FileCheck:
    """Check every row of one export file.

    Raises :class:`OSError` when the file cannot be read and
    :class:`LedgerParseError` when it is not a recognisable export at all.
    """
    source = Path(path)
    system = detect_system(source)
    pattern = re.compile(account_code_pattern)
    lines = _data_lines(system, source.read_text(encoding="utf-8"))
    if not lines:
        raise LedgerParseError(f"{source.name}: no header row")

    header = _split(system, lines[0][1])
    missing = [column for column in FIELD_COLUMNS[system] if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejections: list[Rejection] = []
    for number, line in lines[1:]:
        values = _split(system, line)
        if len(values) != len(header):
            rejections.append(Rejection(number, f"expected {len(header)} fields, found {len(values)}"))
            continue
        problems = check_row(system, dict(zip(header, values, strict=True)), pattern)
        if problems:
            rejections.append(Rejection(number, "; ".join(problems)))
    return FileCheck(system, len(lines) - 1, tuple(rejections))
