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

Lines are split with :func:`ledgerkit.core.fields.split_record`, so a quoted memo
keeps any delimiter or doubled quote it contains.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError, Record, parse_decimal
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

SYSTEM_LETTER = "A"
BANNER = "# ARDENT LEDGER EXPORT"
COMMENT_PREFIX = "#"
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


def read_table(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header and every data line of an Ardent export, split into fields.

    Data lines come back as ``(line number, fields)`` pairs, numbered from 1 over
    the whole file.  Field counts are not checked here.
    """
    source = Path(path)
    header: list[str] | None = None
    body: list[tuple[int, list[str]]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        values = fields.split_record(line)
        if header is None:
            header = values
            continue
        body.append((number, values))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, body


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of an Ardent export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.
    """
    source = Path(path)
    header, body = read_table(source)
    rows: list[dict[str, str]] = []
    for number, values in body:
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def parse_date(raw: str) -> date:
    """Read an Ardent ``posted_on`` field, which is an ISO ``YYYY-MM-DD`` date."""
    try:
        return datetime.strptime(raw.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise LedgerParseError(f"Ardent date {raw!r} is not a YYYY-MM-DD date") from exc


def parse_amount(raw: str) -> Decimal:
    """Read an Ardent ``amount`` field, which is already decimal dollars."""
    return parse_decimal(raw, "Ardent amount")


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
