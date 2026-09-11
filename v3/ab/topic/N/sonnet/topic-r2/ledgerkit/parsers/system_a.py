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

from collections.abc import Iterator
from datetime import date, datetime
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
DATE_FORMAT = "%Y-%m-%d"


def split_fields(line: str) -> list[str]:
    """Split one Ardent data line into fields, honouring quoted memos."""
    return fields.split_record(line)


def parse_date(raw: str) -> date:
    """Read an Ardent ``posted_on`` field, written ISO ``YYYY-MM-DD``."""
    try:
        return datetime.strptime(raw.strip(), DATE_FORMAT).date()
    except ValueError as exc:
        raise LedgerParseError(f"{raw!r} is not a date in the format {DATE_FORMAT}") from exc


def parse_amount(raw: str) -> Decimal:
    """Read an Ardent ``amount`` field, an ordinary decimal number of dollars."""
    try:
        return Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"{raw!r} is not a number") from exc


def to_record(row: dict[str, str], *, unknown_label: str) -> Record:
    """Build a :class:`~ledgerkit.core.records.Record` out of one raw Ardent row."""
    account_code = row["account"]
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=parse_date(row["posted_on"]),
        account_code=account_code,
        account_name=mapping.account_name(account_code, unknown_label),
        description=row["memo"],
        amount=parse_amount(row["amount"]),
    )


def iter_data_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield ``(line number, raw line)`` for every data line, skipping preamble and header."""
    header_seen = False
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if not header_seen:
            header_seen = True
            continue
        yield number, line


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
        return split_fields(line)
    raise LedgerParseError(f"{Path(path).name}: no header row")


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read the data rows of an Ardent export as raw strings.

    Rows come back keyed by :data:`COLUMNS`.  Memos are quoted where they
    contain a comma; :func:`split_fields` handles that quoting.
    """
    source = Path(path)
    header: list[str] | None = None
    rows: list[dict[str, str]] = []

    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith(COMMENT_PREFIX) or not line.strip():
            continue
        if header is None:
            header = split_fields(line)
            continue

        values = split_fields(line)
        if len(values) != len(header):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(header)} fields, found {len(values)}"
            )
        rows.append(dict(zip(header, values, strict=True)))

    if header is None:
        raise LedgerParseError(f"{source.name}: no header row")
    _log.info("read %d row(s) from %s", len(rows), source.name)
    return rows
