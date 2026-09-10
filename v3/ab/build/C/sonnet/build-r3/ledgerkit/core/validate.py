"""Row level validation for export files, used by the ``validate`` subcommand.

Unlike the readers in :mod:`ledgerkit.parsers`, which raise on the first
malformed line, :func:`validate_file` checks every data row and reports every
problem it finds, because that is what the ``validate`` command promises.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_b, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationOutcome:
    """How many rows one file's validation looked at and how many it rejected."""

    checked: int
    rejected: int


@dataclass(frozen=True)
class _SystemSpec:
    date_field: str
    amount_field: str
    account_field: str
    parse_date: Callable[[str], date]
    parse_amount: Callable[[str], Decimal]


def _parse_iso_date(value: str) -> date:
    return date.fromisoformat(value.strip())


def _parse_calder_date(value: str) -> date:
    return datetime.strptime(value.strip(), system_c.DATE_FORMAT).date()


def _parse_decimal_amount(value: str) -> Decimal:
    return Decimal(value.strip())


_SPECS: dict[str, _SystemSpec] = {
    "A": _SystemSpec("posted_on", "amount", "account", _parse_iso_date, _parse_decimal_amount),
    "B": _SystemSpec("value_date", "amount", "acct", _parse_iso_date, system_b.to_major_units),
    "C": _SystemSpec("txn_date", "gross_amount", "ledger_acct", _parse_calder_date, _parse_decimal_amount),
}


def _header_and_lines_a(text: str) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("#") or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


def _header_and_lines_b(text: str) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


def _header_and_lines_c(text: str) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
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
        if header is None:
            header = fields.split_record(line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


_HEADER_READERS: dict[str, Callable[[str], tuple[list[str], list[tuple[int, str]]]]] = {
    "A": _header_and_lines_a,
    "B": _header_and_lines_b,
    "C": _header_and_lines_c,
}


def _check_row(line: str, header: list[str], spec: _SystemSpec, pattern: re.Pattern[str]) -> str | None:
    """Return a description of what is wrong with ``line``, or ``None`` if nothing is."""
    values = fields.split_record(line)
    if len(values) != len(header):
        return f"expected {len(header)} fields, found {len(values)}"
    row = dict(zip(header, values, strict=True))

    date_value = row[spec.date_field]
    try:
        spec.parse_date(date_value)
    except ValueError:
        return f"{spec.date_field} {date_value!r} is not a valid date"

    amount_value = row[spec.amount_field]
    try:
        spec.parse_amount(amount_value)
    except (InvalidOperation, LedgerParseError, ValueError):
        return f"{spec.amount_field} {amount_value!r} is not a valid amount"

    account_value = row[spec.account_field].strip()
    if not pattern.fullmatch(account_value):
        return f"{spec.account_field} {account_value!r} does not match the account code pattern"

    return None


def validate_file(path: Path, account_code_pattern: str) -> ValidationOutcome:
    """Check every data row of one export file.

    Every rejected row produces one WARNING through the project logger, naming
    the file, the line number and what was wrong.  Checking continues to the
    end of the file regardless of what it finds.
    """
    source = Path(path)
    system = detect_system(source)
    spec = _SPECS[system]
    pattern = re.compile(account_code_pattern)
    text = source.read_text(encoding="utf-8")
    header, data_lines = _HEADER_READERS[system](text)

    checked = 0
    rejected = 0
    for number, line in data_lines:
        checked += 1
        problem = _check_row(line, header, spec, pattern)
        if problem is not None:
            rejected += 1
            _log.warning("%s line %d: %s", source.name, number, problem)
    return ValidationOutcome(checked=checked, rejected=rejected)
