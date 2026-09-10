"""``validate`` — reject malformed rows without writing anything.

Unlike the readers under :mod:`ledgerkit.parsers`, which stop at the first bad
row, this module checks every row of every file and reports every rejection.
It re-does the shape parsing the readers do, because that per-row-tolerant
walk is not something ``read_rows`` offers.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class ValidationResult:
    """How many rows one run of ``validate`` looked at and rejected."""

    checked: int
    rejected: int
    unreadable: bool


def _reject(path: Path, line_number: int, reason: str) -> None:
    _log.warning("%s line %d: %s", Path(path).name, line_number, reason)


def _row_reasons(
    row: dict[str, str],
    *,
    date_field: str,
    amount_field: str,
    account_field: str,
    parse_date: Callable[[str], date],
    settings: Settings,
) -> list[str]:
    """Everything wrong with one already field-split row, if anything."""
    reasons: list[str] = []

    raw_date = row[date_field]
    try:
        parse_date(raw_date.strip())
    except ValueError:
        reasons.append(f"date {raw_date!r} is not a valid date")

    raw_amount = row[amount_field]
    try:
        Decimal(raw_amount.strip())
    except (InvalidOperation, ValueError):
        reasons.append(f"amount {raw_amount!r} is not a number")

    code = row[account_field].strip()
    if re.fullmatch(settings.account_code_pattern, code) is None:
        reasons.append(f"account code {code!r} does not match {settings.account_code_pattern!r}")

    return reasons


def _validate_system_a(path: Path, settings: Settings) -> tuple[int, int]:
    checked = 0
    rejected = 0
    header: list[str] | None = None

    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue

        values = fields.split_record(line)
        checked += 1
        if len(values) != len(header):
            _reject(path, number, f"expected {len(header)} fields, found {len(values)}")
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        reasons = _row_reasons(
            row,
            date_field="posted_on",
            amount_field="amount",
            account_field="account",
            parse_date=date.fromisoformat,
            settings=settings,
        )
        if reasons:
            _reject(path, number, "; ".join(reasons))
            rejected += 1

    if header is None:
        raise LedgerParseError(f"{Path(path).name}: no header row")
    return checked, rejected


def _validate_system_b(path: Path, settings: Settings) -> tuple[int, int]:
    checked = 0
    rejected = 0
    header: list[str] | None = None

    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue

        values = line.split(",")
        checked += 1
        if len(values) != len(header):
            _reject(path, number, f"expected {len(header)} fields, found {len(values)}")
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        reasons = _row_reasons(
            row,
            date_field="value_date",
            amount_field="amount",
            account_field="acct",
            parse_date=date.fromisoformat,
            settings=settings,
        )
        if reasons:
            _reject(path, number, "; ".join(reasons))
            rejected += 1

    if header is None:
        raise LedgerParseError(f"{Path(path).name}: no header row")
    return checked, rejected


def _parse_calder_date(text: str) -> date:
    return datetime.strptime(text, "%d/%m/%Y").date()


def _validate_system_c(path: Path, settings: Settings) -> tuple[int, int]:
    checked = 0
    rejected = 0
    header: list[str] | None = None
    seen_banner = False

    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
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

        values = line.split(",")
        checked += 1
        if len(values) != len(header):
            _reject(path, number, f"expected {len(header)} fields, found {len(values)}")
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        reasons = _row_reasons(
            row,
            date_field="txn_date",
            amount_field="gross_amount",
            account_field="ledger_acct",
            parse_date=_parse_calder_date,
            settings=settings,
        )
        if reasons:
            _reject(path, number, "; ".join(reasons))
            rejected += 1

    if header is None:
        raise LedgerParseError(f"{Path(path).name}: no header row")
    return checked, rejected


def validate_file(path: Path, settings: Settings) -> tuple[int, int]:
    """Validate every row of one export file.  Returns ``(checked, rejected)``."""
    system = detect_system(path)
    if system == "A":
        return _validate_system_a(path, settings)
    if system == "B":
        return _validate_system_b(path, settings)
    return _validate_system_c(path, settings)


def validate_files(paths: list[Path], settings: Settings) -> ValidationResult:
    """Validate every row of every file in ``paths``."""
    checked = 0
    rejected = 0
    unreadable = False
    for path in paths:
        try:
            file_checked, file_rejected = validate_file(path, settings)
        except (LedgerParseError, OSError) as exc:
            _log.warning("%s: could not be read: %s", Path(path).name, exc)
            unreadable = True
            continue
        checked += file_checked
        rejected += file_rejected
    return ValidationResult(checked=checked, rejected=rejected, unreadable=unreadable)
