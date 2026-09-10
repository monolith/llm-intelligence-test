"""Turn raw rows from the three export formats into normalized :class:`Record` values.

The parsers under :mod:`ledgerkit.parsers` hand back raw strings keyed by each
system's own column names and do not interpret them, by design (see
``docs/CONVENTIONS.md``).  This module is the caller that knows which system it
is holding and does the interpreting: which column is the date, which format
that date is written in, and what unit the amount column is in.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def _record_from_a(row: dict[str, str], settings: Settings) -> Record:
    code = row["account"].strip().upper()
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=date.fromisoformat(row["posted_on"].strip()),
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["memo"],
        amount=Decimal(row["amount"].strip()),
    )


def _record_from_b(row: dict[str, str], settings: Settings) -> Record:
    code = row["acct"].strip().upper()
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=date.fromisoformat(row["value_date"].strip()),
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["descr"],
        amount=system_b.to_major_units(row["amount"]),
    )


def _record_from_c(row: dict[str, str], settings: Settings) -> Record:
    code = row["ledger_acct"].strip().upper()
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=datetime.strptime(row["txn_date"].strip(), "%d/%m/%Y").date(),
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["narrative"],
        amount=Decimal(row["gross_amount"].strip()),
    )


def read_records(path: Path, settings: Settings) -> list[Record]:
    """Detect the system that wrote ``path`` and turn its rows into records."""
    system = detect_system(path)
    if system == "A":
        rows = system_a.read_rows(path)
        builder = _record_from_a
    elif system == "B":
        rows = system_b.read_rows(path)
        builder = _record_from_b
    else:
        rows = system_c.read_rows(path)
        builder = _record_from_c
    _log.info("built %d record(s) from %s", len(rows), Path(path).name)
    return [builder(row, settings) for row in rows]


def ingest_files(paths: list[Path], settings: Settings) -> list[Record]:
    """Read every export in ``paths`` and return one normalized, ordered list.

    Every posting is kept, refunds included: ``ingest`` is meant to hold the
    whole ledger, not a report total.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(read_records(path, settings))
    return normalize(records, keep_refunds=True)
