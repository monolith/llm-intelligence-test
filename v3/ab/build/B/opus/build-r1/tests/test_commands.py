"""End to end tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
EXPORTS = [SAMPLES / "system_a_export.csv", SAMPLES / "system_b_export.csv", SAMPLES / "system_c_export.csv"]
SETTINGS_FILE = REPO / "config" / "settings.toml"


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


@pytest.fixture()
def records(tmp_path: Path) -> Path:
    out = tmp_path / "nested" / "records.csv"
    result = run("ingest", *map(str, reversed(EXPORTS)), "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    return out


def test_ingest_keeps_every_posting_and_normalizes_units(records: Path) -> None:
    lines = records.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    assert len(lines) == 121
    # Quoted Ardent memo survives with its comma and quotes.
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines
    # Borough cents become dollars.
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    # Calder dates are day first.
    assert "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54" in lines
    # Unknown codes get the configured label; refunds stay in, negative.
    assert "A-10041,A,2026-03-27,8800,UNCLASSIFIED,Reversal of unposted charge,-31.20" in lines
    body = lines[1:]
    keys = [(line.split(",")[2], line.split(",")[1], line.split(",")[0]) for line in body]
    assert keys == sorted(keys)


def test_report_by_account_uses_semicolons_counts_refunds_and_rounds_half_even(records: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    assert "4100;Freight In;6248" in lines  # 6248.50 -> 6248
    assert "5200;Contract Labor;1748" in lines  # 1747.50 -> 1748
    assert "5100;Packaging Materials;3400" in lines  # refunds counted
    assert "8800;UNCLASSIFIED;315" in lines
    assert [line.split(";")[0] for line in lines[1:]] == sorted(line.split(";")[0] for line in lines[1:])

    with_flag = run("report", "--by", "account", "--records", str(records), "--include-refunds")
    assert with_flag.returncode == 0, with_flag.stderr
    assert with_flag.stdout == result.stdout


def test_report_by_month(records: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_reconcile_default_and_explicit_tolerance(records: Path) -> None:
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
        "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
        "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
        "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
        "mismatches=5",
    ]
    loose = run("reconcile", "--records", str(records), "--tolerance", "20")
    assert loose.stdout.splitlines()[-1] == "mismatches=1"


def test_validate_passes_the_samples() -> None:
    result = run("validate", *map(str, EXPORTS))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_rejects_bad_rows_and_unreadable_files(tmp_path: Path) -> None:
    ardent = tmp_path / "a.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-02-30,4100,"Bad, date",10.00,USD\n'
        "A-2,2026-01-05,41X0,ok,abc,USD\n"
        "A-3,2026-01-06,4100,good,1.00,USD\n"
        "A-4,2026-01-06,4100,short\n",
        encoding="utf-8",
    )
    calder = tmp_path / "c.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,2026-01-02,4100,iso date,1.00,USD\n"
        "C-2,31/01/2026,4100,fine,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(calder))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=6 rejected=4"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 4
    assert any("a.csv line 3" in line for line in warnings)
    assert any("a.csv line 6" in line for line in warnings)
    assert any("c.csv line 3" in line for line in warnings)

    missing = run("validate", str(EXPORTS[1]), str(tmp_path / "missing.csv"))
    assert missing.returncode == 2
    assert missing.stdout.splitlines() == ["checked=39 rejected=0"]


def test_config_option_overrides_settings_without_touching_config_dir(tmp_path: Path) -> None:
    before = SETTINGS_FILE.read_bytes()
    override = tmp_path / "override.toml"
    override.write_text('[report]\ndecimals = 2\nunknown_account_label = "HOLD"\n', encoding="utf-8")
    out = tmp_path / "records.csv"

    ingest = run("--config", str(override), "ingest", *map(str, EXPORTS), "--out", str(out))
    assert ingest.returncode == 0, ingest.stderr
    assert ",8800,HOLD," in out.read_text(encoding="utf-8")

    report = run("--config", str(override), "report", "--by", "month", "--records", str(out))
    assert report.stdout.splitlines()[1:] == ["2026-01;13256.48", "2026-02;8456.50", "2026-03;5870.25"]

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    assert SETTINGS_FILE.read_bytes() == before
    assert sorted(p.name for p in SETTINGS_FILE.parent.iterdir()) == ["settings.toml"]
