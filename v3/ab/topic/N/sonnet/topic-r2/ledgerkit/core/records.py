"""The normalized record every reader eventually produces.

One :class:`Record` is one posting: which system it came from, when it was
posted, which account it hit, what it was for, and how much it moved.  Amounts
are :class:`~decimal.Decimal` dollars, positive for a charge and negative for a
refund.  Dates are :class:`datetime.date`, whatever the source system wrote.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
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


def write_records(path: Path, records: Iterable[Record]) -> None:
    """Write ``records`` to ``path`` as a normalized CSV file.

    Parent directories are created if they do not exist.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(fields.join_record(list(RECORD_COLUMNS)) + "\n")
        for record in records:
            handle.write(fields.join_record(record.to_row()) + "\n")


def read_records(path: Path) -> list[Record]:
    """Read a normalized CSV file, as written by :func:`write_records`, back into records."""
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise LedgerParseError(f"{source.name}: empty file")
    header = fields.split_record(lines[0])
    if header != list(RECORD_COLUMNS):
        raise LedgerParseError(f"{source.name}: unexpected header {header!r}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        values = fields.split_record(line)
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{source.name} line {number}: expected {len(RECORD_COLUMNS)} fields, found {len(values)}"
            )
        row = dict(zip(RECORD_COLUMNS, values, strict=True))
        records.append(
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
        )
    return records
