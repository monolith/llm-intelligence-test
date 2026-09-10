"""Turn raw export rows into :class:`~ledgerkit.core.records.Record` values.

The readers in :mod:`ledgerkit.parsers` hand back raw strings.  This module is
where those strings are interpreted: it knows which column of each system holds
the id, the date, the account, the description and the amount, how each system
writes a date, and what unit each system writes an amount in.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, read_rows, system_b

_log = get_logger(__name__)


@dataclass(frozen=True)
class Layout:
    """Where one system keeps each part of a posting, and how it writes a date."""

    system: str
    id_column: str
    date_column: str
    account_column: str
    description_column: str
    amount_column: str
    date_format: str
    date_label: str

    def missing_columns(self, header: list[str]) -> list[str]:
        """The columns this layout needs that ``header`` does not have."""
        wanted = (
            self.id_column,
            self.date_column,
            self.account_column,
            self.description_column,
            self.amount_column,
        )
        return [column for column in wanted if column not in header]


LAYOUTS: dict[str, Layout] = {
    "A": Layout("A", "entry_id", "posted_on", "account", "memo", "amount", "%Y-%m-%d", "YYYY-MM-DD"),
    "B": Layout("B", "doc_no", "value_date", "acct", "descr", "amount", "%Y-%m-%d", "YYYY-MM-DD"),
    # Calder writes its dates day first.
    "C": Layout(
        "C", "ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "%d/%m/%Y", "DD/MM/YYYY"
    ),
}


def parse_date(system: str, raw: str) -> date:
    """Read a date field the way ``system`` writes it."""
    layout = LAYOUTS[system]
    try:
        return datetime.strptime(raw.strip(), layout.date_format).date()
    except ValueError as exc:
        raise LedgerParseError(
            f"date {raw!r} is not a {layout.date_label} date as system {system} writes it"
        ) from exc


def parse_amount(system: str, raw: str) -> Decimal:
    """Read an amount field as dollars, whatever unit ``system`` writes it in."""
    if system == "B":
        return system_b.to_major_units(raw)
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value


def build_record(system: str, row: Mapping[str, str], unknown_label: str) -> Record:
    """Build one record from a raw row that ``system`` wrote."""
    layout = LAYOUTS[system]
    missing = layout.missing_columns(list(row))
    if missing:
        raise LedgerParseError(f"row has no {', '.join(missing)} column")
    code = row[layout.account_column]
    return Record(
        record_id=row[layout.id_column],
        source_system=system,
        date=parse_date(system, row[layout.date_column]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[layout.description_column],
        amount=parse_amount(system, row[layout.amount_column]),
    )


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Read every posting in one export file as a record, in file order."""
    source = Path(path)
    system = detect_system(source)
    layout = LAYOUTS[system]
    records: list[Record] = []
    for row in read_rows(source):
        try:
            records.append(build_record(system, row, unknown_label))
        except LedgerParseError as exc:
            record_id = row.get(layout.id_column, "?")
            raise LedgerParseError(f"{source.name} record {record_id}: {exc}") from exc
    _log.info("built %d record(s) from %s", len(records), source.name)
    return records
