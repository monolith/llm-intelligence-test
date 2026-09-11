"""Reader for Borough (System B) exports.

A Borough file is the plainest of the three::

    sys,doc_no,value_date,acct,descr,amount,cur
    B,B-2201,2026-01-07,4100,Container unload allowance,25440,USD

One header row, then rows.  Every row repeats the system letter in the first
column, which is how Borough files survive being concatenated by hand.  Borough
never quotes a field, and its description column is scrubbed of delimiters at the
source, so a Borough line always has exactly as many commas as the header does.

``value_date`` is an ISO date.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name as _account_name

_log = get_logger(__name__)

HEADER_PREFIX = "sys,doc_no,value_date"
SYSTEM_LETTER = "B"
COLUMNS: tuple[str, ...] = ("sys", "doc_no", "value_date", "acct", "descr", "amount", "cur")


def read_header(path: Path) -> list[str]:
    """Return the header row of a Borough export."""
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            return line.split(",")
    raise LedgerParseError(f"{Path(path).name}: no header row")


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of a Borough export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  Nothing here converts a value; the
    ``amount`` column is handed on exactly as Borough wrote it.
    """
    source = Path(path)
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if header is None:
            header = line.split(",")
            continue

        values = line.split(",")
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        row = dict(zip(header, values, strict=True))
        if row.get("sys", "").strip() != SYSTEM_LETTER:
            raise LedgerParseError(
                f"{source.name} line {number}: sys column says {row.get('sys')!r}, expected 'B'"
            )
        rows.append(row)

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def iter_data_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield the ``(line number, raw line)`` of every data line, header skipped."""
    source = Path(path)
    header_seen = False
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        if not header_seen:
            header_seen = True
            continue
        yield number, line
    if not header_seen:
        raise LedgerParseError(f"{source.name}: no header row")


def document_numbers(path: Path) -> list[str]:
    """The ``doc_no`` of every row, in file order.  Used by the duplicate check."""
    return [row["doc_no"] for row in read_rows(path)]


def has_duplicate_documents(path: Path) -> bool:
    """True when the same ``doc_no`` shows up twice in one export."""
    numbers = document_numbers(path)
    return len(numbers) != len(set(numbers))


def to_major_units(raw: str) -> Decimal:
    """Turn one Borough ``amount`` field into dollars.

    Borough writes that column in **integer minor units**, that is, whole cents,
    and never in dollars.  A row reading ``25440`` is two hundred fifty four
    dollars and forty cents; a row reading ``-8825`` is a refund of eighty eight
    dollars and twenty five cents.  The column header says only ``amount``, and
    the values carry no decimal point, so a reader that treats the column as
    dollars gets numbers a hundred times too large and no error to go with them.
    Two importers have been caught doing exactly that.

    Ardent and Calder both write ordinary decimal dollars in their own amount
    columns, so this scaling applies to Borough files and to nothing else.
    """
    text = raw.strip()
    if not text:
        raise LedgerParseError("empty Borough amount field")
    try:
        cents = int(text)
    except ValueError as exc:
        raise LedgerParseError(f"Borough amount {raw!r} is not an integer number of cents") from exc
    return (Decimal(cents) / Decimal(100)).quantize(Decimal("0.01"))


def parse_date(text: str) -> date:
    """Parse a Borough ``value_date`` field: an ISO ``YYYY-MM-DD`` date."""
    try:
        return date.fromisoformat(text.strip())
    except ValueError as exc:
        raise LedgerParseError(f"date {text!r} is not a valid ISO date") from exc


def to_record(row: dict[str, str], *, unknown_label: str) -> Record:
    """Build a normalized :class:`Record` from one raw Borough row."""
    code = row["acct"].strip()
    return Record(
        record_id=row["doc_no"],
        source_system=SYSTEM_LETTER,
        date=parse_date(row["value_date"]),
        account_code=code,
        account_name=_account_name(code, unknown_label),
        description=row["descr"],
        amount=to_major_units(row["amount"]),
    )
