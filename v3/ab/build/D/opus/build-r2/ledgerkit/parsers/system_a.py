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

ID_COLUMN = "entry_id"
DATE_COLUMN = "posted_on"
ACCOUNT_COLUMN = "account"
DESCRIPTION_COLUMN = "memo"
AMOUNT_COLUMN = "amount"


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


def split_lines(path: Path) -> tuple[list[str], list[tuple[int, list[str]]]]:
    """Return the header row and every data line split into fields.

    Each data line comes back with its line number in the file, counting the
    comment lines.  Quoted memo text is split with
    :func:`ledgerkit.core.fields.split_record`, so a memo keeps any delimiter or
    doubled quote it contains.  Field counts are not checked here.
    """
    source = Path(path)
    header: list[str] | None = None
    lines: list[tuple[int, list[str]]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
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
    header, lines = split_lines(source)
    rows: list[dict[str, str]] = []

    for number, values in lines:
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))

    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def parse_date(raw: str) -> date:
    """Turn one Ardent ``posted_on`` field, an ISO ``YYYY-MM-DD`` date, into a date."""
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise LedgerParseError(f"Ardent date {raw!r} is not YYYY-MM-DD") from exc


def parse_amount(raw: str) -> Decimal:
    """Turn one Ardent ``amount`` field, decimal dollars, into a Decimal."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number")
    return value
