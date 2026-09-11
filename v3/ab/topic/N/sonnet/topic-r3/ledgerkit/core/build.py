"""Turn a raw row from a system reader into a normalized :class:`Record`.

Readers only get a file's shape right; this module is where the raw strings
they hand back are interpreted, one system at a time, per
``docs/CONVENTIONS.md``'s "Reading a file" section.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_b

_ID_COLUMN: dict[str, str] = {"A": "entry_id", "B": "doc_no", "C": "ref"}
_DATE_COLUMN: dict[str, str] = {"A": "posted_on", "B": "value_date", "C": "txn_date"}
_ACCOUNT_COLUMN: dict[str, str] = {"A": "account", "B": "acct", "C": "ledger_acct"}
_DESCRIPTION_COLUMN: dict[str, str] = {"A": "memo", "B": "descr", "C": "narrative"}
_AMOUNT_COLUMN: dict[str, str] = {"A": "amount", "B": "amount", "C": "gross_amount"}


def _parse_date(system: str, raw: str) -> date:
    if system == "C":
        # Calder writes day first, dd/mm/yyyy; Ardent and Borough both write ISO.
        try:
            return datetime.strptime(raw, "%d/%m/%Y").date()
        except ValueError as exc:
            raise LedgerParseError(f"unreadable Calder date {raw!r}") from exc
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise LedgerParseError(f"unreadable date {raw!r}") from exc


def _parse_amount(system: str, raw: str) -> Decimal:
    if system == "B":
        return system_b.to_major_units(raw)
    try:
        return Decimal(raw.strip())
    except InvalidOperation as exc:
        raise LedgerParseError(f"unreadable amount {raw!r}") from exc


def record_from_row(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Build one :class:`Record` out of one raw row from ``system``.

    ``record_id`` and ``description`` are carried through exactly as the source
    system wrote them, including any internal whitespace, delimiter or quote
    character -- unlike :func:`ledgerkit.core.normalize.normalize`, which
    collapses and cases fields for reports built off refund-adjusted totals,
    this is for ``ingest``, whose output is meant to preserve every posting
    exactly.
    """
    code = row[_ACCOUNT_COLUMN[system]]
    return Record(
        record_id=row[_ID_COLUMN[system]],
        source_system=system,
        date=_parse_date(system, row[_DATE_COLUMN[system]]),
        account_code=code,
        account_name=account_name(code, unknown_label),
        description=row[_DESCRIPTION_COLUMN[system]],
        amount=_parse_amount(system, row[_AMOUNT_COLUMN[system]]),
    )
