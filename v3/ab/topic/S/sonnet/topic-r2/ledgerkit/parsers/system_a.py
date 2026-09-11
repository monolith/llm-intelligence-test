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
leading minus sign on a refund.  ``memo`` may be double-quoted and, when it is,
may contain the delimiter and doubled quote characters; :mod:`ledgerkit.core.fields`
is quote-aware and is what this reader uses to split a line.
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


def build_record(row: dict[str, str], *, unknown_account_label: str) -> Record:
    """Turn one raw Ardent row into a normalized :class:`Record`."""
    try:
        posted_on = date.fromisoformat(row["posted_on"])
    except ValueError as exc:
        raise LedgerParseError(f"bad Ardent date {row['posted_on']!r}") from exc
    try:
        amount = Decimal(row["amount"])
    except InvalidOperation as exc:
        raise LedgerParseError(f"bad Ardent amount {row['amount']!r}") from exc

    account_code = row["account"]
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=posted_on,
        account_code=account_code,
        account_name=mapping.account_name(account_code, unknown_account_label),
        description=row["memo"],
        amount=amount,
    )


def build_records(rows: list[dict[str, str]], *, unknown_account_label: str) -> list[Record]:
    """Turn raw Ardent rows into normalized :class:`Record` values."""
    return [build_record(row, unknown_account_label=unknown_account_label) for row in rows]
