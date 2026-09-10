"""Row by row checks of export files, for ``validate``.

A row is rejected when its field count does not match the header, when its date
is not a date in the format its own system writes, when its amount is not a
number in its system's units, or when its account code does not match the
configured pattern.  Each rejected row gets one warning through the project
logger; nothing here prints.
"""

from __future__ import annotations

import re
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import MODULES, detect_system

_log = get_logger(__name__)


def validate_export(path: Path, account_code_pattern: re.Pattern[str]) -> tuple[int, int]:
    """Check every data row of one export and return ``(rows checked, rows rejected)``.

    Raises :class:`LedgerParseError` or :class:`OSError` when the file cannot be
    read as an export at all.
    """
    source = Path(path)
    module = MODULES[detect_system(source)]
    header, lines = module.read_lines(source)
    wanted = (module.DATE_COLUMN, module.AMOUNT_COLUMN, module.ACCOUNT_COLUMN)
    missing = [column for column in wanted if column not in header]
    if missing:
        raise LedgerParseError(f"{source.name}: header has no {', '.join(missing)} column")

    checked = 0
    rejected = 0
    for number, values in lines:
        checked += 1
        problems: list[str] = []
        if len(values) != len(header):
            problems.append(f"expected {len(header)} fields, found {len(values)}")
        else:
            row = dict(zip(header, values, strict=True))
            for parse, column in ((module.parse_date, module.DATE_COLUMN), (module.parse_amount, module.AMOUNT_COLUMN)):
                try:
                    parse(row[column])
                except LedgerParseError as exc:
                    problems.append(str(exc))
            code = row[module.ACCOUNT_COLUMN]
            if not account_code_pattern.search(code):
                problems.append(f"account code {code!r} does not match {account_code_pattern.pattern!r}")
        if problems:
            rejected += 1
            _log.warning("%s line %d rejected: %s", source, number, "; ".join(problems))
    return checked, rejected
