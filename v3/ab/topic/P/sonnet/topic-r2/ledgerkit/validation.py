"""Row level checks over an export file, used by the ``validate`` command.

Unlike the readers in :mod:`ledgerkit.parsers`, which stop at the first
malformed row, the checks here look at every data row and report each one that
fails, because ``validate`` has to say what is wrong with all of them, not just
the first.
"""

from __future__ import annotations

import re
from decimal import InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_COLUMNS_BY_SYSTEM: dict[str, tuple[str, ...]] = {
    "A": system_a.COLUMNS,
    "B": system_b.COLUMNS,
    "C": system_c.COLUMNS,
}
_DATE_FIELD_BY_SYSTEM: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_FIELD_BY_SYSTEM: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_FIELD_BY_SYSTEM: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}


def _split(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _parse_date(system: str, text: str) -> None:
    if system == "A":
        system_a.parse_date(text)
    elif system == "B":
        system_b.parse_date(text)
    else:
        system_c.parse_date(text)


def _parse_amount(system: str, text: str) -> None:
    if system == "B":
        system_b.to_major_units(text)
    elif system == "C":
        system_c.parse_amount(text)
    else:
        system_a.parse_amount(text)


def _raw_data_lines(path: Path, system: str) -> list[tuple[int, str]]:
    """Return ``(line number, raw line)`` for every data line, skipping preamble, header and trailer."""
    numbered_lines = list(enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1))
    out: list[tuple[int, str]] = []

    if system == "A":
        seen_header = False
        for number, line in numbered_lines:
            if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
                continue
            if not seen_header:
                seen_header = True
                continue
            out.append((number, line))
        return out

    if system == "B":
        seen_header = False
        for number, line in numbered_lines:
            if not line.strip():
                continue
            if not seen_header:
                seen_header = True
                continue
            out.append((number, line))
        return out

    seen_banner = False
    seen_header = False
    for number, line in numbered_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if not seen_header:
            seen_header = True
            continue
        out.append((number, line))
    return out


def _row_problems(system: str, row: dict[str, str], account_pattern: re.Pattern[str]) -> list[str]:
    problems: list[str] = []

    date_text = row[_DATE_FIELD_BY_SYSTEM[system]]
    try:
        _parse_date(system, date_text)
    except LedgerParseError:
        problems.append(f"date {date_text!r} is not valid")

    amount_text = row[_AMOUNT_FIELD_BY_SYSTEM[system]]
    try:
        _parse_amount(system, amount_text)
    except (LedgerParseError, InvalidOperation):
        problems.append(f"amount {amount_text!r} is not a number")

    code = row[_ACCOUNT_FIELD_BY_SYSTEM[system]].strip()
    if not account_pattern.fullmatch(code):
        problems.append(f"account code {code!r} does not match the configured pattern")

    return problems


def validate_file(path: Path, account_code_pattern: str) -> tuple[int, int]:
    """Check every data row of one export file.

    Returns ``(rows checked, rows rejected)``.  Raises :class:`LedgerParseError`
    or :class:`OSError` when the file itself cannot be read at all.
    """
    system = detect_system(path)
    columns = _COLUMNS_BY_SYSTEM[system]
    pattern = re.compile(account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in _raw_data_lines(path, system):
        checked += 1
        values = _split(system, line)
        if len(values) != len(columns):
            _log.warning(
                "%s line %d: expected %d field(s), found %d",
                Path(path).name,
                number,
                len(columns),
                len(values),
            )
            rejected += 1
            continue

        row = dict(zip(columns, values, strict=True))
        problems = _row_problems(system, row, pattern)
        if problems:
            _log.warning("%s line %d: %s", Path(path).name, number, "; ".join(problems))
            rejected += 1

    return checked, rejected
