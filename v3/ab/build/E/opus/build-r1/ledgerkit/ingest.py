"""Turn the raw rows the readers hand back into :class:`Record` values.

This is the code that knows which system it is holding, so it is where each
system's way of writing a date and an amount is interpreted:

* A and B write ISO dates; C writes ``dd/mm/yyyy``, day first.
* A and C write decimal dollars; B writes integer cents.

Descriptions are kept exactly as the source wrote them, and nothing is filtered:
refunds and repeated postings come through like any other row.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit import mapping
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

# Which of a system's own columns holds each record field:
# record id, date, account code, description, amount.
FIELD_COLUMNS: dict[str, tuple[str, str, str, str, str]] = {
    "A": ("entry_id", "posted_on", "account", "memo", "amount"),
    "B": ("doc_no", "value_date", "acct", "descr", "amount"),
    "C": ("ref", "txn_date", "ledger_acct", "narrative", "gross_amount"),
}

DATE_FORMATS: dict[str, str] = {
    "A": "%Y-%m-%d",
    "B": "%Y-%m-%d",
    "C": "%d/%m/%Y",
}


def parse_date(system: str, text: str) -> date:
    """Read a date field the way ``system`` writes it."""
    try:
        return datetime.strptime(text, DATE_FORMATS[system]).date()
    except ValueError as exc:
        raise LedgerParseError(f"date {text!r} is not in the {DATE_FORMATS[system]} format") from exc


def parse_amount(system: str, text: str) -> Decimal:
    """Read an amount field the way ``system`` writes it, as dollars."""
    if system == "B":
        return system_b.to_major_units(text)
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise LedgerParseError(f"amount {text!r} is not a number") from exc
    if not value.is_finite():
        raise LedgerParseError(f"amount {text!r} is not a number")
    return value


def record_from_row(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Build one record out of one raw row from ``system``."""
    id_column, date_column, account_column, description_column, amount_column = FIELD_COLUMNS[system]
    record_id = row[id_column]
    try:
        posted = parse_date(system, row[date_column])
        amount = parse_amount(system, row[amount_column])
    except LedgerParseError as exc:
        raise LedgerParseError(f"record {record_id}: {exc}") from exc
    code = row[account_column]
    return Record(
        record_id=record_id,
        source_system=system,
        date=posted,
        account_code=code,
        account_name=mapping.account_name(code, unknown_label),
        description=row[description_column],
        amount=amount,
    )


def read_export(path: Path, unknown_label: str) -> list[Record]:
    """Read every posting in one export file, whichever system wrote it."""
    source = Path(path)
    system = detect_system(source)
    if system == "A":
        rows = system_a.read_rows(source)
    elif system == "B":
        rows = system_b.read_rows(source)
    else:
        rows = system_c.read_rows(source)
    try:
        records = [record_from_row(system, row, unknown_label) for row in rows]
    except LedgerParseError as exc:
        raise LedgerParseError(f"{source.name}: {exc}") from exc
    _log.info("built %d record(s) from %s as system %s", len(records), source.name, system)
    return records
