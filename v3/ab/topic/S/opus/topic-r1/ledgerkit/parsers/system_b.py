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

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.core.values import read_date
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

HEADER_PREFIX = "sys,doc_no,value_date"
SYSTEM_LETTER = "B"
COLUMNS: tuple[str, ...] = ("sys", "doc_no", "value_date", "acct", "descr", "amount", "cur")

ID_COLUMN = "doc_no"
DATE_COLUMN = "value_date"
ACCOUNT_COLUMN = "acct"
DESCRIPTION_COLUMN = "descr"
AMOUNT_COLUMN = "amount"
DATE_FORMAT = "%Y-%m-%d"

# ASCII digits only; ``int`` would also take underscores and other scripts' digits.
_CENTS = re.compile(r"[+-]?[0-9]+")


def read_header(path: Path) -> list[str]:
    """Return the header row of a Borough export."""
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            return line.split(",")
    raise LedgerParseError(f"{Path(path).name}: no header row")


def read_fields(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header row, and the fields of every data line with its line number.

    Line numbers are 1-based and count every line of the file.  Field counts are
    not checked here: :func:`read_numbered_rows` refuses a line whose count is
    wrong, and ``validate`` reports it.
    """
    source = Path(path)
    header: list[str] | None = None
    body: list[tuple[int, list[str]]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        values = line.split(",")
        if header is None:
            header = values
        else:
            body.append((number, values))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, body


def read_numbered_rows(path: Path) -> list[tuple[int, dict[str, str]]]:
    """Read the data rows as raw strings, each paired with its 1-based line number."""
    source = Path(path)
    header, body = read_fields(source)
    rows: list[tuple[int, dict[str, str]]] = []
    for number, values in body:
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        row = dict(zip(header, values, strict=True))
        if row.get("sys", "").strip() != SYSTEM_LETTER:
            raise LedgerParseError(
                f"{source.name} line {number}: sys column says {row.get('sys')!r}, expected 'B'"
            )
        rows.append((number, row))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of a Borough export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  Nothing here converts a value; the
    ``amount`` column is handed on exactly as Borough wrote it.
    """
    return [row for _, row in read_numbered_rows(path)]


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
    if _CENTS.fullmatch(text) is None:
        raise LedgerParseError(f"Borough amount {raw!r} is not an integer number of cents")
    return (Decimal(int(text)) / Decimal(100)).quantize(Decimal("0.01"))


def parse_date(raw: str) -> date:
    """Read a ``value_date`` field, which Borough writes as an ISO date."""
    return read_date(raw, DATE_FORMAT)


def parse_amount(raw: str) -> Decimal:
    """Read an ``amount`` field, which Borough writes in cents, as dollars."""
    return to_major_units(raw)


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` from one raw row.

    ``unknown_label`` is the account name given to a code the account map lacks.
    """
    code = row[ACCOUNT_COLUMN]
    return Record(
        record_id=row[ID_COLUMN],
        source_system=SYSTEM_LETTER,
        date=parse_date(row[DATE_COLUMN]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[DESCRIPTION_COLUMN],
        amount=parse_amount(row[AMOUNT_COLUMN]),
    )
