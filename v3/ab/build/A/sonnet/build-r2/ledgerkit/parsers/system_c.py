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
from collections.abc import Iterator
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

BANNER = "CALDER EXPORT"
SYSTEM_LETTER = "C"
TRAILER_PATTERN = re.compile(r"^==\s*(\d+)\s+rows\s*==$")
COLUMNS: tuple[str, ...] = ("ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "ccy")


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
        values = line.split(",")
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


def iter_data_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield ``(line number, raw line)`` for every data line, skipping the banner, header and trailer."""
    seen_banner = False
    seen_header = False
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if not seen_banner:
            seen_banner = True
            continue
        if TRAILER_PATTERN.match(stripped):
            continue
        if not seen_header:
            seen_header = True
            continue
        yield number, line


def parse_date(raw: str) -> date:
    """Parse a Calder ``txn_date`` field, written day first as ``dd/mm/yyyy``."""
    try:
        return datetime.strptime(raw.strip(), "%d/%m/%Y").date()
    except ValueError as exc:
        raise ValueError(f"Calder date {raw!r} is not in dd/mm/yyyy format") from exc


def parse_amount(raw: str) -> Decimal:
    """Parse a Calder ``gross_amount`` field, ordinary decimal dollars."""
    return Decimal(raw.strip())


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` out of one raw Calder row."""
    code = row["ledger_acct"]
    return Record(
        record_id=row["ref"],
        source_system=SYSTEM_LETTER,
        date=parse_date(row["txn_date"]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"],
        amount=parse_amount(row["gross_amount"]),
    )
