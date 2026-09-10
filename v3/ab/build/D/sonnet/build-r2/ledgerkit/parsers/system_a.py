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
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import mapping
from ledgerkit.core import fields
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

BANNER = "# ARDENT LEDGER EXPORT"
COMMENT_PREFIX = "#"
COLUMNS: tuple[str, ...] = ("entry_id", "posted_on", "account", "memo", "amount", "currency")

SYSTEM_LETTER = "A"
RECORD_ID_FIELD = "entry_id"
DATE_FIELD = "posted_on"
ACCOUNT_FIELD = "account"
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


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of an Ardent export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.
    """
    source = Path(path)
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = fields.split_record(line)
            continue

        values = fields.split_record(line)
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows


def data_lines(path: Path) -> list[tuple[int, str]]:
    """Return the ``(line number, raw line)`` of every data row, skipping the rest."""
    source = Path(path)
    seen_header = False
    out: list[tuple[int, str]] = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if not seen_header:
            seen_header = True
            continue
        out.append((number, line))
    return out


def parse_date(raw: str) -> date:
    """Read an Ardent ``posted_on`` value, which is already an ISO date."""
    text = raw.strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise LedgerParseError(f"Ardent date {raw!r} is not in YYYY-MM-DD format") from exc


def parse_amount(raw: str) -> Decimal:
    """Read an Ardent ``amount`` value, already decimal dollars."""
    text = raw.strip()
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"Ardent amount {raw!r} is not a number") from exc


def to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Turn one raw Ardent row into a normalized :class:`Record`."""
    account_code = row[ACCOUNT_FIELD].strip()
    return Record(
        record_id=row[RECORD_ID_FIELD],
        source_system=SYSTEM_LETTER,
        date=parse_date(row[DATE_FIELD]),
        account_code=account_code,
        account_name=mapping.account_name(account_code, unknown_label),
        description=row["memo"],
        amount=parse_amount(row[AMOUNT_FIELD]),
    )
