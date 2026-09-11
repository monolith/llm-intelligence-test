"""Smoke tests for the three readers and the format sniffer."""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

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


def test_system_a_reads_quoted_memos() -> None:
    rows = system_a.read_rows(SAMPLES / "system_a_export.csv")
    assert len(rows) == 42
    assert rows[0]["memo"] == 'Rebill, "Q1 true-up", carrier'
    assert rows[1]["memo"] == "Drayage, port apron to DC"
    assert rows[0]["amount"] == "239.55"


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
