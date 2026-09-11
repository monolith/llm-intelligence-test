"""Tests for turning each system's rows into records."""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.core.records import LedgerParseError  # noqa: E402
from ledgerkit.parsers import read_records, system_a, system_b, system_c  # noqa: E402

SAMPLES = REPO / "samples"


def by_id(path: Path) -> dict[str, object]:
    return {record.record_id: record for record in read_records(path, "UNCLASSIFIED")}


def test_system_a_reads_quoted_memos() -> None:
    rows = system_a.read_rows(SAMPLES / "system_a_export.csv")
    assert len(rows) == 42
    assert rows[0]["memo"] == 'Rebill, "Q1 true-up", carrier'
    assert rows[0]["amount"] == "239.55"


def test_system_a_records_are_dollars_and_iso_dates() -> None:
    record = by_id(SAMPLES / "system_a_export.csv")["A-10019"]
    assert record.source_system == "A"
    assert record.date == date(2026, 1, 3)
    assert record.amount == Decimal("-125.00")


def test_system_b_amounts_are_cents() -> None:
    records = by_id(SAMPLES / "system_b_export.csv")
    assert records["B-2201"].amount == Decimal("254.40")
    assert records["B-2221"].amount == Decimal("-88.25")
    assert records["B-2201"].date == date(2026, 1, 7)


def test_system_c_dates_are_day_first() -> None:
    records = by_id(SAMPLES / "system_c_export.csv")
    assert records["C-0401"].date == date(2026, 1, 2)
    assert records["C-0405"].date == date(2026, 3, 4)
    assert records["C-0408"].date == date(2026, 3, 13)
    assert records["C-0401"].amount == Decimal("386.54")


def test_account_names_come_from_the_map() -> None:
    records = by_id(SAMPLES / "system_a_export.csv")
    assert records["A-10024"].account_name == "Contract Labor"
    assert records["A-10040"].account_name == "UNCLASSIFIED"


def test_record_text_is_kept_exactly(tmp_path: Path) -> None:
    export = tmp_path / "ardent.csv"
    export.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1 ,2026-01-04,4100,"  two  spaces, ""quoted""  ",1.00,USD\n',
        encoding="utf-8",
    )
    (record,) = read_records(export, "UNCLASSIFIED")
    assert record.record_id == "A-1 "
    assert record.description == '  two  spaces, "quoted"  '


@pytest.mark.parametrize(
    ("raw", "reader"),
    [
        ("2026-1-03", system_a.parse_date),
        ("2026-02-30", system_b.parse_date),
        ("2026-01-02", system_c.parse_date),
        ("01/13/2026", system_c.parse_date),
    ],
)
def test_dates_not_in_the_systems_format_are_rejected(raw: str, reader: object) -> None:
    with pytest.raises(LedgerParseError):
        reader(raw)  # type: ignore[operator]


@pytest.mark.parametrize(
    ("raw", "reader"),
    [
        ("12.x", system_a.parse_amount),
        ("NaN", system_c.parse_amount),
        ("254.40", system_b.parse_amount),
        ("", system_b.parse_amount),
    ],
)
def test_amounts_that_are_not_numbers_are_rejected(raw: str, reader: object) -> None:
    with pytest.raises(LedgerParseError):
        reader(raw)  # type: ignore[operator]


def test_a_bad_value_names_the_file_and_record(tmp_path: Path) -> None:
    export = tmp_path / "borough.csv"
    export.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\nB,B-9,2026-01-07,4100,x,12.50,USD\n",
        encoding="utf-8",
    )
    with pytest.raises(LedgerParseError, match="borough.csv record B-9"):
        read_records(export, "UNCLASSIFIED")
