"""Tests for ``ledgerkit reconcile``."""

from __future__ import annotations

from pathlib import Path

from conftest import Runner

SAMPLE_MISMATCHES = """\
MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-
MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05
MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55
MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60
MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-
mismatches=5
"""


def test_reconcile_samples(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("reconcile")
    assert result.returncode == 0, result.stderr
    assert result.stdout == SAMPLE_MISMATCHES


def test_reconcile_tolerance_flag(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("reconcile", "--records", str(ingested), "--tolerance", "16.30")
    assert result.returncode == 0, result.stderr
    # 16.30 exactly is within tolerance; only strictly greater spreads are reported.
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
        "mismatches=2",
    ]


def test_reconcile_ignores_single_system_combinations_and_counts_refunds(ledgerkit: Runner, tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    records.write_text(
        "record_id,source_system,date,account_code,account_name,description,amount\n"
        "A-1,A,2026-01-05,4100,Freight In,x,100.00\n"
        "B-1,B,2026-01-06,4100,Freight In,x,100.00\n"
        "B-2,B,2026-01-07,4100,Freight In,refund,-10.00\n"
        "C-1,C,2026-01-08,6200,Insurance,only one system,999.00\n",
        encoding="utf-8",
    )
    result = ledgerkit("reconcile", "--records", str(records))
    assert result.stdout == "MISMATCH 4100 2026-01 spread=10.00 A=100.00 B=90.00 C=-\nmismatches=1\n"


def test_reconcile_with_no_mismatches_still_prints_the_count(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("reconcile", "--tolerance", "100")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "mismatches=0\n"


def test_reconcile_rejects_a_non_numeric_tolerance(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("reconcile", "--tolerance", "lots")
    assert result.returncode == 2
    assert "--tolerance" in result.stderr
