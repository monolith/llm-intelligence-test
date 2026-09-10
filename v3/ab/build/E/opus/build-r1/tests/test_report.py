"""Tests for ``ledgerkit report``."""

from __future__ import annotations

from pathlib import Path

from conftest import Runner

BY_ACCOUNT = """\
account_code;account_name;total
4100;Freight In;6248
4200;Duty and Brokerage;2971
4300;Storage;2886
5100;Packaging Materials;3400
5200;Contract Labor;1748
5300;Equipment Rental;1621
6100;Utilities;3577
6200;Insurance;4400
8800;UNCLASSIFIED;315
9000;Suspense;417
"""

BY_MONTH = """\
month;total
2026-01;13256
2026-02;8456
2026-03;5870
"""


def test_report_by_account(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("report", "--by", "account")
    assert result.returncode == 0, result.stderr
    assert result.stdout == BY_ACCOUNT


def test_report_by_month(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("report", "--by", "month", "--records", str(ingested))
    assert result.returncode == 0, result.stderr
    assert result.stdout == BY_MONTH


def test_include_refunds_is_accepted_and_changes_nothing(ledgerkit: Runner, ingested: Path) -> None:
    result = ledgerkit("report", "--by", "account", "--include-refunds")
    assert result.returncode == 0, result.stderr
    assert result.stdout == BY_ACCOUNT


def write_records(path: Path, *amounts: str) -> None:
    lines = ["record_id,source_system,date,account_code,account_name,description,amount"]
    for index, amount in enumerate(amounts):
        lines.append(f"X-{index},A,2026-01-0{index + 1},4100,Freight In,row {index},{amount}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_report_rounds_half_to_even(ledgerkit: Runner, tmp_path: Path) -> None:
    for amounts, shown in ((("1.25", "1.25"), "2"), (("1.75", "1.75"), "4"), (("1240.25", "0.25"), "1240")):
        records = tmp_path / "records.csv"
        write_records(records, *amounts)
        result = ledgerkit("report", "--by", "month", "--records", str(records))
        assert result.stdout.splitlines()[1] == f"2026-01;{shown}", amounts


def test_report_counts_refunds(ledgerkit: Runner, tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    write_records(records, "100.00", "-40.00")
    result = ledgerkit("report", "--by", "account", "--records", str(records))
    assert result.stdout.splitlines()[1] == "4100;Freight In;60"


def test_report_needs_a_records_file(ledgerkit: Runner) -> None:
    result = ledgerkit("report", "--by", "account")
    assert result.returncode != 0
    assert result.stdout == ""
    assert "records.csv" in result.stderr
