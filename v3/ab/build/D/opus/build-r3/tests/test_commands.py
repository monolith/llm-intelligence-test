"""Tests for ingest, report, reconcile, validate and the global --config option."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_c_export.csv", "system_a_export.csv", "system_b_export.csv")]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"

RECORDS = (
    HEADER + "\n"
    "A-1,A,2026-01-05,4100,Freight In,x,1.25\n"
    "A-2,A,2026-01-06,4100,Freight In,x,1.25\n"
    "A-3,A,2026-01-07,4300,Storage,x,10.00\n"
    "B-1,B,2026-01-08,4300,Storage,x,10.05\n"
    'A-4,A,2026-02-01,4200,Duty and Brokerage,"Rebill, ""Q1""",5.00\n'
    "C-1,C,2026-02-02,4200,Duty and Brokerage,x,-1.50\n"
    "A-5,A,2026-02-03,4300,Storage,x,1.00\n"
    "C-2,C,2026-02-04,4300,Storage,x,1.10\n"
    "B-2,B,2026-02-05,5100,Packaging Materials,x,9.00\n"
)


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    env.pop("LEDGERKIT_LOG_LEVEL", None)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def write_records(tmp_path: Path) -> Path:
    path = tmp_path / "records.csv"
    path.write_text(RECORDS, encoding="utf-8")
    return path


def config_digest() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").rglob("*"))
        if path.is_file()
    }


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]

    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == HEADER
    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 120
    by_id = {row["record_id"]: row for row in rows}

    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert by_id["B-2201"]["amount"] == "254.40"
    assert by_id["B-2221"]["amount"] == "-88.25"
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["C-0409"]["date"] == "2026-01-15"
    assert by_id["A-10040"]["account_name"] == "UNCLASSIFIED"
    assert by_id["B-2222"]["account_name"] == "Contract Labor"
    assert {row["source_system"] for row in rows} == {"A", "B", "C"}
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5

    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_default_out_path_is_documented_in_help() -> None:
    result = run("ingest", "--help")
    assert result.returncode == 0
    assert "out/records.csv" in result.stdout


# --- report -------------------------------------------------------------------


def test_report_by_account_counts_refunds_and_rounds_half_even(tmp_path: Path) -> None:
    records = write_records(tmp_path)
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;2",
        "4200;Duty and Brokerage;4",
        "4300;Storage;22",
        "5100;Packaging Materials;9",
    ]


def test_report_include_refunds_flag_is_still_accepted(tmp_path: Path) -> None:
    records = write_records(tmp_path)
    plain = run("report", "--by", "account", "--records", str(records))
    flagged = run("report", "--by", "account", "--records", str(records), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_by_month(tmp_path: Path) -> None:
    records = write_records(tmp_path)
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;23", "2026-02;15"]


def test_report_requires_by() -> None:
    result = run("report")
    assert result.returncode != 0


# --- reconcile ----------------------------------------------------------------


def test_reconcile_reports_spreads_over_tolerance(tmp_path: Path) -> None:
    records = write_records(tmp_path)
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=6.50 A=5.00 B=- C=-1.50",
        "MISMATCH 4300 2026-02 spread=0.10 A=1.00 B=- C=1.10",
        "mismatches=2",
    ]


def test_reconcile_tolerance_flag(tmp_path: Path) -> None:
    records = write_records(tmp_path)
    loose = run("reconcile", "--records", str(records), "--tolerance", "1")
    assert loose.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=6.50 A=5.00 B=- C=-1.50",
        "mismatches=1",
    ]
    strict = run("reconcile", "--records", str(records), "--tolerance", "0")
    assert "MISMATCH 4300 2026-01 spread=0.05 A=10.00 B=10.05 C=-" in strict.stdout.splitlines()
    assert strict.stdout.splitlines()[-1] == "mismatches=3"


# --- validate -----------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_rejects_bad_rows_and_keeps_going(tmp_path: Path) -> None:
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,02/01/2026,4100,fine,1.00,USD\n"
        "C-2,2026-01-02,4100,iso date,1.00,USD\n"
        "C-3,13/13/2026,4100,no such month,1.00,USD\n"
        "C-4,02/01/2026,41A0,bad code,abc,USD\n"
        "C-5,02/01/2026,4100,extra,field,1.00,USD\n"
        "== 5 rows ==\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,fine,25440,USD\n"
        "B,B-2,2026-01-07,4100,dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    result = run("validate", str(calder), str(borough))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=7 rejected=5"]

    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 5
    for expected in (f"{calder} line 4", f"{calder} line 5", f"{calder} line 6", f"{calder} line 7", f"{borough} line 3"):
        assert any(expected in line for line in warnings), expected
    line_6 = next(line for line in warnings if f"{calder} line 6" in line)
    assert "gross_amount" in line_6 and "ledger_acct" in line_6


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    junk = tmp_path / "junk.csv"
    junk.write_text("hello\n", encoding="utf-8")
    result = run("validate", str(junk))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=0 rejected=0"]


# --- --config -----------------------------------------------------------------


def test_config_option_changes_settings_for_one_run(tmp_path: Path) -> None:
    before = config_digest()
    override = tmp_path / "run.toml"
    override.write_text(
        '[report]\ndecimals = 2\nunknown_account_label = "TBD"\n[reconcile]\ntolerance = 5\n'
        '[validate]\naccount_code_pattern = "^[0-9]{3}$"\n',
        encoding="utf-8",
    )
    records = write_records(tmp_path)

    version = run("--config", str(override), "version")
    assert version.returncode == 0, version.stderr
    assert f"settings={override}" in version.stdout.splitlines()

    report = run("--config", str(override), "report", "--by", "account", "--records", str(records))
    assert "4100;Freight In;2.50" in report.stdout.splitlines()

    reconcile = run("--config", str(override), "reconcile", "--records", str(records))
    assert reconcile.stdout.splitlines()[-1] == "mismatches=1"

    out = tmp_path / "records-out.csv"
    ingest = run("--config", str(override), "ingest", SAMPLE_FILES[1], "--out", str(out))
    assert ingest.returncode == 0, ingest.stderr
    assert ",8800,TBD," in out.read_text(encoding="utf-8")

    validate = run("--config", str(override), "validate", SAMPLE_FILES[1])
    assert validate.returncode == 2
    assert validate.stdout.splitlines() == ["checked=42 rejected=42"]

    inspect = run("--config", str(override), "inspect", SAMPLE_FILES[1])
    assert inspect.returncode == 0, inspect.stderr

    assert config_digest() == before


def test_config_option_missing_file_fails(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert "nope.toml" in result.stderr
