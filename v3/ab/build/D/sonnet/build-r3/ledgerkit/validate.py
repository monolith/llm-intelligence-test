"""Row by row validation of export files, for the ``validate`` command.

Unlike the readers in :mod:`ledgerkit.parsers`, which stop at the first
malformed line, the scanners here check every data row of a file and hand back
every problem they found, so a run can report everything wrong with a file in
one pass.
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
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class RowIssue:
    """One rejected row: the line it came from and why it was rejected."""

    line: int
    reason: str


def scan_file(path: Path, pattern: re.Pattern[str]) -> tuple[int, list[RowIssue]]:
    """Check every data row of an export file.

    Returns the number of rows checked and the issues found.  Raises
    :class:`LedgerParseError` or :class:`OSError` when the file cannot be read
    at all, for instance because it has no header row.
    """
    system = detect_system(path)
    if system == "A":
        return _scan_a(path, pattern)
    if system == "B":
        return _scan_b(path, pattern)
    return _scan_c(path, pattern)


def _parse_iso_date(text: str) -> None:
    date.fromisoformat(text.strip())


def _parse_calder_date(text: str) -> None:
    datetime.strptime(text.strip(), "%d/%m/%Y")


def _check_row(
    header: list[str],
    values: list[str],
    *,
    date_column: str,
    amount_column: str,
    account_column: str,
    pattern: re.Pattern[str],
    parse_date: Callable[[str], None],
) -> str | None:
    if len(values) != len(header):
        return f"expected {len(header)} field(s), found {len(values)}"

    row = dict(zip(header, values, strict=True))
    reasons: list[str] = []

    date_text = row.get(date_column, "")
    try:
        parse_date(date_text)
    except ValueError:
        reasons.append(f"unreadable date {date_text!r}")

    amount_text = row.get(amount_column, "")
    try:
        Decimal(amount_text.strip())
    except InvalidOperation:
        reasons.append(f"unreadable amount {amount_text!r}")

    account_text = row.get(account_column, "").strip()
    if not pattern.fullmatch(account_text):
        reasons.append(f"account code {account_text!r} does not match the configured pattern")

    return "; ".join(reasons) if reasons else None


def _scan_a(path: Path, pattern: re.Pattern[str]) -> tuple[int, list[RowIssue]]:
    source = Path(path)
    header: list[str] | None = None
    checked = 0
    issues: list[RowIssue] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        checked += 1
        values = fields.split_record(line)
        reason = _check_row(
            header,
            values,
            date_column="posted_on",
            amount_column="amount",
            account_column="account",
            pattern=pattern,
            parse_date=_parse_iso_date,
        )
        if reason:
            issues.append(RowIssue(number, reason))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return checked, issues


def _scan_b(path: Path, pattern: re.Pattern[str]) -> tuple[int, list[RowIssue]]:
    source = Path(path)
    header: list[str] | None = None
    checked = 0
    issues: list[RowIssue] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue
        checked += 1
        values = line.split(",")
        reason = _check_row(
            header,
            values,
            date_column="value_date",
            amount_column="amount",
            account_column="acct",
            pattern=pattern,
            parse_date=_parse_iso_date,
        )
        if reason:
            issues.append(RowIssue(number, reason))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return checked, issues


def _scan_c(path: Path, pattern: re.Pattern[str]) -> tuple[int, list[RowIssue]]:
    source = Path(path)
    header: list[str] | None = None
    checked = 0
    issues: list[RowIssue] = []
    seen_banner = False

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            if not stripped.startswith(system_c.BANNER):
                raise LedgerParseError(f"{source.name} line {number}: expected the Calder banner")
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if header is None:
            header = line.split(",")
            continue
        checked += 1
        values = line.split(",")
        reason = _check_row(
            header,
            values,
            date_column="txn_date",
            amount_column="gross_amount",
            account_column="ledger_acct",
            pattern=pattern,
            parse_date=_parse_calder_date,
        )
        if reason:
            issues.append(RowIssue(number, reason))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return checked, issues
