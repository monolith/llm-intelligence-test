"""Merge exports into one normalized file."""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal
from pathlib import Path

from ledgerkit.core.normalize import normalize
from ledgerkit.core.records import Record, RECORD_COLUMNS
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)


def row_to_record(system: str, row: dict[str, str], settings_unknown_label: str) -> Record:
    """Convert a raw row from a parser to a Record."""
    if system == "A":
        return _row_a_to_record(row, settings_unknown_label)
    elif system == "B":
        return _row_b_to_record(row, settings_unknown_label)
    else:  # system == "C"
        return _row_c_to_record(row, settings_unknown_label)


def _row_a_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System A row to a Record."""
    posted_on = date.fromisoformat(row["posted_on"])
    amount = Decimal(row["amount"])
    return Record(
        record_id=row["entry_id"],
        source_system="A",
        date=posted_on,
        account_code=row["account"],
        account_name=account_name(row["account"], unknown_label),
        description=row["memo"],
        amount=amount,
    )


def _row_b_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System B row to a Record."""
    value_date = date.fromisoformat(row["value_date"])
    amount = system_b.to_major_units(row["amount"])
    return Record(
        record_id=row["doc_no"],
        source_system="B",
        date=value_date,
        account_code=row["acct"],
        account_name=account_name(row["acct"], unknown_label),
        description=row["descr"],
        amount=amount,
    )


def _row_c_to_record(row: dict[str, str], unknown_label: str) -> Record:
    """Convert a System C row to a Record."""
    # Parse DD/MM/YYYY format
    txn_date_parts = row["txn_date"].split("/")
    day, month, year = int(txn_date_parts[0]), int(txn_date_parts[1]), int(txn_date_parts[2])
    txn_date = date(year, month, day)
    amount = Decimal(row["gross_amount"])
    return Record(
        record_id=row["ref"],
        source_system="C",
        date=txn_date,
        account_code=row["ledger_acct"],
        account_name=account_name(row["ledger_acct"], unknown_label),
        description=row["narrative"],
        amount=amount,
    )


def ingest(file_paths: list[str], out_path: Path, unknown_label: str) -> int:
    """Read and merge export files into a normalized CSV.

    Returns the number of rows written.
    """
    records: list[Record] = []

    for file_path in file_paths:
        path = Path(file_path)
        try:
            system = detect_system(path)
            _log.info("reading %s as system %s", path.name, system)

            if system == "A":
                rows = system_a.read_rows(path)
            elif system == "B":
                rows = system_b.read_rows(path)
            else:  # system == "C"
                rows = system_c.read_rows(path)

            for row in rows:
                record = row_to_record(system, row, unknown_label)
                records.append(record)
        except Exception as exc:
            _log.error("error reading %s: %s", path, exc)
            raise

    # Normalize and sort records
    normalized = normalize(records, keep_refunds=True)

    # Create output directory if needed
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with out_path.open("w", encoding="utf-8", newline="") as f:
        # Write header
        f.write(",".join(RECORD_COLUMNS) + "\n")

        # Write records
        for record in normalized:
            row_data = record.to_row()
            # Quote description if needed
            description = row_data[5]
            if "," in description or '"' in description or "\n" in description:
                description = '"' + description.replace('"', '""') + '"'
                row_data[5] = description
            f.write(",".join(row_data) + "\n")

    return len(normalized)
