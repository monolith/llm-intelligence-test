"""Row-by-row checks on export files for ``validate``.

The readers stop at the first row they cannot use, which is right for ingest and
wrong here: validation has to look at every row and say which ones are bad.  So
this module walks each file itself, a physical line at a time, skipping the same
structure lines the readers skip, and borrows only the readers' knowledge of
column names and of how each system writes dates and amounts.
"""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.ledger import READERS, record_fields
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_c

_log = get_logger(__name__)


def _row_problems(
    reader: ModuleType, header: list[str], values: list[str], account_pattern: re.Pattern[str]
) -> list[str]:
    if len(values) != len(header):
        return [f"expected {len(header)} fields, found {len(values)}"]
    row = dict(zip(header, values, strict=True))
    problems: list[str] = []
    for column, parse in ((reader.DATE_FIELD, reader.parse_date), (reader.AMOUNT_FIELD, reader.parse_amount)):
        try:
            parse(row[column])
        except LedgerParseError as exc:
            problems.append(str(exc))
    code = row[reader.ACCOUNT_FIELD]
    if not account_pattern.search(code):
        problems.append(f"account code {code!r} does not match {account_pattern.pattern!r}")
    return problems


def validate_file(path: Path, account_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(checked, rejected)``.

    Each rejected row gets one warning naming the file, the line and what was
    wrong.  Raises :class:`LedgerParseError` or :class:`OSError` when the file
    cannot be read as an export at all.
    """
    source = Path(path)
    system = detect_system(source)
    reader = READERS[system]
    header: list[str] | None = None
    seen_banner = system != "C"
    checked = 0
    rejected = 0

    with source.open("r", encoding="utf-8") as handle:
        for number, raw_line in enumerate(handle, start=1):
            line = raw_line.rstrip("\r\n")
            stripped = line.strip()
            if not stripped:
                continue
            if system == "A" and line.startswith(system_a.COMMENT_PREFIX):
                continue
            if not seen_banner:
                seen_banner = True
                continue
            if system == "C" and system_c.TRAILER_PATTERN.match(stripped):
                continue
            if header is None:
                header = fields.split_record(line)
                missing = [column for column in record_fields(reader) if column not in header]
                if missing:
                    raise LedgerParseError(f"{source} line {number}: header has no {', '.join(missing)} column")
                continue

            checked += 1
            problems = _row_problems(reader, header, fields.split_record(line), account_pattern)
            if problems:
                rejected += 1
                _log.warning("%s line %d: %s", source, number, "; ".join(problems))

    if header is None:
        raise LedgerParseError(f"{source}: no header row")
    return checked, rejected
