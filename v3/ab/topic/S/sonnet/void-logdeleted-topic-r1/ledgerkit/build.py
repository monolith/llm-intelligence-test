"""Turning one export file's raw rows into normalized :class:`Record` values.

Each parser in :mod:`ledgerkit.parsers` hands back raw strings keyed by its own
system's column names. This module is the caller that knows what those columns
mean: which one is the date, which is the account code, and how that system
writes an amount.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def _parse_calder_date(text: str) -> date:
    day_str, month_str, year_str = text.strip().split("/")
    return date(int(year_str), int(month_str), int(day_str))


def _record_from_a(row: dict[str, str], unknown_label: str) -> Record:
    code = row["account"]
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=date.fromisoformat(row["posted_on"].strip()),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["memo"],
        amount=Decimal(row["amount"].strip()),
    )


def _record_from_b(row: dict[str, str], unknown_label: str) -> Record:
    code = row["acct"]
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=date.fromisoformat(row["value_date"].strip()),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["descr"],
        amount=system_b.to_major_units(row["amount"]),
    )


def _record_from_c(row: dict[str, str], unknown_label: str) -> Record:
    code = row["ledger_acct"]
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=_parse_calder_date(row["txn_date"]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"],
        amount=Decimal(row["gross_amount"].strip()),
    )


_READERS = {"A": system_a.read_rows, "B": system_b.read_rows, "C": system_c.read_rows}
_BUILDERS = {"A": _record_from_a, "B": _record_from_b, "C": _record_from_c}


def records_from_file(path: Path, unknown_label: str) -> list[Record]:
    """Detect the system that wrote ``path`` and build its :class:`Record` values."""
    source = Path(path)
    system = detect_system(source)
    rows = _READERS[system](source)
    builder = _BUILDERS[system]
    records = [builder(row, unknown_label) for row in rows]
    _log.info("built %d record(s) from %s (system %s)", len(records), source.name, system)
    return records
