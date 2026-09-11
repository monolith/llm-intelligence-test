"""Row-level checks for the ``validate`` command.

The readers in :mod:`ledgerkit.parsers` stop at the first malformed line.
``validate`` must not: every data row gets checked, and a bad one is logged and
counted rather than raised. This module keeps its own line-splitting for that
reason, matching each reader's file shape but never aborting on a bad row.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import NamedTuple

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

DataLines = list[tuple[int, str]]


def _plain_split(line: str) -> list[str]:
    return line.split(",")


def _rows_for_a(lines: list[str]) -> tuple[list[str], DataLines]:
    header: list[str] | None = None
    data: DataLines = []
    for number, line in enumerate(lines, start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


def _rows_for_b(lines: list[str]) -> tuple[list[str], DataLines]:
    header: list[str] | None = None
    data: DataLines = []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


def _rows_for_c(lines: list[str]) -> tuple[list[str], DataLines]:
    header: list[str] | None = None
    data: DataLines = []
    seen_banner = False
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            if not stripped.startswith(system_c.BANNER):
                raise LedgerParseError(f"line {number}: expected the Calder banner")
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if header is None:
            header = line.split(",")
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


def _parse_calder_date(text: str) -> date:
    day_str, month_str, year_str = text.strip().split("/")
    return date(int(year_str), int(month_str), int(day_str))


def _decimal(text: str) -> Decimal:
    return Decimal(text.strip())


class _SystemShape(NamedTuple):
    rows: Callable[[list[str]], tuple[list[str], DataLines]]
    split: Callable[[str], list[str]]
    date_field: str
    account_field: str
    amount_field: str
    parse_date: Callable[[str], date]
    parse_amount: Callable[[str], Decimal]


_SHAPES: dict[str, _SystemShape] = {
    "A": _SystemShape(_rows_for_a, fields.split_record, "posted_on", "account", "amount", date.fromisoformat, _decimal),
    "B": _SystemShape(_rows_for_b, _plain_split, "value_date", "acct", "amount", date.fromisoformat, system_b.to_major_units),
    "C": _SystemShape(_rows_for_c, _plain_split, "txn_date", "ledger_acct", "gross_amount", _parse_calder_date, _decimal),
}


def _reason(line: str, header: list[str], shape: _SystemShape, account_pattern: re.Pattern[str]) -> str | None:
    values = shape.split(line)
    if len(values) != len(header):
        return f"expected {len(header)} fields, found {len(values)}"
    row = dict(zip(header, values, strict=True))

    try:
        shape.parse_date(row.get(shape.date_field, ""))
    except (ValueError, KeyError):
        return f"bad date {row.get(shape.date_field)!r}"

    try:
        shape.parse_amount(row.get(shape.amount_field, ""))
    except (ValueError, KeyError, InvalidOperation):
        return f"bad amount {row.get(shape.amount_field)!r}"

    if not account_pattern.fullmatch(row.get(shape.account_field, "")):
        return f"bad account code {row.get(shape.account_field)!r}"

    return None


def validate_file(path: Path, account_code_pattern: str) -> tuple[int, int]:
    """Check every data row of ``path``. Returns ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file itself
    could not be read, or its format could not be recognized at all.
    """
    source = Path(path)
    system = detect_system(source)
    lines = source.read_text(encoding="utf-8").splitlines()
    shape = _SHAPES[system]
    header, data = shape.rows(lines)
    pattern = re.compile(account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in data:
        checked += 1
        reason = _reason(line, header, shape, pattern)
        if reason is not None:
            _log.warning("%s line %d: %s", source.name, number, reason)
            rejected += 1

    return checked, rejected
