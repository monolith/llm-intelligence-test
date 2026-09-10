"""Turn a reader's raw rows into normalized :class:`~ledgerkit.core.records.Record`
objects.

Each source system names its date and amount fields differently and writes
amounts in a different shape.  This is where that gets sorted out, per each
reader's own notes on the subject: System B's ``amount`` is integer cents and
goes through :func:`~ledgerkit.parsers.system_b.to_major_units`, and System C's
``txn_date`` is day-first and is parsed accordingly rather than with
``date.fromisoformat``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import Record
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, read_rows, system_b


def _record_from_a(row: dict[str, str], unknown_label: str) -> Record:
    code = row["account"]
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=date.fromisoformat(row["posted_on"]),
        account_code=code,
        account_name=account_name(code, unknown_label),
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
        account_name=account_name(code, unknown_label),
        description=row["descr"],
        amount=system_b.to_major_units(row["amount"]),
    )


def _record_from_c(row: dict[str, str], unknown_label: str) -> Record:
    code = row["ledger_acct"]
    day, month, year = row["txn_date"].split("/")
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=date(int(year), int(month), int(day)),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"],
        amount=Decimal(row["gross_amount"]),
    )


_BUILDERS = {"A": _record_from_a, "B": _record_from_b, "C": _record_from_c}


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Detect the system that wrote ``path``, read it, and hand back Record objects."""
    system = detect_system(path)
    rows = read_rows(path)
    builder = _BUILDERS[system]
    return [builder(row, unknown_label) for row in rows]
