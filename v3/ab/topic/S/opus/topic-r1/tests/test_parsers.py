"""Smoke tests for the three readers and the format sniffer."""

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
from ledgerkit.parsers import detect_system, system_a, system_b, system_c  # noqa: E402

SAMPLES = REPO / "samples"


def test_detect_system_identifies_all_three() -> None:
    assert detect_system(SAMPLES / "system_a_export.csv") == "A"
    assert detect_system(SAMPLES / "system_b_export.csv") == "B"
    assert detect_system(SAMPLES / "system_c_export.csv") == "C"


def test_system_a_reads_an_export_without_quoted_memos(tmp_path: Path) -> None:
    export = tmp_path / "ardent.csv"
    export.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "# system: A\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        "A-90001,2026-01-04,4100,Inbound freight consolidation,100.00,USD\n"
        "A-90002,2026-01-05,5100,Corrugate 32 ECT,-12.50,USD\n",
        encoding="utf-8",
    )
    rows = system_a.read_rows(export)
    assert len(rows) == 2
    assert list(rows[0]) == list(system_a.COLUMNS)
    assert rows[0]["entry_id"] == "A-90001"
    assert rows[1]["amount"] == "-12.50"


def test_system_a_reads_quoted_memos_in_the_sample() -> None:
    rows = system_a.read_rows(SAMPLES / "system_a_export.csv")
    assert len(rows) == 42
    assert rows[0]["memo"] == 'Rebill, "Q1 true-up", carrier'
    assert rows[0]["amount"] == "239.55"
    assert rows[1]["memo"] == "Drayage, port apron to DC"


def test_read_fields_numbers_lines_as_they_sit_in_the_file() -> None:
    header, body = system_a.read_fields(SAMPLES / "system_a_export.csv")
    assert header == list(system_a.COLUMNS)
    assert body[0][0] == 6
    _, body = system_c.read_fields(SAMPLES / "system_c_export.csv")
    assert (body[0][0], body[-1][0]) == (3, 41)


def test_system_b_read_rows_shape() -> None:
    rows = system_b.read_rows(SAMPLES / "system_b_export.csv")
    assert len(rows) == 39
    assert list(rows[0]) == list(system_b.COLUMNS)
    assert {row["sys"] for row in rows} == {"B"}


def test_system_c_read_rows_shape() -> None:
    rows = system_c.read_rows(SAMPLES / "system_c_export.csv")
    assert len(rows) == 39
    assert list(rows[0]) == list(system_c.COLUMNS)
    assert system_c.read_trailer_count(SAMPLES / "system_c_export.csv") == 39


def test_to_record_reads_ardent_dollars_and_iso_dates() -> None:
    record = system_a.to_record(system_a.read_rows(SAMPLES / "system_a_export.csv")[0], "UNKNOWN")
    assert record.source_system == "A"
    assert record.date == date(2026, 1, 3)
    assert record.amount == Decimal("239.55")
    assert record.description == 'Rebill, "Q1 true-up", carrier'
    assert record.account_name == "Freight In"


def test_to_record_turns_borough_cents_into_dollars() -> None:
    rows = system_b.read_rows(SAMPLES / "system_b_export.csv")
    first = system_b.to_record(rows[0], "UNKNOWN")
    assert (first.record_id, first.date, first.amount) == ("B-2201", date(2026, 1, 7), Decimal("254.40"))
    refund = system_b.to_record(next(row for row in rows if row["doc_no"] == "B-2221"), "UNKNOWN")
    assert refund.amount == Decimal("-88.25")


def test_to_record_reads_calder_dates_day_first() -> None:
    rows = system_c.read_rows(SAMPLES / "system_c_export.csv")
    first = system_c.to_record(rows[0], "UNKNOWN")
    assert first.date == date(2026, 1, 2)
    assert first.amount == Decimal("386.54")
    unmapped = system_c.to_record(next(row for row in rows if row["ledger_acct"] == "8800"), "UNKNOWN")
    assert unmapped.account_name == "UNKNOWN"


def test_account_5200_uses_its_current_name() -> None:
    row = next(r for r in system_b.read_rows(SAMPLES / "system_b_export.csv") if r["acct"] == "5200")
    assert system_b.to_record(row, "UNKNOWN").account_name == "Contract Labor"


@pytest.mark.parametrize("raw", ["12.50", "1_000", "", "12e2"])
def test_borough_amount_must_be_whole_cents(raw: str) -> None:
    with pytest.raises(LedgerParseError):
        system_b.to_major_units(raw)


@pytest.mark.parametrize("raw", ["NaN", "1e3", "1_000.00", "12.345", "abc", ""])
def test_dollar_amounts_are_read_strictly(raw: str) -> None:
    with pytest.raises(LedgerParseError):
        system_a.parse_amount(raw)


def test_calder_rejects_a_month_first_date() -> None:
    with pytest.raises(LedgerParseError):
        system_c.parse_date("01/13/2026")
