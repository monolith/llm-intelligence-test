"""Reader for Calder (System C) exports.

A Calder file carries a banner line, a header row, the rows, and a trailer that
repeats the row count::

    CALDER EXPORT v3
    ref,txn_date,ledger_acct,narrative,gross_amount,ccy
    C-0401,02/01/2026,4100,Container unload allowance,386.54,USD
    == 39 rows ==

``gross_amount`` is a decimal number of dollars with two places.  The trailer is
checked against the number of rows actually read, and a mismatch is a warning
rather than an error, because Calder has been known to miscount its own file
when an operator cancels an export halfway through.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import values
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger

_log = get_logger(__name__)

BANNER = "CALDER EXPORT"
TRAILER_PATTERN = re.compile(r"^==\s*(\d+)\s+rows\s*==$")
COLUMNS: tuple[str, ...] = ("ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "ccy")

ID_COLUMN = "ref"
DATE_COLUMN = "txn_date"
ACCOUNT_COLUMN = "ledger_acct"
DESCRIPTION_COLUMN = "narrative"
AMOUNT_COLUMN = "gross_amount"
# txn_date is written day first, dd/mm/yyyy, which is how Calder has always
# written it and is not how Ardent or Borough write theirs.  Read month first
# and the rows past the twelfth of a month blow up, while the rows on or before
# it quietly land in the wrong month.
DATE_FORMAT = "%d/%m/%Y"


def read_trailer_count(path: Path) -> int | None:
    """Return the row count Calder claims in its trailer, or ``None`` if absent."""
    for line in reversed(Path(path).read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        match = TRAILER_PATTERN.match(line.strip())
        if match:
            return int(match.group(1))
        return None
    return None


def read_fields(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header and every data line of a Calder export, split into fields.

    Each data line comes with its line number in the file.  The banner and the
    trailer are not data lines.  Field counts are not checked here.
    """
    source = Path(path)
    header: list[str] | None = None
    lines: list[tuple[int, list[str]]] = []
    seen_banner = False

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            if not stripped.startswith(BANNER):
                raise LedgerParseError(f"{source.name} line {number}: expected the Calder banner")
            seen_banner = True
            continue
        if TRAILER_PATTERN.match(stripped):
            continue
        if header is None:
            header = line.split(",")
            continue
        lines.append((number, line.split(",")))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, lines


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of a Calder export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  The ``txn_date`` field is passed
    through exactly as Calder wrote it; :func:`parse_date` reads it.
    """
    source = Path(path)
    header, lines = read_fields(source)
    rows: list[dict[str, str]] = []
    for number, row_values in lines:
        if len(row_values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(row_values)}"
            )
        rows.append(dict(zip(header, row_values, strict=True)))

    claimed = read_trailer_count(source)
    if claimed is not None and claimed != len(rows):
        _log.warning("%s: trailer claims %d rows, read %d", source.name, claimed, len(rows))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def parse_date(raw: str) -> date:
    """Read one Calder ``txn_date`` field, which is day first: ``dd/mm/yyyy``."""
    return values.parse_date(raw, DATE_FORMAT, "Calder txn_date")


def parse_amount(raw: str) -> Decimal:
    """Read one Calder ``gross_amount`` field, which is already in dollars."""
    return values.parse_decimal(raw, "Calder gross_amount")
