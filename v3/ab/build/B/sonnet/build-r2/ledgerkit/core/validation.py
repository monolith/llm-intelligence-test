"""Row-by-row validation of export files, independent of the readers in
``ledgerkit/parsers``.

The readers in :mod:`ledgerkit.parsers` raise on the first malformed row they
meet, which suits ``ingest`` but not ``validate``: SPEC.md requires checking
every row in a file even after one has already failed.  This module walks a
file's data lines itself so a bad row does not stop the ones after it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterator

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)

# Which raw column in each system's header carries the date, the amount and
# the account code, keyed by the letter detect_system returns.
_SYSTEM_KEYS: dict[str, dict[str, str]] = {
    "A": {"date": "posted_on", "amount": "amount", "account": "account"},
    "B": {"date": "value_date", "amount": "amount", "account": "acct"},
    "C": {"date": "txn_date", "amount": "gross_amount", "account": "ledger_acct"},
}


@dataclass(frozen=True)
class ValidationResult:
    """How many rows a single file's validation checked and rejected."""

    checked: int
    rejected: int


def _split(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _iter_lines(path: Path, system: str) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, line)`` for a file's header and data lines only."""
    text = Path(path).read_text(encoding="utf-8")
    if system == "A":
        for number, line in enumerate(text.splitlines(), start=1):
            if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
                continue
            yield number, line
        return
    if system == "B":
        for number, line in enumerate(text.splitlines(), start=1):
            if line.strip():
                yield number, line
        return

    seen_banner = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        yield number, line


def _parse_date(system: str, text: str) -> date:
    if system == "C":
        day, month, year = text.split("/")
        return date(int(year), int(month), int(day))
    return date.fromisoformat(text)


def validate_file(path: Path, account_code_pattern: str) -> ValidationResult:
    """Check every data row of one export file against the four SPEC rules.

    Every rejection is logged as a ``WARNING`` through the project logger,
    naming the file, the line number and what was wrong.  A row that fails
    more than one rule is still counted as one rejected row.
    """
    source = Path(path)
    system = detect_system(source)
    keys = _SYSTEM_KEYS[system]
    pattern = re.compile(account_code_pattern)

    header: list[str] | None = None
    checked = 0
    rejected = 0

    for number, line in _iter_lines(source, system):
        if header is None:
            header = _split(system, line)
            continue

        checked += 1
        values = _split(system, line)
        if len(values) != len(header):
            rejected += 1
            _log.warning(
                "%s line %d: expected %d fields, found %d", source.name, number, len(header), len(values)
            )
            continue

        row = dict(zip(header, values, strict=True))
        problems: list[str] = []

        date_text = row.get(keys["date"], "")
        try:
            _parse_date(system, date_text.strip())
        except (ValueError, KeyError):
            problems.append(f"date {date_text!r} is not valid")

        amount_text = row.get(keys["amount"], "")
        try:
            Decimal(amount_text.strip())
        except (InvalidOperation, KeyError):
            problems.append(f"amount {amount_text!r} is not a number")

        code = row.get(keys["account"], "").strip()
        if not pattern.fullmatch(code):
            problems.append(f"account code {code!r} does not match {account_code_pattern!r}")

        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source.name, number, "; ".join(problems))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")

    return ValidationResult(checked=checked, rejected=rejected)
