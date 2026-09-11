"""``validate`` — reject malformed rows without writing anything.

A row is rejected for the first of these that is true: its field count does
not match its system's header shape, its date cannot be read, its amount
cannot be read, or its account code does not match the configured pattern.
Every data row in the file is checked; a bad row does not stop the scan.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_COLUMNS = {"A": system_a.COLUMNS, "B": system_b.COLUMNS, "C": system_c.COLUMNS}
_DATE_FIELD = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_FIELD = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_FIELD = {"A": "account", "B": "acct", "C": "ledger_acct"}
_PARSE_DATE = {"A": system_a.parse_date, "B": system_b.parse_date, "C": system_c.parse_date}
_PARSE_AMOUNT = {"A": system_a.parse_amount, "B": system_b.to_major_units, "C": system_c.parse_amount}


def _data_lines_a(text: str) -> Iterator[tuple[int, list[str]]]:
    header_seen = False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if not header_seen:
            header_seen = True
            continue
        yield number, fields.split_record(line)


def _data_lines_b(text: str) -> Iterator[tuple[int, list[str]]]:
    header_seen = False
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if not header_seen:
            header_seen = True
            continue
        yield number, line.split(",")


def _data_lines_c(text: str) -> Iterator[tuple[int, list[str]]]:
    header_seen = False
    seen_banner = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if not header_seen:
            header_seen = True
            continue
        yield number, line.split(",")


_DATA_LINES = {"A": _data_lines_a, "B": _data_lines_b, "C": _data_lines_c}


def _row_rejection(system: str, values: list[str], settings: Settings) -> str | None:
    """The reason ``values`` is rejected, or ``None`` when the row is fine."""
    columns = _COLUMNS[system]
    if len(values) != len(columns):
        return f"expected {len(columns)} fields, found {len(values)}"

    row = dict(zip(columns, values, strict=True))

    try:
        _PARSE_DATE[system](row[_DATE_FIELD[system]])
    except ValueError:
        return f"bad date {row[_DATE_FIELD[system]]!r}"

    try:
        _PARSE_AMOUNT[system](row[_AMOUNT_FIELD[system]])
    except ValueError:
        return f"bad amount {row[_AMOUNT_FIELD[system]]!r}"

    code = row[_ACCOUNT_FIELD[system]]
    if re.fullmatch(settings.account_code_pattern, code.strip()) is None:
        return f"account code {code!r} does not match pattern {settings.account_code_pattern!r}"

    return None


def validate_file(path: Path, *, settings: Settings) -> tuple[int, int]:
    """Validate one export file. Returns ``(rows checked, rows rejected)``.

    Raises whatever :func:`~ledgerkit.parsers.detect_system` or reading the
    file raises when the file cannot be read at all; the caller decides what
    that means for the exit code.
    """
    text = path.read_text(encoding="utf-8")
    system = detect_system(path)

    checked = 0
    rejected = 0
    for number, values in _DATA_LINES[system](text):
        checked += 1
        reason = _row_rejection(system, values, settings)
        if reason is not None:
            rejected += 1
            _log.warning("%s line %d: %s", path.name, number, reason)
    return checked, rejected
