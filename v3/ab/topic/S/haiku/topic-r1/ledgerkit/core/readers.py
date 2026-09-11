"""Convert system-specific rows to normalized Records."""

from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.records import Record, LedgerParseError
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def rows_to_records(path: Path, unknown_label: str) -> list[Record]:
    """Read all records from a file, converting based on the system it came from."""
    system = detect_system(path)
    rows = {
        "A": lambda p: system_a.read_rows(p),
        "B": lambda p: system_b.read_rows(p),
        "C": lambda p: system_c.read_rows(p),
    }[system](path)

    records: list[Record] = []
    for row_idx, row in enumerate(rows, start=1):
        try:
            record = _row_to_record(system, row, unknown_label)
            records.append(record)
        except LedgerParseError as exc:
            # Augment the error with the source file
            _log.warning("cannot convert row from %s: %s", path.name, exc)
            raise

    return records


def _row_to_record(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Convert a raw row from one system into a Record."""
    if system == "A":
        return _row_a_to_record(row, unknown_label)
    if system == "B":
        return _row_b_to_record(row, unknown_label)
    if system == "C":
        return _row_c_to_record(row, unknown_label)
    raise LedgerParseError(f"unknown system: {system}")


def _row_a_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System A row to a Record."""
    try:
        parsed_date = date.fromisoformat(row["posted_on"])
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"bad date {row.get('posted_on')!r}") from exc

    try:
        amount = Decimal(row["amount"])
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"bad amount {row.get('amount')!r}") from exc

    account_code = row.get("account", "").strip()
    if not account_code:
        raise LedgerParseError("missing account code")

    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=parsed_date,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row.get("memo", ""),
        amount=amount,
    )


def _row_b_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System B row to a Record."""
    try:
        parsed_date = date.fromisoformat(row["value_date"])
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"bad date {row.get('value_date')!r}") from exc

    amount = system_b.to_major_units(row.get("amount", ""))

    account_code = row.get("acct", "").strip()
    if not account_code:
        raise LedgerParseError("missing account code")

    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=parsed_date,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row.get("descr", ""),
        amount=amount,
    )


def _row_c_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System C row to a Record."""
    # System C uses DD/MM/YYYY format
    try:
        date_str = row["txn_date"]
        parsed_date = datetime.strptime(date_str, "%d/%m/%Y").date()
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"bad date {row.get('txn_date')!r}") from exc

    try:
        amount = Decimal(row["gross_amount"])
    except (ValueError, KeyError) as exc:
        raise LedgerParseError(f"bad amount {row.get('gross_amount')!r}") from exc

    account_code = row.get("ledger_acct", "").strip()
    if not account_code:
        raise LedgerParseError("missing account code")

    return Record(
        record_id=row["ref"],
        source_system="C",
        date=parsed_date,
        account_code=account_code,
        account_name=account_name(account_code, unknown_label),
        description=row.get("narrative", ""),
        amount=amount,
    )
