"""Lenient, line-by-line checking of export files.

``system_a``/``system_b``/``system_c``'s ``read_rows`` are fail fast: they raise
on the first malformed line. ``validate`` has to check every row and keep going
past a bad one, so this module re-reads each file with its own pass instead of
calling those readers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_COLUMNS: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}
_DATE_FIELD: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_FIELD: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_FIELD: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}


@dataclass(frozen=True)
class ValidationResult:
    """How many rows of one file were checked, and how many were rejected."""

    checked: int
    rejected: int


def _is_valid_date(system: str, raw: str) -> bool:
    text = raw.strip()
    try:
        if system == "C":
            day_str, month_str, year_str = text.split("/")
            date(int(year_str), int(month_str), int(day_str))
        else:
            date.fromisoformat(text)
        return True
    except (ValueError, TypeError):
        return False


def _is_valid_amount(raw: str) -> bool:
    try:
        Decimal(raw.strip())
        return True
    except InvalidOperation:
        return False


def _data_lines(path: Path, system: str) -> list[tuple[int, str]]:
    """Every data line of ``path``, skipping preamble/banner, header and trailer."""
    out: list[tuple[int, str]] = []
    seen_banner = system != "C"
    seen_header = False
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if system == "A" and stripped.startswith(system_a.COMMENT_PREFIX):
            continue
        if system == "C" and not seen_banner:
            seen_banner = True
            continue
        if system == "C" and system_c.TRAILER_PATTERN.match(stripped):
            continue
        if not seen_header:
            seen_header = True
            continue
        out.append((number, line))
    return out


def validate_file(path: Path, settings: Settings) -> ValidationResult:
    """Check every data row of one export file.

    A rejected row logs one WARNING through the project logger, naming the file,
    the line number and what was wrong. This does not stop at the first bad row.
    """
    system = detect_system(path)
    columns = _COLUMNS[system]
    date_field = _DATE_FIELD[system]
    amount_field = _AMOUNT_FIELD[system]
    account_field = _ACCOUNT_FIELD[system]
    pattern = re.compile(settings.account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in _data_lines(path, system):
        checked += 1
        values = fields.split_record(line) if system == "A" else line.split(",")

        reason: str | None = None
        if len(values) != len(columns):
            reason = f"expected {len(columns)} fields, found {len(values)}"
        else:
            row = dict(zip(columns, values, strict=True))
            if not _is_valid_date(system, row[date_field]):
                reason = f"{date_field} {row[date_field]!r} is not a valid date"
            elif not _is_valid_amount(row[amount_field]):
                reason = f"{amount_field} {row[amount_field]!r} is not a number"
            elif not pattern.match(row[account_field].strip()):
                reason = f"{account_field} {row[account_field]!r} does not match the account code pattern"

        if reason is not None:
            rejected += 1
            _log.warning("%s line %d: %s", Path(path).name, number, reason)

    return ValidationResult(checked=checked, rejected=rejected)
