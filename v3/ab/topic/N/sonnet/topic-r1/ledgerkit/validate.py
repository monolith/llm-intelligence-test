"""Check export files for malformed rows without writing anything.

See ``SPEC.md``, section 4, for the command this implements.  Unlike the
readers in :mod:`ledgerkit.parsers`, this module never stops at the first bad
row: it scans every row, on its own, so one malformed line does not hide the
rest.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_c

_log = get_logger(__name__)

_DATE_COLUMN = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_COLUMN = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_COLUMN = {"A": "account", "B": "acct", "C": "ledger_acct"}


@dataclass(frozen=True)
class ValidationResult:
    """How many rows a file's scan looked at, and how many failed."""

    checked: int
    rejected: int


def _split(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _collect_a(lines: list[str]) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        if line.startswith("#") or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError("no header row")
    return header, data


def _collect_b(lines: list[str]) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
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


def _collect_c(lines: list[str]) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    seen_banner = False
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
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


_COLLECTORS = {"A": _collect_a, "B": _collect_b, "C": _collect_c}


def _check_date(system: str, raw: str) -> bool:
    text = raw.strip()
    try:
        if system == "C":
            day_str, month_str, year_str = text.split("/")
            date(int(year_str), int(month_str), int(day_str))
        else:
            date.fromisoformat(text)
    except ValueError:
        return False
    return True


def _row_problems(system: str, row: dict[str, str], pattern: re.Pattern[str]) -> list[str]:
    problems: list[str] = []

    date_raw = row[_DATE_COLUMN[system]]
    if not _check_date(system, date_raw):
        problems.append(f"date {date_raw!r} is not valid")

    amount_raw = row[_AMOUNT_COLUMN[system]]
    try:
        Decimal(amount_raw.strip())
    except InvalidOperation:
        problems.append(f"amount {amount_raw!r} is not a number")

    account_raw = row[_ACCOUNT_COLUMN[system]]
    if not pattern.match(account_raw.strip()):
        problems.append(f"account code {account_raw!r} does not match the configured pattern")

    return problems


def validate_file(path: Path, account_code_pattern: str) -> ValidationResult | None:
    """Scan every row of one export file.

    Returns ``None`` when the file itself could not be read at all -- an
    unrecognized format or a missing header row -- rather than a per-row
    problem.  Every rejected row produces one ``WARNING`` through the project
    logger, naming the file, the line, and what was wrong with it.
    """
    try:
        system = detect_system(path)
        header, data_lines = _COLLECTORS[system](Path(path).read_text(encoding="utf-8").splitlines())
    except (LedgerParseError, OSError) as exc:
        _log.warning("cannot read %s: %s", path, exc)
        return None

    pattern = re.compile(account_code_pattern)
    checked = 0
    rejected = 0
    for number, line in data_lines:
        checked += 1
        values = _split(system, line)
        if len(values) != len(header):
            _log.warning(
                "%s line %d: expected %d field(s), found %d", path.name, number, len(header), len(values)
            )
            rejected += 1
            continue
        row = dict(zip(header, values, strict=True))
        problems = _row_problems(system, row, pattern)
        if problems:
            _log.warning("%s line %d: %s", path.name, number, "; ".join(problems))
            rejected += 1

    return ValidationResult(checked=checked, rejected=rejected)
