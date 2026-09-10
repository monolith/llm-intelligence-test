"""Row by row checks on export files.

The readers stop at the first row they cannot shape, which is right for
``ingest`` and wrong for ``validate``: validation looks at every row and reports
each bad one.  It uses the readers' shape-only :func:`read_lines` and their own
date and amount parsers, so it judges each field the way that system writes it.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import READERS, detect_system

_log = get_logger(__name__)


def row_problems(
    reader: ModuleType, header: list[str], values: list[str], account_code_pattern: re.Pattern[str]
) -> list[str]:
    """Return what is wrong with one data line; an empty list means it passed."""
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    try:
        reader.parse_date(row[reader.DATE_FIELD])
    except LedgerParseError as exc:
        problems.append(str(exc))
    try:
        reader.parse_amount(row[reader.AMOUNT_FIELD])
    except LedgerParseError as exc:
        problems.append(str(exc))
    code = row[reader.ACCOUNT_FIELD]
    if not account_code_pattern.search(code):
        problems.append(f"account code {code!r} does not match {account_code_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_code_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(checked, rejected)``.

    One warning is logged per rejected row, naming the file and line.  Raises
    :class:`LedgerParseError` or :class:`OSError` when the file cannot be read at
    all.
    """
    source = Path(path)
    reader = READERS[detect_system(source)]
    header, lines = reader.read_lines(source)
    missing = [
        column
        for column in (reader.DATE_FIELD, reader.AMOUNT_FIELD, reader.ACCOUNT_FIELD)
        if column not in header
    ]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    rejected = 0
    for number, values in lines:
        problems = row_problems(reader, header, values, account_code_pattern)
        if problems:
            rejected += 1
            _log.warning("%s line %d: %s", source.name, number, "; ".join(problems))
    return len(lines), rejected
