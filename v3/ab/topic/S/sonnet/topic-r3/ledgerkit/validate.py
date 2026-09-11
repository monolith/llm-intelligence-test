"""Checking export files for malformed rows without writing anything.

This walks each file's own preamble/header/trailer shape -- the same shape
:mod:`ledgerkit.parsers` knows -- but unlike the readers there, it does not stop
at the first bad row: every row is checked, and a bad one is logged and counted
rather than raising.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)

_DATE_FIELD: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_DATE_FORMAT: dict[str, str] = {"A": "%Y-%m-%d", "B": "%Y-%m-%d", "C": "%d/%m/%Y"}
_AMOUNT_FIELD: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_FIELD: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}


@dataclass(frozen=True)
class ValidationResult:
    """How many rows one file's :func:`validate_file` looked at."""

    checked: int
    rejected: int


def _split_fields(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _data_lines(path: Path, system: str) -> tuple[list[str], list[tuple[int, str]]]:
    """Return (header fields, [(line number, raw line), ...]) for one export's data rows.

    Preamble, banner, header and trailer lines are identified the same way the
    matching reader in :mod:`ledgerkit.parsers` identifies them, but a bad data
    row here is left for :func:`_row_problem` to judge rather than raising.
    """
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    header: list[str] | None = None
    data: list[tuple[int, str]] = []

    if system == "A":
        for number, line in enumerate(lines, start=1):
            if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
                continue
            if header is None:
                header = fields.split_record(line)
                continue
            data.append((number, line))
    elif system == "B":
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            if header is None:
                header = line.split(",")
                continue
            data.append((number, line))
    else:
        seen_banner = False
        for number, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            if not seen_banner:
                if not stripped.startswith(system_c.BANNER):
                    raise LedgerParseError(f"{Path(path).name} line {number}: expected the Calder banner")
                seen_banner = True
                continue
            if system_c.TRAILER_PATTERN.match(stripped):
                continue
            if header is None:
                header = line.split(",")
                continue
            data.append((number, line))

    if header is None:
        raise LedgerParseError(f"{Path(path).name}: no header row")
    return header, data


def _row_problem(system: str, header: list[str], line: str, account_code_pattern: str) -> str | None:
    """Return why this row would be rejected, or ``None`` when it is fine."""
    values = _split_fields(system, line)
    if len(values) != len(header):
        return f"expected {len(header)} fields, found {len(values)}"

    row = dict(zip(header, values, strict=True))

    date_field = _DATE_FIELD[system]
    try:
        datetime.strptime(row[date_field].strip(), _DATE_FORMAT[system])
    except ValueError:
        return f"bad date {row[date_field]!r}"

    amount_field = _AMOUNT_FIELD[system]
    amount_text = row[amount_field].strip()
    try:
        Decimal(amount_text)
    except InvalidOperation:
        return f"bad amount {amount_text!r}"

    account_field = _ACCOUNT_FIELD[system]
    code = row[account_field].strip()
    if re.fullmatch(account_code_pattern, code) is None:
        return f"account code {code!r} does not match the configured pattern"

    return None


def validate_file(path: Path, account_code_pattern: str) -> ValidationResult:
    """Check every data row of one export file against SPEC.md's four criteria.

    Raises :class:`LedgerParseError` or :class:`OSError` only when the file
    itself, or its preamble/header/banner, cannot be located at all -- a
    problem with an individual row never stops the check.
    """
    source = Path(path)
    system = detect_system(source)
    header, data = _data_lines(source, system)

    checked = 0
    rejected = 0
    for number, line in data:
        checked += 1
        problem = _row_problem(system, header, line, account_code_pattern)
        if problem is not None:
            rejected += 1
            _log.warning("%s line %d: %s", source.name, number, problem)
    return ValidationResult(checked=checked, rejected=rejected)
