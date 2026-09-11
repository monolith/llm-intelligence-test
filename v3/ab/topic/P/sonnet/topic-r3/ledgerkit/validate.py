"""Checking export files for malformed rows without writing anything.

Unlike :func:`ledgerkit.parsers.read_rows`, which stops at the first malformed
row, :func:`validate_file` checks every row of a file and reports every
problem it finds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

_READERS = {"A": system_a, "B": system_b, "C": system_c}
_DATE_COLUMN = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_AMOUNT_COLUMN = {"A": "amount", "B": "amount", "C": "gross_amount"}
_ACCOUNT_COLUMN = {"A": "account", "B": "acct", "C": "ledger_acct"}
_DATE_PARSERS = {"A": system_a.parse_date, "B": system_b.parse_date, "C": system_c.parse_date}
_AMOUNT_PARSERS = {"A": system_a.parse_amount, "B": system_b.to_major_units, "C": system_c.parse_amount}


@dataclass(frozen=True)
class ValidationResult:
    """How many rows one file's validation run checked and rejected."""

    checked: int
    rejected: int
    file_unreadable: bool


def _split_fields(system: str, line: str) -> list[str]:
    if system == "A":
        return fields.split_record(line)
    return line.split(",")


def _row_problems(system: str, row: dict[str, str], pattern: re.Pattern[str]) -> list[str]:
    problems: list[str] = []

    try:
        _DATE_PARSERS[system](row[_DATE_COLUMN[system]])
    except LedgerParseError:
        problems.append("bad date")

    try:
        _AMOUNT_PARSERS[system](row[_AMOUNT_COLUMN[system]])
    except LedgerParseError:
        problems.append("bad amount")

    if not pattern.match(row[_ACCOUNT_COLUMN[system]].strip()):
        problems.append("bad account code")

    return problems


def validate_file(path: Path, settings: Settings) -> ValidationResult:
    """Check one export file's rows against the four rules in ``SPEC.md``.

    Every rejected row is logged as one ``WARNING`` naming the file, the line
    number and what was wrong with it.  Checking continues past a bad row.
    """
    source = Path(path)
    try:
        system = detect_system(source)
        module = _READERS[system]
        header = module.read_header(source)
        data_lines = list(module.iter_data_lines(source))
    except (LedgerParseError, OSError) as exc:
        _log.warning("%s: cannot read file: %s", source, exc)
        return ValidationResult(checked=0, rejected=0, file_unreadable=True)

    pattern = re.compile(settings.account_code_pattern)
    checked = 0
    rejected = 0
    for number, line in data_lines:
        checked += 1
        values = _split_fields(system, line)
        if len(values) != len(header):
            _log.warning(
                "%s line %d: expected %d fields, found %d", source.name, number, len(header), len(values)
            )
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        problems = _row_problems(system, row, pattern)
        if problems:
            _log.warning("%s line %d: %s", source.name, number, "; ".join(problems))
            rejected += 1

    return ValidationResult(checked=checked, rejected=rejected, file_unreadable=False)
