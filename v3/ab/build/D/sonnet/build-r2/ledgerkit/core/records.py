"""The normalized record every reader eventually produces.

One :class:`Record` is one posting: which system it came from, when it was
posted, which account it hit, what it was for, and how much it moved.  Amounts
are :class:`~decimal.Decimal` dollars, positive for a charge and negative for a
refund.  Dates are :class:`datetime.date`, whatever the source system wrote.
"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

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


def from_row(row: Sequence[str]) -> Record:
    """Rebuild a :class:`Record` from one row of a normalized CSV file."""
    record_id, source_system, date_text, account_code, account_name, description, amount_text = row
    return Record(
        record_id=record_id,
        source_system=source_system,
        date=date.fromisoformat(date_text),
        account_code=account_code,
        account_name=account_name,
        description=description,
        amount=Decimal(amount_text),
    )


def read_records(path: Path) -> list[Record]:
    """Read a normalized CSV file written by ``ingest`` back into :class:`Record` values."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return [from_row(row) for row in reader]
