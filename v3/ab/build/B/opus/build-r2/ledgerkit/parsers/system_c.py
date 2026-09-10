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

from ledgerkit.core import fields, values
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

BANNER = "CALDER EXPORT"
TRAILER_PATTERN = re.compile(r"^==\s*(\d+)\s+rows\s*==$")
SYSTEM_LETTER = "C"
COLUMNS: tuple[str, ...] = ("ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "ccy")
ID_COLUMN = "ref"
DATE_COLUMN = "txn_date"
ACCOUNT_COLUMN = "ledger_acct"
DESCRIPTION_COLUMN = "narrative"
AMOUNT_COLUMN = "gross_amount"
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


def read_lines(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header and every data line of a Calder export, split into fields.

    Each data line comes back with its line number in the file; the banner and the
    trailer are not data lines.  Field counts are not checked here, so a caller
    can report a short or long line instead of stopping at it.
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
            fields.require_columns(header, COLUMNS, source.name)
            continue
        lines.append((number, line.split(",")))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, lines


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of a Calder export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  The ``txn_date`` field is passed
    through exactly as Calder wrote it.
    """
    source = Path(path)
    header, lines = read_lines(source)
    rows: list[dict[str, str]] = []

    # txn_date is written day first, dd/mm/yyyy, which is how Calder has always
    # written it and is not how Ardent or Borough write theirs.  Read month first
    # and the rows past the twelfth of a month blow up, while the rows on or
    # before it quietly land in the wrong month.  The field is handed on as
    # written; :func:`parse_date` is the one place that reads it.
    for number, parts in lines:
        if len(parts) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(parts)}"
            )
        rows.append(dict(zip(header, parts, strict=True)))

    claimed = read_trailer_count(source)
    if claimed is not None and claimed != len(rows):
        _log.warning("%s: trailer claims %d rows, read %d", source.name, claimed, len(rows))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def parse_date(raw: str) -> date:
    """Read a ``txn_date`` field, which Calder writes day first as ``dd/mm/yyyy``."""
    return values.parse_date(raw, DATE_FORMAT)


def parse_amount(raw: str) -> Decimal:
    """Read a ``gross_amount`` field, which Calder writes in decimal dollars."""
    return values.parse_decimal(raw)


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` out of one row from :func:`read_rows`."""
    return Record(
        record_id=row[ID_COLUMN],
        source_system=SYSTEM_LETTER,
        date=parse_date(row[DATE_COLUMN]),
        account_code=row[ACCOUNT_COLUMN],
        account_name=account_name(row[ACCOUNT_COLUMN], unknown_label),
        description=row[DESCRIPTION_COLUMN],
        amount=parse_amount(row[AMOUNT_COLUMN]),
    )
