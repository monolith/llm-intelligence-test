"""Turn raw rows from any of the three readers into normalized records.

Each system names its columns differently and writes dates and amounts in its
own way; this module is where those differences get resolved into one
:class:`~ledgerkit.core.records.Record` shape. Nothing here drops a posting -
that is left to :func:`~ledgerkit.core.normalize.normalize`, which is called
with ``keep_refunds=True`` so every row survives.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from ledgerkit import mapping
from ledgerkit.config import Settings
from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.parsers import detect_system, read_rows, system_b

_log = get_logger(__name__)

# Which raw column holds each canonical field, per source system.
_ROW_FIELDS: dict[str, dict[str, str]] = {
    "A": {"id": "entry_id", "date": "posted_on", "account": "account", "description": "memo", "amount": "amount"},
    "B": {"id": "doc_no", "date": "value_date", "account": "acct", "description": "descr", "amount": "amount"},
    "C": {"id": "ref", "date": "txn_date", "account": "ledger_acct", "description": "narrative", "amount": "gross_amount"},
}


def _parse_date(system: str, raw: str) -> date:
    text = raw.strip()
    if system == "C":
        return datetime.strptime(text, "%d/%m/%Y").date()
    return date.fromisoformat(text)


def _parse_amount(system: str, raw: str) -> Decimal:
    if system == "B":
        return system_b.to_major_units(raw)
    return Decimal(raw.strip())


def record_from_row(system: str, row: dict[str, str], settings: Settings) -> Record:
    """Turn one raw row, as handed back by a reader, into a :class:`Record`."""
    names = _ROW_FIELDS[system]
    account_code = row[names["account"]].strip()
    return Record(
        record_id=row[names["id"]],
        source_system=system,
        date=_parse_date(system, row[names["date"]]),
        account_code=account_code,
        account_name=mapping.account_name(account_code, settings.unknown_account_label),
        description=row[names["description"]],
        amount=_parse_amount(system, row[names["amount"]]),
    )


def build_records(paths: Sequence[Path], settings: Settings) -> list[Record]:
    """Read every file in ``paths`` and merge them into one normalized list.

    Files may be any mixture of the three systems, in any order. Every posting
    in every file appears in the result; nothing is filtered, deduplicated or
    summarized here.
    """
    records: list[Record] = []
    for path in paths:
        system = detect_system(path)
        for row in read_rows(path):
            try:
                records.append(record_from_row(system, row, settings))
            except ValueError as exc:
                raise LedgerParseError(f"{Path(path).name}: cannot read row {row!r}: {exc}") from exc
        _log.info("built records for %s (system %s)", Path(path).name, system)
    return normalize(records, keep_refunds=True)
