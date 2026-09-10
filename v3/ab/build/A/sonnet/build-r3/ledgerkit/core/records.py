"""The normalized record every reader eventually produces.

One :class:`Record` is one posting: which system it came from, when it was
posted, which account it hit, what it was for, and how much it moved.  Amounts
are :class:`~decimal.Decimal` dollars, positive for a charge and negative for a
refund.  Dates are :class:`datetime.date`, whatever the source system wrote.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core import fields

RECORD_COLUMNS: tuple[str, ...] = (
    "record_id",
    "source_system",
    "date",
    "account_code",
    "account_name",
    "description",
    "amount",
)


class LedgerParseError(ValueError):
    """Raised when a reader cannot make a row out of a line."""


@dataclass(frozen=True)
class Record:
    """One normalized posting."""

    record_id: str
    source_system: str
    date: date
    account_code: str
    account_name: str
    description: str
    amount: Decimal

    def is_refund(self) -> bool:
        """True when this posting moved money back out of the ledger."""
        return self.amount < 0

    def month(self) -> str:
        """The posting month as ``YYYY-MM``."""
        return f"{self.date.year:04d}-{self.date.month:02d}"

    def to_row(self) -> list[str]:
        """Render this record as one row in :data:`RECORD_COLUMNS` order."""
        return [
            self.record_id,
            self.source_system,
            self.date.isoformat(),
            self.account_code,
            self.account_name,
            self.description,
            f"{self.amount:.2f}",
        ]


def sort_key(record: Record) -> tuple[str, str, str]:
    """The ordering every normalized output uses: date, then system, then id."""
    return (record.date.isoformat(), record.source_system, record.record_id)


def from_row(values: list[str]) -> Record:
    """Rebuild a :class:`Record` from one row in :data:`RECORD_COLUMNS` order."""
    if len(values) != len(RECORD_COLUMNS):
        raise LedgerParseError(f"expected {len(RECORD_COLUMNS)} fields, found {len(values)}")
    record_id, source_system, date_str, account_code, name, description, amount = values
    try:
        parsed_date = date.fromisoformat(date_str)
    except ValueError as exc:
        raise LedgerParseError(f"{date_str!r} is not an ISO date") from exc
    try:
        parsed_amount = Decimal(amount)
    except InvalidOperation as exc:
        raise LedgerParseError(f"{amount!r} is not a number") from exc
    return Record(
        record_id=record_id,
        source_system=source_system,
        date=parsed_date,
        account_code=account_code,
        account_name=name,
        description=description,
        amount=parsed_amount,
    )


def read_records(path: Path) -> list[Record]:
    """Read a normalized records CSV, as written by ``ingest``, back into Records."""
    source = Path(path)
    lines = [line for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return []
    header = fields.split_record(lines[0])
    if list(header) != list(RECORD_COLUMNS):
        raise LedgerParseError(f"{source.name}: unexpected header {header}")
    return [from_row(fields.split_record(line)) for line in lines[1:]]
