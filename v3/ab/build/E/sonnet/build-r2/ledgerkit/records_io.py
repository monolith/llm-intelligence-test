"""Building :class:`Record` values from raw export rows, and reading and
writing the package's own normalized CSV.

Building a record is per-system, because each system names its columns
differently; reading and writing the normalized file is not, because
``ingest`` fixes that shape for every system at once.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from ledgerkit import convert, mapping
from ledgerkit.core import fields
from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

FIELD_NAMES: dict[str, dict[str, str]] = {
    "A": {
        "id": "entry_id",
        "date": "posted_on",
        "account": "account",
        "description": "memo",
        "amount": "amount",
    },
    "B": {
        "id": "doc_no",
        "date": "value_date",
        "account": "acct",
        "description": "descr",
        "amount": "amount",
    },
    "C": {
        "id": "ref",
        "date": "txn_date",
        "account": "ledger_acct",
        "description": "narrative",
        "amount": "gross_amount",
    },
}


def record_from_row(system: str, row: dict[str, str], unknown_label: str) -> Record:
    """Build one normalized :class:`Record` out of a raw row from ``system``."""
    names = FIELD_NAMES[system]
    account_code = row[names["account"]]
    return Record(
        record_id=row[names["id"]],
        source_system=system,
        date=convert.parse_date(system, row[names["date"]]),
        account_code=account_code,
        account_name=mapping.account_name(account_code, unknown_label),
        description=row[names["description"]],
        amount=convert.parse_amount(system, row[names["amount"]]),
    )


def write_normalized(path: Path, records: list[Record]) -> int:
    """Write ``records`` as the normalized CSV at ``path``. Returns the row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [fields.join_record(list(RECORD_COLUMNS))]
    lines.extend(fields.join_record(record.to_row()) for record in records)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _log.info("wrote %d row(s) to %s", len(records), path)
    return len(records)


def read_normalized(path: Path) -> list[Record]:
    """Read a normalized CSV written by :func:`write_normalized` back into records."""
    text = Path(path).read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []

    header = fields.split_record(lines[0])
    if list(header) != list(RECORD_COLUMNS):
        raise LedgerParseError(f"{Path(path).name}: unexpected header {header!r}")

    records: list[Record] = []
    for number, line in enumerate(lines[1:], start=2):
        values = fields.split_record(line)
        if len(values) != len(RECORD_COLUMNS):
            raise LedgerParseError(
                f"{Path(path).name} line {number}: expected {len(RECORD_COLUMNS)} fields, "
                f"found {len(values)}"
            )
        row = dict(zip(RECORD_COLUMNS, values, strict=True))
        records.append(
            Record(
                record_id=row["record_id"],
                source_system=row["source_system"],
                date=date.fromisoformat(row["date"]),
                account_code=row["account_code"],
                account_name=row["account_name"],
                description=row["description"],
                amount=Decimal(row["amount"]),
            )
        )
    return records
