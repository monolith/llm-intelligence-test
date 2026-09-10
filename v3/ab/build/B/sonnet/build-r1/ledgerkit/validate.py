"""Row-by-row checking of export files, for the ``validate`` command.

The three readers in :mod:`ledgerkit.parsers` stop at the first malformed row.
``validate`` has to look at every row and report all the bad ones, so it reads
each file's data lines itself instead of going through those readers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class _SystemSpec:
    columns: tuple[str, ...]
    date_field: str
    date_format: str
    amount_field: str
    account_field: str
    quoted: bool


_SPECS: dict[str, _SystemSpec] = {
    "A": _SystemSpec(system_a.COLUMNS, "posted_on", "%Y-%m-%d", "amount", "account", quoted=True),
    "B": _SystemSpec(system_b.COLUMNS, "value_date", "%Y-%m-%d", "amount", "acct", quoted=False),
    "C": _SystemSpec(system_c.COLUMNS, "txn_date", "%d/%m/%Y", "gross_amount", "ledger_acct", quoted=False),
}


def _data_lines(path: Path, system: str) -> list[tuple[int, str]]:
    """Return ``(line number, raw line)`` for every data line in ``path``.

    Structural lines (comments, banner, header, trailer) are skipped, not
    validated; only the rows a reader would hand back as data are checked.
    """
    name = Path(path).name
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out: list[tuple[int, str]] = []

    if system == "A":
        seen_header = False
        for number, line in enumerate(lines, start=1):
            if not line.strip() or line.startswith(system_a.COMMENT_PREFIX):
                continue
            if not seen_header:
                seen_header = True
                continue
            out.append((number, line))
        if not seen_header:
            raise LedgerParseError(f"{name}: no header row")
        return out

    if system == "B":
        seen_header = False
        for number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            if not seen_header:
                seen_header = True
                continue
            out.append((number, line))
        if not seen_header:
            raise LedgerParseError(f"{name}: no header row")
        return out

    seen_banner = False
    seen_header = False
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            if not stripped.startswith(system_c.BANNER):
                raise LedgerParseError(f"{name} line {number}: expected the Calder banner")
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if not seen_header:
            seen_header = True
            continue
        out.append((number, line))
    if not seen_header:
        raise LedgerParseError(f"{name}: no header row")
    return out


def _row_problems(row_fields: list[str], spec: _SystemSpec, account_pattern: re.Pattern[str]) -> list[str]:
    problems: list[str] = []
    if len(row_fields) != len(spec.columns):
        problems.append(f"expected {len(spec.columns)} fields, found {len(row_fields)}")
        return problems

    row = dict(zip(spec.columns, row_fields, strict=True))

    date_text = row[spec.date_field].strip()
    try:
        datetime.strptime(date_text, spec.date_format)
    except ValueError:
        problems.append(f"date {date_text!r} does not match {spec.date_format}")

    amount_text = row[spec.amount_field].strip()
    try:
        Decimal(amount_text)
    except InvalidOperation:
        problems.append(f"amount {amount_text!r} is not a number")

    account_text = row[spec.account_field].strip()
    if not account_pattern.fullmatch(account_text):
        problems.append(f"account code {account_text!r} does not match {account_pattern.pattern}")

    return problems


def validate_file(path: Path, settings: Settings) -> tuple[int, int]:
    """Check every row of ``path`` and return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError` when the file cannot be read as any known
    export format at all, rather than when an individual row is bad.
    """
    source = Path(path)
    system = detect_system(source)
    spec = _SPECS[system]
    account_pattern = re.compile(settings.account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in _data_lines(source, system):
        checked += 1
        row_fields = fields.split_record(line) if spec.quoted else line.split(",")
        problems = _row_problems(row_fields, spec, account_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source.name, number, "; ".join(problems))

    return checked, rejected
