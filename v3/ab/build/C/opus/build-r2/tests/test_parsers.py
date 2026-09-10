"""Smoke tests for the three readers and the format sniffer."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from datetime import date  # noqa: E402
from decimal import Decimal  # noqa: E402

import pytest  # noqa: E402

from ledgerkit.core.records import LedgerParseError  # noqa: E402
from ledgerkit.parsers import (  # noqa: E402
    detect_system,
    read_records,
    system_a,
    system_b,
    system_c,
)

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


def test_system_a_reads_quoted_memos() -> None:
    rows = system_a.read_rows(SAMPLES / "system_a_export.csv")
    assert len(rows) == 42
    assert rows[0]["memo"] == 'Rebill, "Q1 true-up", carrier'
    assert rows[0]["amount"] == "239.55"
    assert rows[1]["memo"] == "Drayage, port apron to DC"


def test_read_records_scales_borough_cents_to_dollars() -> None:
    records = {r.record_id: r for r in read_records(SAMPLES / "system_b_export.csv", "UNCLASSIFIED")}
    assert records["B-2201"].amount == Decimal("254.40")
    assert records["B-2221"].amount == Decimal("-88.25")
    assert records["B-2201"].date == date(2026, 1, 7)


def test_read_records_reads_calder_dates_day_first() -> None:
    records = {r.record_id: r for r in read_records(SAMPLES / "system_c_export.csv", "UNCLASSIFIED")}
    assert records["C-0401"].date == date(2026, 1, 2)
    assert records["C-0405"].date == date(2026, 3, 4)
    assert records["C-0408"].date == date(2026, 3, 13)
    assert records["C-0401"].amount == Decimal("386.54")


def test_read_records_labels_unknown_codes_and_uses_current_names() -> None:
    records = {r.record_id: r for r in read_records(SAMPLES / "system_a_export.csv", "NOPE")}
    assert records["A-10040"].account_code == "8800"
    assert records["A-10040"].account_name == "NOPE"
    assert records["A-10024"].account_name == "Contract Labor"
    assert records["A-10001"].account_name == "Freight In"


def test_read_records_names_the_line_of_a_bad_row(tmp_path: Path) -> None:
    export = tmp_path / "borough.csv"
    export.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,100,USD\n"
        "B,B-2,07/01/2026,4100,Bad date,100,USD\n",
        encoding="utf-8",
    )
    with pytest.raises(LedgerParseError, match="borough.csv line 3"):
        read_records(export, "UNCLASSIFIED")
