"""Reader for Ardent (System A) exports.

An Ardent file looks like this::

    # ARDENT LEDGER EXPORT
    # system: A
    # period: 2026-01-01 through 2026-03-31
    # note: memo text is quoted where it contains the delimiter
    entry_id,posted_on,account,memo,amount,currency
    A-10001,2026-01-03,4100,"Rebill, ""Q1 true-up"", carrier",239.55,USD

Any number of comment lines, then one header row, then the rows.  ``posted_on``
is an ISO date.  ``amount`` is a decimal number of dollars with two places, and a
leading minus sign on a refund.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.core.values import parse_dollars
from ledgerkit.core.values import parse_date as _parse_date
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

BANNER = "# ARDENT LEDGER EXPORT"
COMMENT_PREFIX = "#"
SYSTEM_LETTER = "A"
COLUMNS: tuple[str, ...] = ("entry_id", "posted_on", "account", "memo", "amount", "currency")
ID_COLUMN = "entry_id"
DATE_COLUMN = "posted_on"
ACCOUNT_COLUMN = "account"
DESCRIPTION_COLUMN = "memo"
AMOUNT_COLUMN = "amount"
DATE_FORMAT = "%Y-%m-%d"


def read_preamble(path: Path) -> list[str]:
    """Return the comment lines at the top of the file, minus their ``#``."""
    out: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.startswith(COMMENT_PREFIX):
            break
        out.append(line.lstrip(COMMENT_PREFIX).strip())
    return out


def read_header(path: Path) -> list[str]:
    """Return the header row of an Ardent export."""
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        return fields.split_record(line)
    raise LedgerParseError(f"{Path(path).name}: no header row")


def read_numbered(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header and every data row of an Ardent export, split into fields.

    Each data row comes with its line number in the file.  Quoted memo text is
    split the way Ardent writes it: a quoted field keeps any delimiter inside it,
    and a doubled quote stands for one quote character.  Field counts are not
    checked here.
    """
    source = Path(path)
    header: list[str] | None = None
    rows: list[tuple[int, list[str]]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        rows.append((number, fields.split_record(line)))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, rows


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of an Ardent export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.
    """
    source = Path(path)
    header, numbered = read_numbered(source)
    rows: list[dict[str, str]] = []

    for number, values in numbered:
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))

    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def parse_date(raw: str) -> date:
    """Read one ``posted_on`` field.  Ardent writes ISO dates, ``YYYY-MM-DD``."""
    return _parse_date(raw, DATE_FORMAT, "Ardent posted_on")


def parse_amount(raw: str) -> Decimal:
    """Read one ``amount`` field.  Ardent writes decimal dollars."""
    return parse_dollars(raw, "Ardent amount")


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` from one row returned by :func:`read_rows`."""
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
