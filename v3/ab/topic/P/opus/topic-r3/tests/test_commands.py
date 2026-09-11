"""Tests for ingest, report, reconcile, validate and the global --config option."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [
    SAMPLES / "system_a_export.csv",
    SAMPLES / "system_b_export.csv",
    SAMPLES / "system_c_export.csv",
]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


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


def ingest_samples(tmp_path: Path, files: list[Path] = SAMPLE_FILES) -> Path:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *map(str, files), "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    return out


def read_output(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "override.toml"
    path.write_text(text, encoding="utf-8")
    return path


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting_normalized(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    assert out.read_text(encoding="utf-8").splitlines()[0] == HEADER
    rows = {row["record_id"]: row for row in read_output(out)}
    assert len(rows) == 120
    assert {row["source_system"] for row in rows.values()} == {"A", "B", "C"}
    # Quoted Ardent memo survives intact.
    assert rows["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    # Borough amounts are cents.
    assert rows["B-2201"]["amount"] == "254.40"
    assert rows["B-2221"]["amount"] == "-88.25"
    # Calder dates are day first.
    assert rows["C-0401"]["date"] == "2026-01-02"
    assert rows["C-0409"]["date"] == "2026-01-15"
    # Account names come from the map; 5200 is the FY-2 name; unknown codes get the label.
    assert rows["A-10024"]["account_name"] == "Contract Labor"
    assert rows["A-10040"]["account_name"] == "UNCLASSIFIED"
    # Refunds are kept.
    assert sum(1 for row in rows.values() if row["amount"].startswith("-")) == 5


def test_ingest_quotes_descriptions_that_need_it(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    text = out.read_text(encoding="utf-8")
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55\n' in text


def test_ingest_orders_by_date_system_id_whatever_the_input_order(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    rows = read_output(out)
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)

    other = ingest_samples(tmp_path / "reversed", list(reversed(SAMPLE_FILES)))
    assert other.read_bytes() == out.read_bytes()


def test_ingest_fails_without_writing_on_an_unreadable_file(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    result = run("ingest", str(SAMPLE_FILES[0]), str(tmp_path / "missing.csv"), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert not out.exists()


# --- report -------------------------------------------------------------------


def test_report_by_account_semicolons_refunds_counted_half_even(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;6248",  # 6248.50, half to even
        "4200;Duty and Brokerage;2971",
        "4300;Storage;2886",
        "5100;Packaging Materials;3400",  # 3765.00 less 365.00 of refunds
        "5200;Contract Labor;1748",  # 1747.50, half to even
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
        "2026-02;8456",  # 8456.50, half to even
        "2026-03;5870",
    ]


def test_report_include_refunds_is_accepted_and_changes_nothing(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    plain = run("report", "--by", "month", "--records", str(out))
    flagged = run("report", "--by", "month", "--records", str(out), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_decimals_come_from_config(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "report", "--by", "month", "--records", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[2] == "2026-02;8456.50"


# --- reconcile ----------------------------------------------------------------


def test_reconcile_reports_every_mismatch(tmp_path: Path) -> None:
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


def test_reconcile_a_spread_equal_to_the_tolerance_agrees(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(out), "--tolerance", "57.75")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_tolerance_from_config(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    config = write_config(tmp_path, "[reconcile]\ntolerance = 16.30\n")
    result = run("--config", str(config), "reconcile", "--records", str(out))
    assert result.returncode == 0, result.stderr
    # 57.75 and 16.75 exceed it; 6100 2026-01 sits exactly on it and agrees.
    assert result.stdout.splitlines()[-2:] == [
        "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
        "mismatches=2",
    ]


# --- validate -----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *map(str, SAMPLE_FILES))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_rejects_bad_rows_and_carries_on(tmp_path: Path) -> None:
    export = tmp_path / "ardent.csv"
    export.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Quoted, with a comma",100.00,USD\n'
        "A-2,2026-01-05,4100,Too few fields,USD\n"
        "A-3,2026-13-01,4100,Bad date,10.00,USD\n"
        "A-4,2026-01-06,4100,Bad amount,twelve,USD\n"
        "A-5,2026-01-07,41X0,Bad code,10.00,USD\n"
        "A-6,2026-01-08,5100,Fine,-2.50,USD\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=6 rejected=4"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 4
    for number in (4, 5, 6, 7):
        assert any(f"{export} line {number}:" in line for line in warnings)


def test_validate_reads_calder_dates_day_first(tmp_path: Path) -> None:
    export = tmp_path / "calder.csv"
    export.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,31/01/2026,4100,Day first,10.00,USD\n"
        "C-2,01/31/2026,4100,Month first,10.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=2 rejected=1"]
    assert "line 4:" in result.stderr


def test_validate_exits_2_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    result = run("validate", str(SAMPLE_FILES[1]), str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config -----------------------------------------------------------------


def test_config_option_names_the_settings_file(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 1\n")
    result = run("--config", str(config), "version")
    assert result.returncode == 0, result.stderr
    assert f"settings={config}" in result.stdout.splitlines()


def test_config_option_rejects_a_missing_file(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""


def test_config_directory_is_never_touched(tmp_path: Path) -> None:
    config_dir = REPO / "config"
    before = {path: path.read_bytes() for path in config_dir.rglob("*")}
    override = write_config(tmp_path, "[report]\ndecimals = 2\n[reconcile]\ntolerance = 1\n")
    out = tmp_path / "records.csv"
    for args in (
        ("ingest", *map(str, SAMPLE_FILES), "--out", str(out)),
        ("report", "--by", "account", "--records", str(out)),
        ("reconcile", "--records", str(out)),
        ("validate", *map(str, SAMPLE_FILES)),
    ):
        assert run("--config", str(override), *args).returncode == 0
    after = {path: path.read_bytes() for path in config_dir.rglob("*")}
    assert after == before
