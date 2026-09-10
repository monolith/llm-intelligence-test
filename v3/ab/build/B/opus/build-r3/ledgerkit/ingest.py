"""Turn raw export rows into :class:`~ledgerkit.core.records.Record` values.

The readers in :mod:`ledgerkit.parsers` hand back raw strings.  This module is
the one place that knows what each system means by them: which column holds
what, how each system writes a date, and what units each writes an amount in.
:mod:`ledgerkit.validate` uses the same parsers, so a row that validates is a
row that ingests.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, read_rows, system_b

_log = get_logger(__name__)


@dataclass(frozen=True)
class Layout:
    """Which of a system's own columns holds each part of a posting."""

    system: str
    record_id: str
    date: str
    account_code: str
    description: str
    amount: str
    date_format: str


LAYOUTS: dict[str, Layout] = {
    "A": Layout("A", "entry_id", "posted_on", "account", "memo", "amount", "%Y-%m-%d"),
    "B": Layout("B", "doc_no", "value_date", "acct", "descr", "amount", "%Y-%m-%d"),
    # Calder writes its dates day first.
    "C": Layout("C", "ref", "txn_date", "ledger_acct", "narrative", "gross_amount", "%d/%m/%Y"),
}


def parse_date(system: str, raw: str) -> date:
    """Read a date field the way ``system`` writes it."""
    layout = LAYOUTS[system]
    try:
        return datetime.strptime(raw.strip(), layout.date_format).date()
    except ValueError as exc:
        raise LedgerParseError(
            f"date {raw!r} is not a system {system} date ({layout.date_format})"
        ) from exc


def parse_amount(system: str, raw: str) -> Decimal:
    """Read an amount field as dollars.

    Borough writes whole cents; Ardent and Calder write dollars.
    """
    if system == "B":
        return system_b.to_major_units(raw)
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {raw!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {raw!r} is not a number")
    return value


def build_record(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Make one record out of one raw row from ``system``."""
    layout = LAYOUTS[system]
    code = row[layout.account_code]
    return Record(
        record_id=row[layout.record_id],
        source_system=system,
        date=parse_date(system, row[layout.date]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[layout.description],
        amount=parse_amount(system, row[layout.amount]),
    )


def read_export(path: Path, unknown_label: str) -> list[Record]:
    """Read every posting in one export file, whichever system wrote it."""
    source = Path(path)
    system = detect_system(source)
    records: list[Record] = []
    for row in read_rows(source):
        layout = LAYOUTS[system]
        try:
            records.append(build_record(system, row, unknown_label))
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} {row.get(layout.record_id)!r}: {exc}") from exc
    return records


def merge(exports: Iterable[list[Record]]) -> list[Record]:
    """Put the postings from several exports into one list in output order.

    Nothing is dropped, deduplicated or rewritten.
    """
    merged = [record for records in exports for record in records]
    merged.sort(key=sort_key)
    return merged
