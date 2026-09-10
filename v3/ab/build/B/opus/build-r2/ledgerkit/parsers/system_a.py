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

from ledgerkit.core import fields, values
from ledgerkit.core.records import LedgerParseError, Record
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


def read_lines(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header and every data line of an Ardent export, split into fields.

    Each data line comes back with its line number in the file.  Field counts are
    not checked here, so a caller can report a short or long line instead of
    stopping at it.  Quoted memos are split with :func:`fields.split_record`.
    """
    source = Path(path)
    header: list[str] | None = None
    lines: list[tuple[int, list[str]]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            fields.require_columns(header, COLUMNS, source.name)
            continue
        lines.append((number, fields.split_record(line)))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, lines


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of an Ardent export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.
    """
    source = Path(path)
    header, lines = read_lines(source)
    rows: list[dict[str, str]] = []
    for number, parts in lines:
        if len(parts) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(parts)}"
            )
        rows.append(dict(zip(header, parts, strict=True)))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def parse_date(raw: str) -> date:
    """Read a ``posted_on`` field, which Ardent writes as an ISO date."""
    return values.parse_date(raw, DATE_FORMAT)


def parse_amount(raw: str) -> Decimal:
    """Read an ``amount`` field, which Ardent writes in decimal dollars."""
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
