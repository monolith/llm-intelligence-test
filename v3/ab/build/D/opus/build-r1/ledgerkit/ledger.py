"""The normalized records file: building it from exports, writing it, reading it back.

The file is comma separated with a :data:`~ledgerkit.core.records.RECORD_COLUMNS`
header, and fields are quoted where the CSV format requires it, so a description
keeps every delimiter and quote character its source system wrote.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record, sort_key
from ledgerkit.log import get_logger
from ledgerkit.parsers import read_records

_log = get_logger(__name__)

DEFAULT_RECORDS_PATH = Path("out") / "records.csv"


def ingest(paths: Sequence[Path], unknown_label: str) -> list[Record]:
    """Read every posting from every export and put them in normalized order.

    Nothing is filtered, deduplicated or cleaned: every posting in the input
    appears in the result, refunds included.
    """
    records: list[Record] = []
    for path in paths:
        records.extend(read_records(path, unknown_label))
    records.sort(key=sort_key)
    _log.info("ingested %d record(s) from %d file(s)", len(records), len(paths))
    return records


def write_records(records: Iterable[Record], path: Path) -> int:
    """Write records to ``path`` as a normalized file and return the row count.

    Parent directories are created when they do not exist.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(RECORD_COLUMNS)
        for record in records:
            writer.writerow(record.to_row())
            count += 1
    return count


def load_records(path: Path) -> list[Record]:
    """Read a normalized file written by :func:`write_records`."""
    source = Path(path)
    records: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or tuple(header) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source.name}: not a normalized records file (header is {header!r})")
        for values in reader:
            if not values:
                continue
            if len(values) != len(RECORD_COLUMNS):
                raise LedgerParseError(
                    f"{source.name} line {reader.line_num}: expected {len(RECORD_COLUMNS)} fields, "
                    f"found {len(values)}"
                )
            row = dict(zip(RECORD_COLUMNS, values, strict=True))
            try:
                posted = date.fromisoformat(row["date"])
                amount = Decimal(row["amount"])
            except (ValueError, InvalidOperation) as exc:
                raise LedgerParseError(f"{source.name} line {reader.line_num}: {exc}") from exc
            records.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=posted,
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=amount,
                )
            )
    return records
