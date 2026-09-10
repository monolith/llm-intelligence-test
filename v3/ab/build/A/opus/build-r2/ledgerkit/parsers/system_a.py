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
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name

_log = get_logger(__name__)

BANNER = "# ARDENT LEDGER EXPORT"
COMMENT_PREFIX = "#"
COLUMNS: tuple[str, ...] = ("entry_id", "posted_on", "account", "memo", "amount", "currency")
SYSTEM_LETTER = "A"
DATE_FORMAT = "%Y-%m-%d"
DATE_FIELD = "posted_on"
AMOUNT_FIELD = "amount"
ACCOUNT_FIELD = "account"


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
    """Return the header and every data line as ``(line number, fields)``.

    Only the file's shape is handled here: comments and blank lines are skipped
    and quoted fields are split correctly.  Field counts are not checked.
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
    header, lines = read_lines(source)
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
    """Read an Ardent ``posted_on`` field, which is an ISO date."""
    try:
        return datetime.strptime(raw.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise LedgerParseError(f"Ardent date {raw!r} is not YYYY-MM-DD") from exc


def parse_amount(raw: str) -> Decimal:
    """Read an Ardent ``amount`` field, which is decimal dollars."""
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number")
    return value


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` from one raw Ardent row."""
    return Record(
        record_id=row["entry_id"],
        source_system=SYSTEM_LETTER,
        date=parse_date(row["posted_on"]),
        account_code=row["account"],
        account_name=account_name(row["account"], unknown_label),
        description=row["memo"],
        amount=parse_amount(row["amount"]),
    )
