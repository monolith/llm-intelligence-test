"""`validate` (SPEC.md): reject malformed rows without stopping at the first one.

The readers under :mod:`ledgerkit.parsers` raise on the first structural
problem they hit and abort the whole file.  ``validate`` has to keep going and
warn on every bad row instead, so this module re-walks each format's shape
itself rather than calling ``read_rows``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core.fields import split_record
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)

_DATE_FIELD = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_ACCOUNT_FIELD = {"A": "account", "B": "acct", "C": "ledger_acct"}
_AMOUNT_FIELD = {"A": "amount", "B": "amount", "C": "gross_amount"}


@dataclass(frozen=True)
class ValidationResult:
    """How many rows of one file were checked, and how many were rejected."""

    checked: int
    rejected: int


def _split_line(system: str, line: str) -> list[str]:
    if system == "A":
        return split_record(line)
    return line.split(",")


def _parse_date(system: str, raw: str) -> date:
    if system == "C":
        return datetime.strptime(raw.strip(), "%d/%m/%Y").date()
    return date.fromisoformat(raw.strip())


def _data_lines(system: str, path: Path) -> tuple[list[str], list[tuple[int, str]]]:
    """Return the header fields and the ``(line_number, raw_line)`` data rows."""
    numbered = list(enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1))

    if system == "A":
        header: list[str] | None = None
        data: list[tuple[int, str]] = []
        for number, line in numbered:
            if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
                continue
            if header is None:
                header = split_record(line)
                continue
            data.append((number, line))
        if header is None:
            raise LedgerParseError(f"{Path(path).name}: no header row")
        return header, data

    if system == "B":
        header = None
        data = []
        for number, line in numbered:
            if not line.strip():
                continue
            if header is None:
                header = line.split(",")
                continue
            data.append((number, line))
        if header is None:
            raise LedgerParseError(f"{Path(path).name}: no header row")
        return header, data

    header = None
    data = []
    seen_banner = False
    for number, line in numbered:
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


def validate_file(path: Path, settings: Settings) -> ValidationResult:
    """Check one export file row by row.

    Warns through the project logger on each rejected row and keeps going;
    raises :class:`LedgerParseError` or ``OSError`` only when the file itself
    could not be read at all.
    """
    source = Path(path)
    system = detect_system(source)
    header, data = _data_lines(system, source)
    account_field = _ACCOUNT_FIELD[system]
    date_field = _DATE_FIELD[system]
    amount_field = _AMOUNT_FIELD[system]
    pattern = re.compile(settings.account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in data:
        checked += 1
        values = _split_line(system, line)
        if len(values) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d", source.name, number, len(header), len(values)
            )
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        problems: list[str] = []

        try:
            _parse_date(system, row[date_field])
        except ValueError:
            problems.append(f"date {row[date_field]!r} is not a valid date")

        try:
            Decimal(row[amount_field].strip())
        except InvalidOperation:
            problems.append(f"amount {row[amount_field]!r} is not a number")

        code = row[account_field]
        if not pattern.fullmatch(code.strip()):
            problems.append(f"account code {code!r} does not match the configured pattern")

        if problems:
            _log.warning("%s line %d: %s", source.name, number, "; ".join(problems))
            rejected += 1

    return ValidationResult(checked=checked, rejected=rejected)
