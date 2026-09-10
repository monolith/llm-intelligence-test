"""Row level validation for export files.

Unlike the readers under ``ledgerkit.parsers``, which stop at the first
malformed line, :func:`validate_file` checks every data row in a file and
keeps going past a bad one, because SPEC.md wants every row checked, not just
the first failure. Each rejected row is logged as one ``WARNING`` through the
project logger; nothing here prints.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields as fieldutil
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def _reject(path: Path, line_number: int, reason: str) -> None:
    _log.warning("%s line %d: %s", path.name, line_number, reason)


def _row_is_valid(
    path: Path,
    line_number: int,
    row: dict[str, str],
    *,
    date_field: str,
    amount_field: str,
    account_field: str,
    parse_date: Callable[[str], date],
    settings: Settings,
) -> bool:
    date_text = row[date_field].strip()
    try:
        parse_date(date_text)
    except ValueError:
        _reject(path, line_number, f"{date_field} {date_text!r} is not a valid date")
        return False

    amount_text = row[amount_field].strip()
    try:
        Decimal(amount_text)
    except InvalidOperation:
        _reject(path, line_number, f"{amount_field} {amount_text!r} is not a number")
        return False

    code = row[account_field].strip()
    if re.fullmatch(settings.account_code_pattern, code) is None:
        _reject(path, line_number, f"{account_field} {code!r} does not match the account code pattern")
        return False

    return True


def _iso_date(text: str) -> date:
    return date.fromisoformat(text)


def _dmy_date(text: str) -> date:
    return datetime.strptime(text, "%d/%m/%Y").date()


def _validate_system_a(path: Path, settings: Settings) -> tuple[int, int]:
    header: list[str] | None = None
    checked = 0
    rejected = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fieldutil.split_record(line)
            continue

        checked += 1
        values = fieldutil.split_record(line)
        if len(values) != len(header):
            _reject(path, number, f"expected {len(header)} fields, found {len(values)}")
            rejected += 1
            continue
        row = dict(zip(header, values, strict=True))
        if not _row_is_valid(
            path, number, row,
            date_field="posted_on", amount_field="amount", account_field="account",
            parse_date=_iso_date, settings=settings,
        ):
            rejected += 1

    if header is None:
        raise LedgerParseError(f"{path.name}: no header row")
    return checked, rejected


def _validate_system_b(path: Path, settings: Settings) -> tuple[int, int]:
    header: list[str] | None = None
    checked = 0
    rejected = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue

        checked += 1
        values = line.split(",")
        if len(values) != len(header):
            _reject(path, number, f"expected {len(header)} fields, found {len(values)}")
            rejected += 1
            continue
        row = dict(zip(header, values, strict=True))
        if not _row_is_valid(
            path, number, row,
            date_field="value_date", amount_field="amount", account_field="acct",
            parse_date=_iso_date, settings=settings,
        ):
            rejected += 1

    if header is None:
        raise LedgerParseError(f"{path.name}: no header row")
    return checked, rejected


def _validate_system_c(path: Path, settings: Settings) -> tuple[int, int]:
    header: list[str] | None = None
    checked = 0
    rejected = 0
    seen_banner = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            if not stripped.startswith(system_c.BANNER):
                raise LedgerParseError(f"{path.name} line {number}: expected the Calder banner")
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if header is None:
            header = line.split(",")
            continue

        checked += 1
        values = line.split(",")
        if len(values) != len(header):
            _reject(path, number, f"expected {len(header)} fields, found {len(values)}")
            rejected += 1
            continue
        row = dict(zip(header, values, strict=True))
        if not _row_is_valid(
            path, number, row,
            date_field="txn_date", amount_field="gross_amount", account_field="ledger_acct",
            parse_date=_dmy_date, settings=settings,
        ):
            rejected += 1

    if header is None:
        raise LedgerParseError(f"{path.name}: no header row")
    return checked, rejected


def validate_file(path: Path, settings: Settings) -> tuple[int, int]:
    """Check every data row of ``path`` and return ``(checked, rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot
    be read at all - an unrecognized format, or a missing header or banner.
    """
    system = detect_system(path)
    if system == "A":
        return _validate_system_a(path, settings)
    if system == "B":
        return _validate_system_b(path, settings)
    return _validate_system_c(path, settings)
