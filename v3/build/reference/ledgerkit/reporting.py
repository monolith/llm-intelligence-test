"""Reading a normalized file back, and totalling it.

The commands that report never touch an export.  They read the CSV that
``ingest`` wrote, which is the one place the three systems have been made to
agree with each other.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

from ledgerkit.core.records import RECORD_COLUMNS, LedgerParseError, Record
from ledgerkit.log import get_logger

_log = get_logger(__name__)

CENTS = Decimal("0.01")
MISSING_SYSTEM = "-"


def read_records(path: Path) -> list[Record]:
    """Read a normalized records file back into :class:`Record` objects."""
    source = Path(path)
    if not source.is_file():
        raise LedgerParseError(f"{source}: no such records file; run ingest first")
    out: list[Record] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or tuple(reader.fieldnames) != RECORD_COLUMNS:
            raise LedgerParseError(f"{source}: header is not {','.join(RECORD_COLUMNS)}")
        for row in reader:
            out.append(
                Record(
                    record_id=row["record_id"],
                    source_system=row["source_system"],
                    date=date.fromisoformat(row["date"]),
                    account_code=row["account_code"],
                    account_name=row["account_name"],
                    description=row["description"],
                    amount=Decimal(row["amount"]).quantize(CENTS),
                )
            )
    _log.info("read %d record(s) from %s", len(out), source.name)
    return out


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even, as the conventions require."""
    exponent = Decimal(1).scaleb(-decimals)
    return value.quantize(exponent, rounding=ROUND_HALF_EVEN)


def totals_by_account(records: Iterable[Record]) -> dict[str, tuple[str, Decimal]]:
    """Total every account code, carrying its name along."""
    out: dict[str, tuple[str, Decimal]] = {}
    for record in records:
        name, running = out.get(record.account_code, (record.account_name, Decimal("0.00")))
        out[record.account_code] = (name, running + record.amount)
    return out


def totals_by_month(records: Iterable[Record]) -> dict[str, Decimal]:
    """Total every posting month, keyed ``YYYY-MM``."""
    out: dict[str, Decimal] = {}
    for record in records:
        out[record.month()] = out.get(record.month(), Decimal("0.00")) + record.amount
    return out


def system_totals(records: Iterable[Record]) -> dict[tuple[str, str], dict[str, Decimal]]:
    """Total every account and month combination, broken out by source system."""
    out: dict[tuple[str, str], dict[str, Decimal]] = {}
    for record in records:
        key = (record.account_code, record.month())
        per_system = out.setdefault(key, {})
        per_system[record.source_system] = per_system.get(record.source_system, Decimal("0.00")) + record.amount
    return out


def mismatches(
    records: Iterable[Record], tolerance: Decimal
) -> list[tuple[str, str, Decimal, dict[str, Decimal]]]:
    """Account and month combinations where two systems disagree by more than ``tolerance``."""
    found: list[tuple[str, str, Decimal, dict[str, Decimal]]] = []
    cells = system_totals(records)
    for (code, month) in sorted(cells):
        per_system = cells[(code, month)]
        if len(per_system) < 2:
            continue
        spread = max(per_system.values()) - min(per_system.values())
        if spread > tolerance:
            found.append((code, month, spread, per_system))
    return found
