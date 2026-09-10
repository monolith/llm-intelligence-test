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
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

BANNER = "CALDER EXPORT"
TRAILER_PATTERN = re.compile(r"^==\s*(\d+)\s+rows\s*==$")
COLUMNS: tuple[str, ...] = ("ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "ccy")
ACCOUNT_FIELD = "ledger_acct"
DATE_FIELD = "txn_date"
AMOUNT_FIELD = "gross_amount"


def split_line(line: str) -> list[str]:
    """Split one Calder data line into its fields.  Calder never quotes a field."""
    return line.split(",")


def read_header(path: Path) -> list[str]:
    """Return the header row of a Calder export."""
    seen_banner = False
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if TRAILER_PATTERN.match(stripped):
            continue
        return line.split(",")
    raise LedgerParseError(f"{Path(path).name}: no header row")


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


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of a Calder export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  The ``txn_date`` field is passed
    through exactly as Calder wrote it.
    """
    source = Path(path)
    header: list[str] | None = None
    rows: list[dict[str, str]] = []
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

        # txn_date is written day first, dd/mm/yyyy, which is how Calder has
        # always written it and is not how Ardent or Borough write theirs.  Read
        # month first and the rows past the twelfth of a month blow up, while the
        # rows on or before it quietly land in the wrong month.  The field is
        # handed on as written; whoever builds records out of these rows decides
        # how to read it.
        values = split_line(line)
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")

    claimed = read_trailer_count(source)
    if claimed is not None and claimed != len(rows):
        _log.warning("%s: trailer claims %d rows, read %d", source.name, claimed, len(rows))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def iter_data_lines(path: Path) -> list[tuple[int, str]]:
    """Return every data line's (line number, raw text), banner/header/trailer skipped.

    Unlike :func:`read_rows`, this does not check field counts, so it is safe to
    call on rows :func:`read_rows` would reject.
    """
    source = Path(path)
    out: list[tuple[int, str]] = []
    seen_banner = False
    header_seen = False
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if TRAILER_PATTERN.match(stripped):
            continue
        if not header_seen:
            header_seen = True
            continue
        out.append((number, line))
    return out


def parse_date(raw: str) -> date:
    """Calder writes a day-first date, ``dd/mm/yyyy``."""
    text = raw.strip()
    parts = text.split("/")
    if len(parts) != 3:
        raise LedgerParseError(f"Calder date {raw!r} is not dd/mm/yyyy")
    day_str, month_str, year_str = parts
    try:
        return date(int(year_str), int(month_str), int(day_str))
    except ValueError as exc:
        raise LedgerParseError(f"Calder date {raw!r} is not a valid dd/mm/yyyy date") from exc


def parse_amount(raw: str) -> Decimal:
    """Calder writes ordinary decimal dollars, already in the units a Record wants."""
    try:
        return Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"Calder amount {raw!r} is not a number") from exc


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Turn one raw Calder row into a normalized :class:`~ledgerkit.core.records.Record`."""
    code = row[ACCOUNT_FIELD].strip()
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=parse_date(row[DATE_FIELD]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"],
        amount=parse_amount(row[AMOUNT_FIELD]),
    )
