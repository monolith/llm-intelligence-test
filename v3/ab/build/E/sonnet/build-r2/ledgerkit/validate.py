"""Row level validation for export files.

The readers in :mod:`ledgerkit.parsers` raise and stop at the first malformed
row. Validation has to look at every row and keep going, so this module walks
each system's file shape (preamble/banner, header, trailer) itself and checks
each data row independently, collecting a warning per bad row instead of
raising.
"""

from __future__ import annotations

import re
from pathlib import Path

from ledgerkit import convert
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.parsers import system_a, system_b, system_c
from ledgerkit.records_io import FIELD_NAMES

_log = get_logger(__name__)


def _data_lines_a(path: Path) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(system_a.COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError(f"{path.name}: no header row")
    return header, data


def _data_lines_b(path: Path) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError(f"{path.name}: no header row")
    return header, data


def _data_lines_c(path: Path) -> tuple[list[str], list[tuple[int, str]]]:
    header: list[str] | None = None
    data: list[tuple[int, str]] = []
    seen_banner = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            if not stripped.startswith(system_c.BANNER):
                raise LedgerParseError(f"{path.name} line {number}: expected the Calder banner")
            seen_banner = True
            continue
        if system_c.TRAILER_PATTERN.match(stripped):
            continue
        if header is None:
            header = line.split(",")
            continue
        data.append((number, line))
    if header is None:
        raise LedgerParseError(f"{path.name}: no header row")
    return header, data


_DATA_LINES = {"A": _data_lines_a, "B": _data_lines_b, "C": _data_lines_c}
_SPLIT = {
    "A": fields.split_record,
    "B": lambda line: line.split(","),
    "C": lambda line: line.split(","),
}


def check_file(path: Path, system: str, account_code_pattern: str) -> tuple[int, int]:
    """Validate one export file already known to be system ``system``.

    Returns ``(checked, rejected)``. Every bad row is logged as a WARNING
    through the project logger and checking continues; nothing here raises
    for a row level problem. A file level problem (missing header, missing
    banner) still raises :class:`LedgerParseError`, since there is no row to
    attach a per-row warning to.
    """
    header, data = _DATA_LINES[system](path)
    split = _SPLIT[system]
    names = FIELD_NAMES[system]
    pattern = re.compile(account_code_pattern)

    checked = 0
    rejected = 0
    for number, line in data:
        checked += 1
        values = split(line)
        if len(values) != len(header):
            _log.warning(
                "%s line %d: expected %d field(s), found %d",
                path.name,
                number,
                len(header),
                len(values),
            )
            rejected += 1
            continue

        row = dict(zip(header, values, strict=True))
        reasons: list[str] = []

        try:
            convert.parse_date(system, row[names["date"]])
        except LedgerParseError as exc:
            reasons.append(str(exc))

        try:
            convert.parse_amount(system, row[names["amount"]])
        except LedgerParseError as exc:
            reasons.append(str(exc))

        account_code = row[names["account"]].strip()
        if not pattern.fullmatch(account_code):
            reasons.append(f"account code {account_code!r} does not match {account_code_pattern!r}")

        if reasons:
            _log.warning("%s line %d: %s", path.name, number, "; ".join(reasons))
            rejected += 1

    return checked, rejected
