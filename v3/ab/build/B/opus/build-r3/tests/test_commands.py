"""End to end tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
EXPORTS = [
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
    str(SAMPLES / "system_c_export.csv"),
]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def ingest_samples(tmp_path: Path) -> Path:
    out = tmp_path / "nested" / "records.csv"
    result = run("ingest", *reversed(EXPORTS), "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    return out


# --- ingest ----------------------------------------------------------------


def test_ingest_writes_every_posting_normalized(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    rows = list(csv.DictReader(text.splitlines()))
    assert len(rows) == 120
    assert {row["source_system"] for row in rows} == {"A", "B", "C"}
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)

    by_id = {row["record_id"]: row for row in rows}
    # Quoted Ardent memo survives, commas and quotes included.
    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert '"Rebill, ""Q1 true-up"", carrier"' in text
    # Borough cents become dollars.
    assert by_id["B-2201"]["amount"] == "254.40"
    # Calder dates are day first.
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["C-0403"]["date"] == "2026-01-11"
    # Account names come from the map; unknown codes get the configured label.
    assert {row["account_name"] for row in rows if row["account_code"] == "5200"} == {"Contract Labor"}
    assert {row["account_name"] for row in rows if row["account_code"] == "8800"} == {"UNCLASSIFIED"}


def test_ingest_fails_without_writing_on_unreadable_file(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.csv"
    bogus.write_text("not,an,export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", EXPORTS[0], str(bogus), "--out", str(out))
    assert result.returncode == 2
    assert result.stdout == ""
    assert not out.exists()


# --- report ----------------------------------------------------------------


def test_report_by_account_counts_refunds_and_uses_semicolons(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;6248",  # exact 6248.50, half to even
        "4200;Duty and Brokerage;2971",
        "4300;Storage;2886",
        "5100;Packaging Materials;3400",
        "5200;Contract Labor;1748",  # exact 1747.50
        "5300;Equipment Rental;1621",
        "6100;Utilities;3577",
        "6200;Insurance;4400",
        "8800;UNCLASSIFIED;315",
        "9000;Suspense;417",
    ]


def test_report_by_month(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("report", "--by", "month", "--records", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "month;total",
        "2026-01;13256",
        "2026-02;8456",
        "2026-03;5870",
    ]
    flagged = run("report", "--by", "month", "--records", str(out), "--include-refunds")
    assert flagged.stdout == result.stdout


def test_report_rounds_half_to_even(tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    records.write_text(
        "record_id,source_system,date,account_code,account_name,description,amount\n"
        "X-1,A,2026-01-01,4100,Freight In,a,2.50\n"
        "X-2,A,2026-01-01,4200,Duty and Brokerage,b,3.50\n"
        "X-3,A,2026-02-01,4300,Storage,c,-0.40\n",
        encoding="utf-8",
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.stdout.splitlines()[1:] == [
        "4100;Freight In;2",
        "4200;Duty and Brokerage;4",
        "4300;Storage;0",
    ]


def test_report_missing_records_file(tmp_path: Path) -> None:
    result = run("report", "--by", "month", "--records", str(tmp_path / "nope.csv"))
    assert result.returncode == 2
    assert result.stdout == ""


# --- reconcile -------------------------------------------------------------


def test_reconcile_samples(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
        "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
        "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
        "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
        "mismatches=5",
    ]


def test_reconcile_tolerance_flag(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    loose = run("reconcile", "--records", str(out), "--tolerance", "20")
    assert loose.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "mismatches=1",
    ]
    # 6200 2026-01 has a spread of 0.03: inside the default 0.05, outside 0.
    strict = run("reconcile", "--records", str(out), "--tolerance", "0")
    assert "MISMATCH 6200 2026-01 spread=0.03" in strict.stdout


# --- validate --------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *EXPORTS)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_reports_every_bad_row(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Quoted, fine",100.00,USD\n'
        "A-2,2026-13-04,4100,bad date,100.00,USD\n"
        "A-3,2026-01-04,41X0,bad code,abc,USD\n"
        "A-4,2026-01-04,4100,too,many,fields,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,25/01/2026,4100,day first,1.00,USD\n"
        "C-2,2026-01-25,4100,iso date,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,cents,25440,USD\n"
        "B,B-2,2026-01-07,4100,not cents,254.40,USD\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(calder), str(borough))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=8 rejected=5"]
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 5
    assert any(f"{ardent} line 4:" in line and "date" in line for line in warnings)
    assert any(
        f"{ardent} line 5:" in line and "amount" in line and "account code" in line for line in warnings
    )
    assert any(f"{ardent} line 6:" in line and "expected 6 fields, found 7" in line for line in warnings)
    assert any(f"{calder} line 4:" in line for line in warnings)
    assert any(f"{borough} line 3:" in line for line in warnings)


def test_validate_unreadable_file(tmp_path: Path) -> None:
    result = run("validate", EXPORTS[1], str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config --------------------------------------------------------------


def test_config_option_applies_to_every_command(tmp_path: Path) -> None:
    settings_dir = REPO / "config"
    before = {p.name: p.read_bytes() for p in settings_dir.iterdir()}

    override = tmp_path / "quarter.toml"
    override.write_text(
        '[report]\ndecimals = 2\nunknown_account_label = "TBD"\n'
        "[reconcile]\ntolerance = 20\n"
        '[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n',
        encoding="utf-8",
    )
    out = tmp_path / "records.csv"
    assert run("--config", str(override), "ingest", *EXPORTS, "--out", str(out)).returncode == 0
    assert ",8800,TBD," in out.read_text(encoding="utf-8")

    report = run("--config", str(override), "report", "--by", "account", "--records", str(out))
    assert "4100;Freight In;6248.50" in report.stdout.splitlines()

    reconcile = run("--config", str(override), "reconcile", "--records", str(out))
    assert reconcile.stdout.splitlines()[-1] == "mismatches=1"

    validate = run("--config", str(override), "validate", EXPORTS[1])
    assert validate.returncode == 2

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    assert {p.name: p.read_bytes() for p in settings_dir.iterdir()} == before


def test_config_option_missing_file(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "absent.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
