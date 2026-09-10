"""Turn raw export rows into normalized records.

Each source system says the same three things -- when, how much, which account --
in its own way, so the conversion needs to know which system a row came from.
:func:`records_from_export` is the whole path: sniff the file, read its rows, and
build one :class:`~ledgerkit.core.records.Record` per row.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.config import Settings
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, read_rows, system_b

_log = get_logger(__name__)

CENTS = Decimal("0.01")

# Which column of each system's raw row holds which piece of a Record.
COLUMN_MAP: dict[str, dict[str, str]] = {
    "A": {
        "record_id": "entry_id",
        "date": "posted_on",
        "account_code": "account",
        "description": "memo",
        "amount": "amount",
    },
    "B": {
        "record_id": "doc_no",
        "date": "value_date",
        "account_code": "acct",
        "description": "descr",
        "amount": "amount",
    },
    "C": {
        "record_id": "ref",
        "date": "txn_date",
        "account_code": "ledger_acct",
        "description": "narrative",
        "amount": "gross_amount",
    },
}

# Calder writes its dates day first.  Ardent and Borough both write ISO.
CALDER_DATE_FORMAT = "%d/%m/%Y"


def parse_date(system: str, raw: str) -> date:
    """Read one date field the way ``system`` writes dates."""
    text = raw.strip()
    if not text:
        raise LedgerParseError(f"system {system}: empty date field")
    try:
        if system == "C":
            return datetime.strptime(text, CALDER_DATE_FORMAT).date()
        return date.fromisoformat(text)
    except ValueError as exc:
        raise LedgerParseError(f"system {system}: {raw!r} is not a date this system writes") from exc


def parse_amount(system: str, raw: str) -> Decimal:
    """Read one amount field the way ``system`` writes amounts, in dollars."""
    if system == "B":
        return system_b.to_major_units(raw)
    text = raw.strip()
    if not text:
        raise LedgerParseError(f"system {system}: empty amount field")
    try:
        return Decimal(text).quantize(CENTS)
    except (InvalidOperation, ArithmeticError) as exc:
        raise LedgerParseError(f"system {system}: {raw!r} is not an amount") from exc


def record_from_row(system: str, row: dict[str, str], settings: Settings) -> Record:
    """Build one record out of one raw row of ``system``."""
    columns = COLUMN_MAP[system]
    code = row[columns["account_code"]].strip().upper()
    return Record(
        record_id=row[columns["record_id"]].strip(),
        source_system=system,
        date=parse_date(system, row[columns["date"]]),
        account_code=code,
        account_name=account_name(code, settings.unknown_account_label),
        description=row[columns["description"]],
        amount=parse_amount(system, row[columns["amount"]]),
    )


def records_from_export(path: Path, settings: Settings) -> list[Record]:
    """Read one export file and build a record for every row in it."""
    source = Path(path)
    system = detect_system(source)
    rows = read_rows(source)
    built = [record_from_row(system, row, settings) for row in rows]
    _log.info("built %d record(s) from %s (system %s)", len(built), source.name, system)
    return built
