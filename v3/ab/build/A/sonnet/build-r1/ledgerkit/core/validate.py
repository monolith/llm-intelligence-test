"""Permissive, whole-file row checking for ``validate``.

The readers in :mod:`ledgerkit.parsers` stop at the first bad row, which is
right for ``ingest`` but wrong here: ``validate`` has to look at every row and
report on each one that fails, rather than stopping at the first.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)


def _bad_date_iso(text: str) -> str | None:
    try:
        date.fromisoformat(text.strip())
    except ValueError:
        return f"date {text!r} is not a valid ISO date"
    return None


def _bad_date_dmy(text: str) -> str | None:
    try:
        datetime.strptime(text.strip(), "%d/%m/%Y")
    except ValueError:
        return f"date {text!r} is not a valid DD/MM/YYYY date"
    return None


def _bad_amount_decimal(text: str) -> str | None:
    try:
        Decimal(text.strip())
    except InvalidOperation:
        return f"amount {text!r} is not a number"
    return None


def _bad_amount_cents(text: str) -> str | None:
    try:
        int(text.strip())
    except ValueError:
        return f"amount {text!r} is not an integer number of cents"
    return None


def _bad_account(text: str, pattern: re.Pattern[str]) -> str | None:
    if pattern.fullmatch(text.strip()) is None:
        return f"account code {text!r} does not match the configured pattern"
    return None


def _scan_a(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    checked = 0
    rejected = 0
    header: list[str] | None = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        checked += 1
        values = fields.split_record(line)
        if len(values) != len(header):
            reason: str | None = f"expected {len(header)} fields, found {len(values)}"
        else:
            row = dict(zip(header, values, strict=True))
            reason = (
                _bad_date_iso(row["posted_on"])
                or _bad_amount_decimal(row["amount"])
                or _bad_account(row["account"], pattern)
            )
        if reason:
            rejected += 1
            _log.warning("%s line %d: %s", path.name, number, reason)
    return checked, rejected


def _scan_b(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    checked = 0
    rejected = 0
    header: list[str] | None = None
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue
        checked += 1
        values = line.split(",")
        if len(values) != len(header):
            reason: str | None = f"expected {len(header)} fields, found {len(values)}"
        else:
            row = dict(zip(header, values, strict=True))
            reason = (
                _bad_date_iso(row["value_date"])
                or _bad_amount_cents(row["amount"])
                or _bad_account(row["acct"], pattern)
            )
        if reason:
            rejected += 1
            _log.warning("%s line %d: %s", path.name, number, reason)
    return checked, rejected


def _scan_c(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    checked = 0
    rejected = 0
    header: list[str] | None = None
    seen_banner = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
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
        checked += 1
        values = line.split(",")
        if len(values) != len(header):
            reason: str | None = f"expected {len(header)} fields, found {len(values)}"
        else:
            row = dict(zip(header, values, strict=True))
            reason = (
                _bad_date_dmy(row["txn_date"])
                or _bad_amount_decimal(row["gross_amount"])
                or _bad_account(row["ledger_acct"], pattern)
            )
        if reason:
            rejected += 1
            _log.warning("%s line %d: %s", path.name, number, reason)
    return checked, rejected


def scan_file(path: Path, pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export file against ``pattern``.

    Returns ``(checked, rejected)``.  Raises
    :class:`~ledgerkit.core.records.LedgerParseError` or :class:`OSError` when
    the file cannot be read at all.
    """
    system = detect_system(path)
    if system == "A":
        return _scan_a(path, pattern)
    if system == "B":
        return _scan_b(path, pattern)
    return _scan_c(path, pattern)
