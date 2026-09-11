"""Convert raw rows from each system into Record objects."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from ledgerkit.core.records import LedgerParseError, Record
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import system_a, system_b, system_c

_log = get_logger(__name__)


def system_a_to_records(rows: list[dict[str, str]], unknown_label: str) -> list[Record]:
    """Convert raw System A rows to Records."""
    records: list[Record] = []
    for raw in rows:
        posted_on_str = raw["posted_on"].strip()
        try:
            posted_on = datetime.fromisoformat(posted_on_str).date()
        except ValueError as e:
            raise LedgerParseError(f"System A date {posted_on_str!r} is not ISO format") from e

        amount_str = raw["amount"].strip()
        try:
            amount = Decimal(amount_str)
        except Exception as e:
            raise LedgerParseError(f"System A amount {amount_str!r} is not a number") from e

        account_code = raw["account"].strip()
        records.append(
            Record(
                record_id=raw["entry_id"].strip(),
                source_system="A",
                date=posted_on,
                account_code=account_code,
                account_name=account_name(account_code, unknown_label),
                description=raw["memo"].strip(),
                amount=amount,
            )
        )
    return records


def system_b_to_records(rows: list[dict[str, str]], unknown_label: str) -> list[Record]:
    """Convert raw System B rows to Records."""
    records: list[Record] = []
    for raw in rows:
        value_date_str = raw["value_date"].strip()
        try:
            value_date = datetime.fromisoformat(value_date_str).date()
        except ValueError as e:
            raise LedgerParseError(f"System B date {value_date_str!r} is not ISO format") from e

        amount_str = raw["amount"].strip()
        try:
            amount = system_b.to_major_units(amount_str)
        except LedgerParseError:
            raise

        account_code = raw["acct"].strip()
        records.append(
            Record(
                record_id=raw["doc_no"].strip(),
                source_system="B",
                date=value_date,
                account_code=account_code,
                account_name=account_name(account_code, unknown_label),
                description=raw["descr"].strip(),
                amount=amount,
            )
        )
    return records


def system_c_to_records(rows: list[dict[str, str]], unknown_label: str) -> list[Record]:
    """Convert raw System C rows to Records."""
    records: list[Record] = []
    for raw in rows:
        txn_date_str = raw["txn_date"].strip()
        try:
            # System C uses dd/mm/yyyy format
            day, month, year = txn_date_str.split("/")
            txn_date = date(int(year), int(month), int(day))
        except (ValueError, IndexError) as e:
            raise LedgerParseError(f"System C date {txn_date_str!r} is not dd/mm/yyyy format") from e

        amount_str = raw["gross_amount"].strip()
        try:
            amount = Decimal(amount_str)
        except Exception as e:
            raise LedgerParseError(f"System C amount {amount_str!r} is not a number") from e

        account_code = raw["ledger_acct"].strip()
        records.append(
            Record(
                record_id=raw["ref"].strip(),
                source_system="C",
                date=txn_date,
                account_code=account_code,
                account_name=account_name(account_code, unknown_label),
                description=raw["narrative"].strip(),
                amount=amount,
            )
        )
    return records
