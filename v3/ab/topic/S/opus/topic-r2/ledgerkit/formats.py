"""What each system's columns mean, and how to read its dates and amounts.

The readers in :mod:`ledgerkit.parsers` get a file's shape right and hand back
raw strings keyed by the system's own column names.  :data:`FORMATS` says, for
each system, which of those columns holds a posting's id, date, account,
description and amount, and which functions read that system's dates and
amounts.  Ingest and validate both go through it, so they cannot disagree about
what a system writes.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.parsers import detect_system, system_a, system_b, system_c

RawLines = tuple[list[str], list[tuple[int, list[str]]]]


@dataclass(frozen=True)
class ExportFormat:
    """How to read one system's export."""

    system: str
    id_column: str
    date_column: str
    account_column: str
    description_column: str
    amount_column: str
    read_fields: Callable[[Path], RawLines]
    read_rows: Callable[[Path], list[dict[str, str]]]
    parse_date: Callable[[str], date]
    parse_amount: Callable[[str], Decimal]

    def required_columns(self) -> tuple[str, ...]:
        """The columns a record cannot be built without."""
        return (
            self.id_column,
            self.date_column,
            self.account_column,
            self.description_column,
            self.amount_column,
        )

    def missing_columns(self, header: Iterable[str]) -> list[str]:
        """The required columns that ``header`` does not have."""
        present = set(header)
        return [column for column in self.required_columns() if column not in present]


FORMATS: dict[str, ExportFormat] = {
    "A": ExportFormat(
        system="A",
        id_column="entry_id",
        date_column="posted_on",
        account_column="account",
        description_column="memo",
        amount_column="amount",
        read_fields=system_a.read_fields,
        read_rows=system_a.read_rows,
        parse_date=system_a.parse_date,
        parse_amount=system_a.parse_amount,
    ),
    "B": ExportFormat(
        system="B",
        id_column="doc_no",
        date_column="value_date",
        account_column="acct",
        description_column="descr",
        amount_column="amount",
        read_fields=system_b.read_fields,
        read_rows=system_b.read_rows,
        parse_date=system_b.parse_date,
        parse_amount=system_b.parse_amount,
    ),
    "C": ExportFormat(
        system="C",
        id_column="ref",
        date_column="txn_date",
        account_column="ledger_acct",
        description_column="narrative",
        amount_column="gross_amount",
        read_fields=system_c.read_fields,
        read_rows=system_c.read_rows,
        parse_date=system_c.parse_date,
        parse_amount=system_c.parse_amount,
    ),
}


def format_for(path: Path) -> ExportFormat:
    """Detect which system wrote ``path`` and return how to read it."""
    return FORMATS[detect_system(path)]
