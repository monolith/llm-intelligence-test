"""Row-level checks for export files; the engine behind SPEC.md's ``validate`` command.

This deliberately does not reuse :func:`ledgerkit.parsers.read_rows`: that
function raises on the first malformed row, and ``validate`` has to look at
every row in the file regardless of what came before it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)

# Which raw column in each system's rows holds the date, the amount and the
# account code -- the three fields validate has to look inside.
_DATE_FIELD: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_FIELD: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_FIELD: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}


@dataclass(frozen=True)
class ValidationOutcome:
    """How many rows one file's worth of checking looked at, and how many failed."""

    checked: int
    rejected: int


def _parse_date(system: str, text: str) -> date:
    """Parse ``text`` the way ``system`` writes a date; raise ValueError if it cannot."""
    if system == "C":
        return datetime.strptime(text, "%d/%m/%Y").date()
    return date.fromisoformat(text)


def _split_fields(system: str, line: str) -> list[str]:
    """Split one data line the way that system's reader does."""
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _read_header_fields(system: str, path: Path) -> list[str]:
    """Return the column names an export's own header row declares."""
    if system == "A":
        return system_a.read_header(path)

    seen_banner = system != "C"
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if not seen_banner:
            seen_banner = True
            continue
        return line.split(",")
    raise LedgerParseError(f"{Path(path).name}: no header row")


def _data_lines(system: str, path: Path) -> list[tuple[int, str]]:
    """The (line number, raw text) of every data line, preamble/banner/header/trailer skipped."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []
    seen_banner = system != "C"
    seen_header = False
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if not stripped:
            continue
        if system == "A" and stripped.startswith(system_a.COMMENT_PREFIX):
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if system == "C" and system_c.TRAILER_PATTERN.match(stripped):
            continue
        if not seen_header:
            seen_header = True
            continue
        out.append((number, raw))
    return out


def validate_file(path: Path, settings: Settings) -> ValidationOutcome:
    """Check every data row of one export file, logging a WARNING per rejection."""
    source = Path(path)
    system = detect_system(source)
    header = _read_header_fields(system, source)
    date_key = _DATE_FIELD[system]
    amount_key = _AMOUNT_FIELD[system]
    account_key = _ACCOUNT_FIELD[system]

    checked = 0
    rejected = 0
    for number, raw_line in _data_lines(system, source):
        checked += 1
        values = _split_fields(system, raw_line)

        if len(values) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d", source.name, number, len(header), len(values)
            )
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        problem: str | None = None

        try:
            _parse_date(system, row[date_key])
        except ValueError:
            problem = f"invalid date {row[date_key]!r}"

        if problem is None:
            try:
                Decimal(row[amount_key])
            except InvalidOperation:
                problem = f"invalid amount {row[amount_key]!r}"

        if problem is None and re.fullmatch(settings.account_code_pattern, row[account_key]) is None:
            problem = f"account code {row[account_key]!r} does not match {settings.account_code_pattern!r}"

        if problem is not None:
            _log.warning("%s line %d: %s", source.name, number, problem)
            rejected += 1

    return ValidationOutcome(checked=checked, rejected=rejected)
