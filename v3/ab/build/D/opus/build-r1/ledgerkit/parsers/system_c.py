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
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger

_log = get_logger(__name__)

BANNER = "CALDER EXPORT"
TRAILER_PATTERN = re.compile(r"^==\s*(\d+)\s+rows\s*==$")
COLUMNS: tuple[str, ...] = ("ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "ccy")
ID_FIELD = "ref"
DATE_FIELD = "txn_date"
ACCOUNT_FIELD = "ledger_acct"
DESCRIPTION_FIELD = "narrative"
AMOUNT_FIELD = "gross_amount"


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


def split_body(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Split a Calder export into its header and its data lines.

    The banner and the trailer are dropped.  Each data line comes back as
    ``(line number, fields)``, not yet checked against the header.
    """
    source = Path(path)
    header: list[str] | None = None
    body: list[tuple[int, list[str]]] = []
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
        body.append((number, line.split(",")))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, body


def parse_date(raw: str) -> date:
    """Turn one ``txn_date`` field into a date.

    Calder writes day first, ``dd/mm/yyyy``: ``02/01/2026`` is the second of
    January.
    """
    try:
        return datetime.strptime(raw.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise LedgerParseError(f"Calder date {raw!r} is not dd/mm/yyyy") from exc


def parse_amount(raw: str) -> Decimal:
    """Turn one ``gross_amount`` field, decimal dollars, into dollars."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"Calder amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"Calder amount {raw!r} is not a number")
    return value


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of a Calder export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  The ``txn_date`` field is passed
    through exactly as Calder wrote it.
    """
    source = Path(path)
    header, body = split_body(source)
    rows: list[dict[str, str]] = []

    for number, values in body:
        # txn_date is written day first, dd/mm/yyyy, which is how Calder has
        # always written it and is not how Ardent or Borough write theirs.  Read
        # month first and the rows past the twelfth of a month blow up, while the
        # rows on or before it quietly land in the wrong month.  The field is
        # handed on as written; parse_date is where it gets read.
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))

    claimed = read_trailer_count(source)
    if claimed is not None and claimed != len(rows):
        _log.warning("%s: trailer claims %d rows, read %d", source.name, claimed, len(rows))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows
