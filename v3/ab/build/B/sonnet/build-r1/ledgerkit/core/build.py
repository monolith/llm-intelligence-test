"""Turn a reader's raw rows into normalized :class:`Record` values.

Each source system encodes its date and its amount its own way; per
``docs/CONVENTIONS.md``'s "Reading a file" section, that interpretation belongs
here, not in the readers themselves.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def _parse_date(text: str, date_format: str, label: str) -> date:
    try:
        return datetime.strptime(text.strip(), date_format).date()
    except ValueError as exc:
        raise LedgerParseError(f"bad {label} date {text!r}") from exc


def _parse_decimal(text: str, label: str) -> Decimal:
    try:
        return Decimal(text.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"bad {label} amount {text!r}") from exc


def record_from_a(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` out of one raw Ardent (System A) row."""
    posted_on = _parse_date(row["posted_on"], "%Y-%m-%d", "Ardent")
    amount = _parse_decimal(row["amount"], "Ardent")
    code = row["account"].strip()
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=posted_on,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["memo"],
        amount=amount,
    )


def record_from_b(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` out of one raw Borough (System B) row."""
    value_date = _parse_date(row["value_date"], "%Y-%m-%d", "Borough")
    amount = system_b.to_major_units(row["amount"])
    code = row["acct"].strip()
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=value_date,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["descr"],
        amount=amount,
    )


def record_from_c(row: dict[str, str], unknown_label: str) -> Record:
    """Build a :class:`Record` out of one raw Calder (System C) row."""
    txn_date = _parse_date(row["txn_date"], "%d/%m/%Y", "Calder")
    amount = _parse_decimal(row["gross_amount"], "Calder")
    code = row["ledger_acct"].strip()
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=txn_date,
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row["narrative"],
        amount=amount,
    )


_BUILDERS = {"A": record_from_a, "B": record_from_b, "C": record_from_c}


def read_records(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file and hand back its postings as :class:`Record` values."""
    source = Path(path)
    system = detect_system(source)
    if system == "A":
        rows = system_a.read_rows(source)
    elif system == "B":
        rows = system_b.read_rows(source)
    else:
        rows = system_c.read_rows(source)
    builder = _BUILDERS[system]
    records = [builder(row, unknown_label) for row in rows]
    _log.info("built %d record(s) from %s", len(records), source.name)
    return records
