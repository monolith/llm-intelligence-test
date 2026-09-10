"""Records built from exports, and the normalized records file.

:func:`records_from_export` turns one export into :class:`Record` values, one per
posting.  Each system's reader module supplies the column names and the date and
amount conversions, so this module never needs to know how a system writes
things.  Nothing is filtered, deduplicated or tidied: the record id, account code
and description stay exactly as the source wrote them.

:func:`write_records` and :func:`read_records` are the two ends of the normalized
file that ``ingest`` writes and ``report`` and ``reconcile`` read.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import ModuleType

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.mapping import account_name
from ledgerkit.parsers import detect_system, system_a, system_b, system_c

_log = get_logger(__name__)

READERS: dict[str, ModuleType] = {"A": system_a, "B": system_b, "C": system_c}


def record_fields(reader: ModuleType) -> tuple[str, ...]:
    """The columns of a system that a :class:`Record` is built from."""
    return (
        reader.ID_FIELD,
        reader.DATE_FIELD,
        reader.ACCOUNT_FIELD,
        reader.DESCRIPTION_FIELD,
        reader.AMOUNT_FIELD,
    )


def records_from_export(path: Path, unknown_label: str) -> list[Record]:
    """Read one export file and return one record per posting, in file order."""
    source = Path(path)
    system = detect_system(source)
    reader = READERS[system]
    records: list[Record] = []
    for number, row in enumerate(reader.read_rows(source), start=1):
        missing = [column for column in record_fields(reader) if column not in row]
        if missing:
            raise LedgerParseError(f"{source.name}: no {', '.join(missing)} column in the header")
        code = row[reader.ACCOUNT_FIELD]
        try:
            record_date = reader.parse_date(row[reader.DATE_FIELD])
            amount = reader.parse_amount(row[reader.AMOUNT_FIELD])
        except LedgerParseError as exc:
            raise LedgerParseError(f"{source.name} row {number}: {exc}") from exc
        records.append(
            Record(
                record_id=row[reader.ID_FIELD],
                source_system=system,
                date=record_date,
                account_code=code,
                account_name=account_name(code, unknown_label),
                description=row[reader.DESCRIPTION_FIELD],
                amount=amount,
            )
        )
    _log.info("built %d record(s) from %s (system %s)", len(records), source.name, system)
    return records


def ingest_files(paths: Iterable[Path], unknown_label: str) -> list[Record]:
    """Every posting in every file, in :func:`~ledgerkit.core.records.sort_key` order."""
    records: list[Record] = []
    for path in paths:
        records.extend(records_from_export(path, unknown_label))
    records.sort(key=sort_key)
    return records


def write_records(records: Sequence[Record], path: Path) -> None:
    """Write records as the normalized, comma separated file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        writer.writerows(record.to_row() for record in records)


def read_records(path: Path) -> list[Record]:
    """Read a normalized file written by :func:`write_records`."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in RECORD_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise LedgerParseError(f"{source.name}: not a records file, no {', '.join(missing)} column")
        for row in reader:
            try:
                record_date = date.fromisoformat(row["date"])
                amount = Decimal(row["amount"])
            except (TypeError, ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {reader.line_num}: bad date or amount") from exc
            records.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=record_date,
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=amount,
                )
            )
    return records
