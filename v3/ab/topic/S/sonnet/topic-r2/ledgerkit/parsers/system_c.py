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

from ledgerkit import mapping
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

BANNER = "CALDER EXPORT"
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


def parse_date(text: str) -> date:
    """Parse a Calder ``txn_date`` field, which is written day first, ``DD/MM/YYYY``."""
    try:
        return datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError as exc:
        raise LedgerParseError(f"bad Calder date {text!r}") from exc


def build_record(row: dict[str, str], *, unknown_account_label: str) -> Record:
    """Turn one raw Calder row into a normalized :class:`Record`."""
    txn_date = parse_date(row["txn_date"])
    try:
        amount = Decimal(row["gross_amount"])
    except InvalidOperation as exc:
        raise LedgerParseError(f"bad Calder amount {row['gross_amount']!r}") from exc

    account_code = row["ledger_acct"]
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=txn_date,
        account_code=account_code,
        account_name=mapping.account_name(account_code, unknown_account_label),
        description=row["narrative"],
        amount=amount,
    )


def build_records(rows: list[dict[str, str]], *, unknown_account_label: str) -> list[Record]:
    """Turn raw Calder rows into normalized :class:`Record` values."""
    return [build_record(row, unknown_account_label=unknown_account_label) for row in rows]
