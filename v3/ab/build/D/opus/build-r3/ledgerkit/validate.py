"""Row level checks for the ``validate`` command.

Each data row of an export is checked against its own file's header and its own
system's date and amount formats.  Every bad row is reported, one warning each,
through the project logger; checking never stops at the first one.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import MODULES, detect_system

_log = get_logger(__name__)


def row_problems(
    module: ModuleType, header: list[str], row_values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    """Return what is wrong with one data row, or an empty list when it is fine."""
    if len(row_values) != len(header):
        return [f"expected {len(header)} fields, found {len(row_values)}"]

    row = dict(zip(header, row_values, strict=True))
    problems: list[str] = []
    checks = (
        (module.DATE_COLUMN, module.parse_date),
        (module.AMOUNT_COLUMN, module.parse_amount),
    )
    for column, parse in checks:
        if column not in row:
            problems.append(f"no {column} column in the header")
            continue
        try:
            parse(row[column])
        except LedgerParseError as exc:
            problems.append(f"{column}: {exc}")

    if module.ACCOUNT_COLUMN not in row:
        problems.append(f"no {module.ACCOUNT_COLUMN} column in the header")
    else:
        code = row[module.ACCOUNT_COLUMN].strip()
        if not account_pattern.search(code):
            problems.append(
                f"{module.ACCOUNT_COLUMN}: account code {code!r} does not match {account_pattern.pattern!r}"
            )
    return problems


def validate_file(path: Path, account_code_pattern: str) -> tuple[int, int]:
    """Check every data row of one export and return ``(checked, rejected)``.

    Raises :class:`LedgerParseError`, :class:`OSError` or
    :class:`UnicodeDecodeError` when the file cannot be read at all.
    """
    source = Path(path)
    module = MODULES[detect_system(source)]
    header, lines = module.split_lines(source)
    pattern = re.compile(account_code_pattern)

    checked = 0
    rejected = 0
    for number, row_values in lines:
        checked += 1
        problems = row_problems(module, header, row_values, pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d rejected: %s", source, number, "; ".join(problems))
    return checked, rejected
