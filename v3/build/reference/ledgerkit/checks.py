"""Row by row checking of an export file.

Unlike the readers, which stop at the first line they cannot make sense of, this
module looks at every line and reports each bad one.  It builds nothing and
writes nothing.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.convert import COLUMN_MAP, parse_amount, parse_date
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def iter_data_lines(path: Path, system: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line number, text)`` for the data lines of an export, header excluded."""
    source = Path(path)
    seen_header = False
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if system == "A" and line.startswith(system_a.COMMENT_PREFIX):
            continue
        if system == "C" and stripped.startswith(system_c.BANNER):
            continue
        if system == "C" and system_c.TRAILER_PATTERN.match(stripped):
            continue
        if not seen_header:
            seen_header = True
            continue
        yield number, line


def header_of(path: Path, system: str) -> list[str]:
    """The header row of an export, as a list of column names."""
    if system == "A":
        return system_a.read_header(path)
    if system == "B":
        return system_b.read_header(path)
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(system_c.BANNER):
            continue
        return line.split(",")
    raise LedgerParseError(f"{Path(path).name}: no header row")


def split_line(line: str, system: str) -> list[str]:
    """Split one data line into its fields, the way that system quotes them."""
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def check_row(system: str, row: dict[str, str], code_pattern: re.Pattern[str]) -> str | None:
    """Return the reason this row is bad, or ``None`` when it is fine."""
    columns = COLUMN_MAP[system]
    code = row[columns["account_code"]].strip()
    if not code_pattern.match(code):
        return f"account code {code!r} does not match {code_pattern.pattern}"
    try:
        parse_date(system, row[columns["date"]])
    except LedgerParseError as exc:
        return str(exc)
    try:
        parse_amount(system, row[columns["amount"]])
    except LedgerParseError as exc:
        return str(exc)
    return None


def validate_file(path: Path, settings: Settings) -> tuple[int, int]:
    """Check every row of one export.  Returns ``(rows checked, rows rejected)``."""
    source = Path(path)
    system = detect_system(source)
    header = header_of(source, system)
    code_pattern = re.compile(settings.account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in iter_data_lines(source, system):
        checked += 1
        values = split_line(line, system)
        if len(values) != len(header):
            rejected += 1
            _log.warning(
                "%s line %d: expected %d fields, found %d",
                source.name,
                number,
                len(header),
                len(values),
            )
            continue
        row = dict(zip(header, values, strict=True))
        reason = check_row(system, row, code_pattern)
        if reason is not None:
            rejected += 1
            _log.warning("%s line %d: %s", source.name, number, reason)
    return checked, rejected
