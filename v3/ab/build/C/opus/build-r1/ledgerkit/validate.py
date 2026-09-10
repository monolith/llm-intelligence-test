"""Checking export files row by row, without writing anything.

A row is rejected when it does not have as many fields as its header, when its
date cannot be read in the layout its system writes, when its amount cannot be
read as a number in its system's units, or when its account code does not match
the ``[validate] account_code_pattern`` setting.  Each rejected row gets one
warning through the project logger, naming the file, the line and every problem
found on it, and checking carries on to the end of the file.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import read_numbered, system_module

_log = get_logger(__name__)


@dataclass(frozen=True)
class FileCheck:
    """What validating one export found."""

    checked: int
    rejected: int


def row_problems(
    module: ModuleType,
    header: list[str],
    values: list[str],
    account_code_pattern: re.Pattern[str],
) -> list[str]:
    """Everything wrong with one data row of the system ``module`` reads.

    An empty list means the row passes.  A row with the wrong number of fields
    reports only that, because its other columns cannot be trusted to be where
    the header says they are.
    """
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]

    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    try:
        module.parse_date(row[module.DATE_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        module.parse_amount(row[module.AMOUNT_COLUMN])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[module.ACCOUNT_COLUMN]
    if account_code_pattern.search(code) is None:
        problems.append(f"account code {code!r} does not match {account_code_pattern.pattern!r}")
    return problems


def check_file(path: Path, account_code_pattern: re.Pattern[str]) -> FileCheck:
    """Check every data row of one export, logging a warning for each rejected row.

    Raises :class:`~ledgerkit.core.records.LedgerParseError` or :class:`OSError`
    when the file cannot be read at all.
    """
    source = Path(path)
    system, header, rows = read_numbered(source)
    module = system_module(system)
    needed = (module.DATE_COLUMN, module.AMOUNT_COLUMN, module.ACCOUNT_COLUMN)
    missing = [column for column in needed if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in rows:
        problems = row_problems(module, header, values, account_code_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d rejected: %s", source, number, "; ".join(problems))
    _log.info("checked %d row(s) in %s, rejected %d", len(rows), source.name, rejected)
    return FileCheck(checked=len(rows), rejected=rejected)
