"""Row-by-row validation of export files.

Unlike the readers in :mod:`ledgerkit.parsers`, which stop at the first
malformed line, this module checks every row of a file and reports every
problem it finds through the project logger.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_DATE_FIELD: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_FIELD: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_FIELD: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}


def _parse_date(system: str, text: str) -> date:
    if system == "C":
        return system_c.parse_date(text)
    return date.fromisoformat(text)


def _parse_amount(system: str, text: str) -> Decimal:
    if system == "B":
        return system_b.to_major_units(text)
    return Decimal(text)


def _split(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _data_lines(path: Path, system: str) -> tuple[list[str], list[tuple[int, str]]]:
    """Return a file's header fields and its ``(line number, raw line)`` data lines."""
    text = Path(path).read_text(encoding="utf-8")
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    seen_banner = system != "C"

    for number, line in enumerate(text.splitlines(), start=1):
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
        if header is None:
            header = _split(system, line)
            continue
        data.append((number, line))

    if header is None:
        raise LedgerParseError(f"{Path(path).name}: no header row")
    return header, data


def _row_problem(
    system: str,
    row: dict[str, str],
    *,
    date_field: str,
    amount_field: str,
    account_field: str,
    account_code_pattern: re.Pattern[str],
) -> str | None:
    """The reason this row is rejected, or ``None`` when it passes."""
    date_text = row.get(date_field, "")
    try:
        _parse_date(system, date_text)
    except ValueError:
        return f"bad date {date_text!r}"

    amount_text = row.get(amount_field, "")
    try:
        _parse_amount(system, amount_text)
    except (InvalidOperation, LedgerParseError, ValueError):
        return f"bad amount {amount_text!r}"

    account_text = row.get(account_field, "").strip()
    if not account_code_pattern.fullmatch(account_text):
        return f"account code {account_text!r} does not match pattern"

    return None


@dataclass(frozen=True)
class ValidationResult:
    """How many rows of one file were checked and how many were rejected."""

    checked: int
    rejected: int


def validate_file(path: Path, *, account_code_pattern: str) -> ValidationResult:
    """Validate every row of one export file, logging a WARNING for each bad one.

    Raises :class:`OSError` if the file cannot be read, or
    :class:`~ledgerkit.core.records.LedgerParseError` if its export format
    cannot be recognized or it has no header row.
    """
    source = Path(path)
    system = detect_system(source)
    header, data_lines = _data_lines(source, system)
    pattern = re.compile(account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in data_lines:
        checked += 1
        values = _split(system, line)
        if len(values) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d",
                source.name,
                number,
                len(header),
                len(values),
            )
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        reason = _row_problem(
            system,
            row,
            date_field=_DATE_FIELD[system],
            amount_field=_AMOUNT_FIELD[system],
            account_field=_ACCOUNT_FIELD[system],
            account_code_pattern=pattern,
        )
        if reason is not None:
            _log.warning("%s line %d: %s", source.name, number, reason)
            rejected += 1

    return ValidationResult(checked=checked, rejected=rejected)


def validate_files(
    paths: Iterable[str | Path], *, account_code_pattern: str
) -> tuple[int, int, bool]:
    """Validate every file. Returns ``(checked, rejected, all_readable)``."""
    checked = 0
    rejected = 0
    all_readable = True
    for path in paths:
        source = Path(path)
        try:
            result = validate_file(source, account_code_pattern=account_code_pattern)
        except (OSError, LedgerParseError) as exc:
            _log.warning("%s: cannot read file: %s", source, exc)
            all_readable = False
            continue
        checked += result.checked
        rejected += result.rejected
    return checked, rejected, all_readable
