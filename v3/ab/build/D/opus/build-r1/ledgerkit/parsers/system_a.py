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

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError
from ledgerkit.log import get_logger

_log = get_logger(__name__)

BANNER = "# ARDENT LEDGER EXPORT"
COMMENT_PREFIX = "#"
COLUMNS: tuple[str, ...] = ("entry_id", "posted_on", "account", "memo", "amount", "currency")
ID_FIELD = "entry_id"
DATE_FIELD = "posted_on"
ACCOUNT_FIELD = "account"
DESCRIPTION_FIELD = "memo"
AMOUNT_FIELD = "amount"


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


def split_body(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Split an Ardent export into its header and its data lines.

    Each data line comes back as ``(line number, fields)``, with the fields split
    by the quote aware splitter and not yet checked against the header.
    """
    source = Path(path)
    header: list[str] | None = None
    body: list[tuple[int, list[str]]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue
        body.append((number, fields.split_record(line)))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    return header, body


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of an Ardent export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  Quoted memo text, including any
    delimiter or doubled quote inside it, comes back exactly as Ardent meant it.
    """
    source = Path(path)
    header, body = split_body(source)
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
    """Turn one ``posted_on`` field, an ISO ``YYYY-MM-DD`` date, into a date."""
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise LedgerParseError(f"Ardent date {raw!r} is not YYYY-MM-DD") from exc


def parse_amount(raw: str) -> Decimal:
    """Turn one ``amount`` field, decimal dollars, into dollars."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number")
    return value
