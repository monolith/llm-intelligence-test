"""Turn the raw rows a reader hands back into :class:`~ledgerkit.core.records.Record` values.

Each source system names its columns, its date format and its amount units
differently.  This module is the one place that knows all three, so that
``ingest`` can treat any mixture of export files the same way.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import mapping
from ledgerkit.core.records import Record
from ledgerkit.parsers import detect_system, system_a, system_b, system_c


def _record_from_a(row: dict[str, str], unknown_label: str) -> Record:
    code = row["account"]
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=date.fromisoformat(row["posted_on"]),
        account_code=code,
        account_name=mapping.account_name(code, unknown_label),
        description=row["memo"],
        amount=Decimal(row["amount"]),
    )


def _record_from_b(row: dict[str, str], unknown_label: str) -> Record:
    code = row["acct"]
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=date.fromisoformat(row["value_date"]),
        account_code=code,
        account_name=mapping.account_name(code, unknown_label),
        description=row["descr"],
        amount=system_b.to_major_units(row["amount"]),
    )


def _record_from_c(row: dict[str, str], unknown_label: str) -> Record:
    code = row["ledger_acct"]
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=datetime.strptime(row["txn_date"], "%d/%m/%Y").date(),
        account_code=code,
        account_name=mapping.account_name(code, unknown_label),
        description=row["narrative"],
        amount=Decimal(row["gross_amount"]),
    )


def build_records(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file and return every posting in it as a :class:`Record`.

    ``unknown_label`` is used for any account code the package's account map
    does not know, per the ``[report] unknown_account_label`` setting.
    """
    system = detect_system(path)
    if system == "A":
        return [_record_from_a(row, unknown_label) for row in system_a.read_rows(path)]
    if system == "B":
        return [_record_from_b(row, unknown_label) for row in system_b.read_rows(path)]
    return [_record_from_c(row, unknown_label) for row in system_c.read_rows(path)]
