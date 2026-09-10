"""Tests for ingest, report, reconcile, validate and the global --config option."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]
RECORDS_HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


def run(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def records_file(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]

    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == RECORDS_HEADER
    assert '"Rebill, ""Q1 true-up"", carrier"' in text

    rows = list(csv.DictReader(text.splitlines()))
    assert len(rows) == 120
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5
    assert {row["source_system"] for row in rows} == {"A", "B", "C"}
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert by_id["B-2201"]["amount"] == "254.40"
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["A-10041"]["account_name"] == "UNCLASSIFIED"
    assert all(row["account_name"] == "Contract Labor" for row in rows if row["account_code"] == "5200")


def test_ingest_default_out_is_relative_to_working_directory(tmp_path: Path) -> None:
    result = run("ingest", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out" / "records.csv").is_file()


def test_ingest_fails_cleanly_on_unknown_file(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.csv"
    bogus.write_text("not,an,export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", str(bogus), "--out", str(out))
    assert result.returncode != 0
    assert not out.exists()
    assert "LEDGERKIT WARNING" in result.stderr


# --- report -------------------------------------------------------------------


def test_report_by_account(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;6248",
        "4200;Duty and Brokerage;2971",
        "4300;Storage;2886",
        "5100;Packaging Materials;3400",
        "5200;Contract Labor;1748",
        "5300;Equipment Rental;1621",
        "6100;Utilities;3577",
        "6200;Insurance;4400",
        "8800;UNCLASSIFIED;315",
        "9000;Suspense;417",
    ]


def test_report_by_month(records_file: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_include_refunds_is_accepted_and_changes_nothing(records_file: Path) -> None:
    plain = run("report", "--by", "month", "--records", str(records_file))
    flagged = run("report", "--by", "month", "--records", str(records_file), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_rounds_half_to_even(tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    records.write_text(
        RECORDS_HEADER + "\n"
        "X-1,A,2026-01-01,4100,Freight In,a,1.25\n"
        "X-2,A,2026-01-02,4100,Freight In,b,1.25\n"
        "X-3,B,2026-02-01,4200,Duty and Brokerage,c,3.50\n"
        "X-4,C,2026-03-01,4300,Storage,d,1240.50\n"
        "X-5,C,2026-04-01,5100,Packaging Materials,e,883.50\n",
        encoding="utf-8",
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert [line.rsplit(";", 1)[1] for line in result.stdout.splitlines()[1:]] == ["2", "4", "1240", "884"]


def test_report_decimals_from_config(records_file: Path, tmp_path: Path) -> None:
    override = tmp_path / "two-places.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")
    result = run("--config", str(override), "report", "--by", "account", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "4100;Freight In;6248.50" in lines
    assert "5200;Contract Labor;1747.50" in lines


def test_report_requires_by() -> None:
    assert run("report").returncode == 2


def test_report_missing_records_file(tmp_path: Path) -> None:
    result = run("report", "--by", "month", "--records", str(tmp_path / "absent.csv"))
    assert result.returncode != 0
    assert result.stdout == ""


# --- reconcile ----------------------------------------------------------------


def test_reconcile_default_tolerance(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
        "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
        "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
        "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
        "mismatches=5",
    ]


def test_reconcile_tolerance_flag(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file), "--tolerance", "20")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "mismatches=1",
    ]


def test_reconcile_tolerance_from_config(records_file: Path, tmp_path: Path) -> None:
    override = tmp_path / "loose.toml"
    override.write_text("[reconcile]\ntolerance = 100\n", encoding="utf-8")
    result = run("--config", str(override), "reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_rejects_bad_tolerance(records_file: Path) -> None:
    assert run("reconcile", "--records", str(records_file), "--tolerance", "lots").returncode == 2


# --- validate -----------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_reports_every_bad_row(tmp_path: Path) -> None:
    export_a = tmp_path / "a.csv"
    export_a.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Quoted, fine",1.00,USD\n'
        "A-2,2026-13-03,4100,Bad month,1.00,USD\n"
        "\n"
        "A-3,2026-01-03,41X0,Bad code,ten,USD\n"
        "A-4,2026-01-03,4100,Too,many,fields,1.00,USD\n",
        encoding="utf-8",
    )
    export_b = tmp_path / "b.csv"
    export_b.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Cents,25440,USD\n"
        "B,B-2,2026-01-07,4100,Dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    export_c = tmp_path / "c.csv"
    export_c.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,Day first,1.00,USD\n"
        "C-2,01/13/2026,4100,Month first,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(export_a), str(export_b), str(export_c))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=8 rejected=5"]

    warnings = [line for line in result.stderr.splitlines() if line.startswith("LEDGERKIT WARNING")]
    assert len(warnings) == 5
    assert f"{export_a} line 4:" in warnings[0] and "posted_on" in warnings[0]
    assert f"{export_a} line 6:" in warnings[1] and "41X0" in warnings[1] and "ten" in warnings[1]
    assert f"{export_a} line 7:" in warnings[2] and "expected 6 fields, found 8" in warnings[2]
    assert f"{export_b} line 3:" in warnings[3] and "cents" in warnings[3]
    assert f"{export_c} line 4:" in warnings[4] and "txn_date" in warnings[4]


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.csv"
    bogus.write_text("not,an,export\n", encoding="utf-8")
    result = run("validate", SAMPLE_FILES[1], str(bogus), str(tmp_path / "absent.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]
    assert result.stderr.count("LEDGERKIT WARNING") == 2


def test_validate_pattern_from_config(tmp_path: Path) -> None:
    override = tmp_path / "strict.toml"
    override.write_text('[validate]\naccount_code_pattern = "^[1-7][0-9]{3}$"\n', encoding="utf-8")
    result = run("--config", str(override), "validate", SAMPLE_FILES[0])
    assert result.returncode == 2
    # The A sample ends with two 8800 rows and one 9000 row.
    assert result.stdout.splitlines() == ["checked=42 rejected=3"]
    assert result.stderr.count("does not match") == 3


# --- --config -----------------------------------------------------------------


def test_config_option_names_the_settings_file(tmp_path: Path) -> None:
    override = tmp_path / "run.toml"
    override.write_text("[report]\ndecimals = 1\n", encoding="utf-8")
    result = run("--config", str(override), "version")
    assert result.returncode == 0, result.stderr
    assert f"settings={override}" in result.stdout.splitlines()


def test_config_option_leaves_environment_as_it_was(tmp_path: Path) -> None:
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from ledgerkit.cli import main

    override = tmp_path / "run.toml"
    override.write_text("", encoding="utf-8")
    before = os.environ.get("LEDGERKIT_CONFIG")
    assert main(["--config", str(override), "version"]) == 0
    assert os.environ.get("LEDGERKIT_CONFIG") == before


def test_commands_leave_config_directory_untouched(tmp_path: Path, records_file: Path) -> None:
    config_dir = REPO / "config"
    before = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    override = tmp_path / "run.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")
    run("--config", str(override), "report", "--by", "account", "--records", str(records_file))
    run("--config", str(tmp_path / "absent.toml"), "validate", *SAMPLE_FILES)
    after = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    assert after == before
