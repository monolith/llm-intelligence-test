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
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]


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
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


def config_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted((REPO / "config").rglob("*")):
        digest.update(str(path).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting_in_order(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", SAMPLE_FILES[2], SAMPLE_FILES[0], SAMPLE_FILES[1], "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]

    text = out.read_text(encoding="utf-8")
    assert text.splitlines()[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 120
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)

    by_id = {row["record_id"]: row for row in rows}
    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in text
    assert by_id["B-2201"]["amount"] == "254.40"
    assert by_id["B-2221"]["amount"] == "-88.25"
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["C-0408"]["date"] == "2026-03-13"
    assert by_id["A-10024"]["account_name"] == "Contract Labor"
    assert by_id["A-10040"]["account_name"] == "UNCLASSIFIED"


def test_ingest_fails_without_writing_on_unreadable_input(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("not an export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_FILES[0], str(bad), "--out", str(out))
    assert result.returncode != 0
    assert not out.exists()
    assert result.stdout == ""


# --- report -------------------------------------------------------------------


def test_report_by_account_uses_semicolons_counts_refunds_and_rounds_half_even(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    assert "4100;Freight In;6248" in lines  # exactly 6248.50
    assert "5200;Contract Labor;1748" in lines  # exactly 1747.50
    assert "5100;Packaging Materials;3400" in lines  # refunds counted
    assert "8800;UNCLASSIFIED;315" in lines
    codes = [line.split(";")[0] for line in lines[1:]]
    assert codes == sorted(codes)

    with_flag = run("report", "--by", "account", "--records", str(records), "--include-refunds")
    assert with_flag.returncode == 0, with_flag.stderr
    assert with_flag.stdout == result.stdout


def test_report_by_month(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


# --- reconcile ----------------------------------------------------------------


def test_reconcile_reports_mismatches(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-"
    assert lines[-1] == f"mismatches={len(lines) - 1}"
    assert all(line.startswith("MISMATCH ") for line in lines[:-1])


def test_reconcile_tolerance_flag(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records), "--tolerance", "100000")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["mismatches=0"]


# --- validate -----------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_rejects_bad_rows_and_keeps_going(tmp_path: Path) -> None:
    export = tmp_path / "calder.csv"
    export.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,02/01/2026,4100,Fine,10.00,USD\n"
        "C-2,2026-01-02,4100,ISO date,10.00,USD\n"
        "C-3,03/01/2026,41X0,Bad code,ten,USD\n"
        "C-4,04/01/2026,4100,Too,many,fields,10.00,USD\n"
        "== 4 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=4 rejected=3"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 3
    assert "line 4" in warnings[0] and "calder.csv" in warnings[0]
    assert "line 5" in warnings[1] and "amount" in warnings[1] and "account code" in warnings[1]
    assert "line 6" in warnings[2] and "fields" in warnings[2]


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    result = run("validate", SAMPLE_FILES[1], str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config -----------------------------------------------------------------


def test_config_option_changes_settings_for_one_run(tmp_path: Path) -> None:
    before = config_digest()
    records = ingest_samples(tmp_path)
    override = tmp_path / "quarter-close.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")

    result = run("--config", str(override), "report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert "4100;Freight In;6248.50" in result.stdout.splitlines()

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    strict = tmp_path / "strict.toml"
    strict.write_text('[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n', encoding="utf-8")
    checked = run("--config", str(strict), "validate", SAMPLE_FILES[0])
    assert checked.returncode == 2
    assert checked.stdout.splitlines() == ["checked=42 rejected=3"]

    assert config_digest() == before


def test_config_option_with_missing_file_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
