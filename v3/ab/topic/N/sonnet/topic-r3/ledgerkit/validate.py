"""Row-by-row validation of export files.

Unlike the readers in :mod:`ledgerkit.parsers`, which stop at the first
malformed row, validation has to look at every row and report every reject.
This module walks a file's data lines the same way the matching reader does
(skipping the same preamble, header, and trailer lines) but never raises on a
bad row -- it counts it instead.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)


@dataclass(frozen=True)
class _Spec:
    """Which raw columns a system's validation checks look at."""

    date_column: str
    amount_column: str
    account_column: str


_SPECS: dict[str, _Spec] = {
    "A": _Spec(date_column="posted_on", amount_column="amount", account_column="account"),
    "B": _Spec(date_column="value_date", amount_column="amount", account_column="acct"),
    "C": _Spec(date_column="txn_date", amount_column="gross_amount", account_column="ledger_acct"),
}


def _is_valid_date(system: str, raw: str) -> bool:
    try:
        if system == "C":
            datetime.strptime(raw, "%d/%m/%Y")
        else:
            date.fromisoformat(raw)
    except ValueError:
        return False
    return True


def _is_valid_amount(system: str, raw: str) -> bool:
    text = raw.strip()
    if system == "B":
        try:
            int(text)
        except ValueError:
            return False
        return True
    try:
        Decimal(text)
    except InvalidOperation:
        return False
    return True


def _data_lines(system: str, path: Path) -> tuple[list[str], list[tuple[int, str]]] | None:
    """Return the header and the numbered data lines of an export.

    ``None`` means the file's own shape -- its banner or header row -- could
    not be made out at all; the caller treats that as an unreadable file
    rather than a row level reject.
    """
    numbered = list(enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1))

    if system == "A":
        body = [(n, line) for n, line in numbered if line.strip() and not line.startswith(system_a.COMMENT_PREFIX)]
    elif system == "B":
        body = [(n, line) for n, line in numbered if line.strip()]
    else:
        non_blank = [(n, line) for n, line in numbered if line.strip()]
        if not non_blank or not non_blank[0][1].strip().startswith(system_c.BANNER):
            return None
        body = [
            (n, line) for n, line in non_blank[1:] if not system_c.TRAILER_PATTERN.match(line.strip())
        ]

    if not body:
        return None
    header = fields.split_record(body[0][1])
    return header, body[1:]


def validate_file(path: Path, account_code_pattern: str) -> tuple[int, int] | None:
    """Check every row of one export file.

    Returns ``(checked, rejected)``, or ``None`` when the file could not be
    read at all.
    """
    try:
        system = detect_system(path)
        located = _data_lines(system, path)
    except OSError as exc:
        _log.warning("%s: cannot read file: %s", Path(path).name, exc)
        return None
    if located is None:
        _log.warning("%s: could not make out a header row", Path(path).name)
        return None

    header, data_lines = located
    spec = _SPECS[system]
    pattern = re.compile(account_code_pattern)
    name = Path(path).name

    checked = 0
    rejected = 0
    for number, line in data_lines:
        checked += 1
        values = fields.split_record(line)
        if len(values) != len(header):
            _log.warning("%s line %d: expected %d fields, found %d", name, number, len(header), len(values))
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        problems: list[str] = []
        if not _is_valid_date(system, row[spec.date_column]):
            problems.append(f"unreadable date {row[spec.date_column]!r}")
        if not _is_valid_amount(system, row[spec.amount_column]):
            problems.append(f"unreadable amount {row[spec.amount_column]!r}")
        if not pattern.fullmatch(row[spec.account_column]):
            problems.append(f"account code {row[spec.account_column]!r} does not match {account_code_pattern!r}")

        if problems:
            _log.warning("%s line %d: %s", name, number, "; ".join(problems))
            rejected += 1

    return checked, rejected
