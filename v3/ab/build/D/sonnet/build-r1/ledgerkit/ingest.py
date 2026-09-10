"""``ingest`` — merge exports from any of the three systems into one normalized file.

Each reader hands back raw strings keyed by its own column names; this module is
the code that knows which system it is holding and turns those strings into
:class:`~ledgerkit.core.records.Record` values, per ``docs/CONVENTIONS.md``
("Reading a file").
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core.io import write_records
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

DEFAULT_OUT_PATH = Path("out") / "records.csv"


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
    day, month, year = row["txn_date"].strip().split("/")
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=date(int(year), int(month), int(day)),
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row["narrative"],
        amount=Decimal(row["gross_amount"].strip()),
    )


def records_from_file(path: Path, settings: Settings) -> list[Record]:
    """Read one export file and return its postings as :class:`Record` values."""
    system = detect_system(path)
    if system == "A":
        return [_record_from_a(row, settings) for row in system_a.read_rows(path)]
    if system == "B":
        return [_record_from_b(row, settings) for row in system_b.read_rows(path)]
    return [_record_from_c(row, settings) for row in system_c.read_rows(path)]


def ingest(paths: list[Path], out_path: Path, settings: Settings) -> int:
    """Merge ``paths`` into one normalized CSV at ``out_path``.

    Returns the number of rows written.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(records_from_file(path, settings))
    normalized = normalize(records, keep_refunds=True)
    write_records(normalized, out_path)
    _log.info("ingested %d file(s) into %d row(s) at %s", len(paths), len(normalized), out_path)
    return len(normalized)
