"""Build normalized :class:`~ledgerkit.core.records.Record` values from an export,
and read or write the normalized CSV file the ``ingest`` command produces.

Each ``_record_from_*`` function knows how its own system writes a date and an
amount; that knowledge does not belong anywhere else, per
``docs/CONVENTIONS.md``.
"""

from __future__ import annotations

import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def read_records(path: Path, unknown_account_label: str) -> list[Record]:
    """Detect which system wrote ``path`` and read its postings as :class:`Record`."""
    system = detect_system(path)
    if system == "A":
        return [_record_from_a(row, unknown_account_label) for row in system_a.read_rows(path)]
    if system == "B":
        return [_record_from_b(row, unknown_account_label) for row in system_b.read_rows(path)]
    return [_record_from_c(row, unknown_account_label) for row in system_c.read_rows(path)]


def _record_from_a(row: dict[str, str], unknown_account_label: str) -> Record:
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=date.fromisoformat(row["posted_on"].strip()),
        account_code=row["account"],
        account_name=account_name(row["account"], unknown_account_label),
        description=row["memo"],
        amount=Decimal(row["amount"].strip()),
    )


def _record_from_b(row: dict[str, str], unknown_account_label: str) -> Record:
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=date.fromisoformat(row["value_date"].strip()),
        account_code=row["acct"],
        account_name=account_name(row["acct"], unknown_account_label),
        description=row["descr"],
        amount=system_b.to_major_units(row["amount"]),
    )


def _record_from_c(row: dict[str, str], unknown_account_label: str) -> Record:
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=datetime.strptime(row["txn_date"].strip(), "%d/%m/%Y").date(),
        account_code=row["ledger_acct"],
        account_name=account_name(row["ledger_acct"], unknown_account_label),
        description=row["narrative"],
        amount=Decimal(row["gross_amount"].strip()),
    )


def write_normalized(records: list[Record], path: Path) -> int:
    """Write ``records`` to ``path`` as the normalized CSV.  Returns the row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
    return len(records)


def read_normalized(path: Path) -> list[Record]:
    """Read a normalized CSV file, as written by :func:`write_normalized`, back into
    :class:`Record` values."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
            for row in reader
        ]
