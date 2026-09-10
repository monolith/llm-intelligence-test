"""End to end tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.cli import main  # noqa: E402
from ledgerkit.config import CONFIG_ENV_VAR  # noqa: E402

SAMPLES = REPO / "samples"
SAMPLE_A = str(SAMPLES / "system_a_export.csv")
SAMPLE_B = str(SAMPLES / "system_b_export.csv")
SAMPLE_C = str(SAMPLES / "system_c_export.csv")
ALL_SAMPLES = (SAMPLE_A, SAMPLE_B, SAMPLE_C)

HEADER = "record_id,source_system,date,account_code,account_name,description,amount"

EXPECTED_MISMATCHES = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop(CONFIG_ENV_VAR, None)
    env.pop("LEDGERKIT_LOG_LEVEL", None)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "override.toml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def records_file(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *ALL_SAMPLES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


# --- ingest ---------------------------------------------------------------------


def test_ingest_writes_every_posting_and_creates_parents(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "deeper" / "records.csv"
    result = run("ingest", SAMPLE_C, SAMPLE_A, SAMPLE_B, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121


def test_ingest_converts_each_system(records_file: Path) -> None:
    lines = set(records_file.read_text(encoding="utf-8").splitlines())
    # Ardent: quoted memo preserved exactly, quoted again on the way out.
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines
    assert 'A-10002,A,2026-01-05,4100,Freight In,"Drayage, port apron to DC",283.82' in lines
    # Borough: whole cents become dollars, refunds stay negative.
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    assert "B-2221,B,2026-02-23,5100,Packaging Materials,Credit note damaged corrugate,-88.25" in lines
    # Calder: day first dates.
    assert "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54" in lines
    assert "C-0408,C,2026-03-13,4100,Freight In,Fuel surcharge inbound,80.94" in lines
    # Account names: the FY-2 name for 5200, the unknown label for 8800.
    assert "A-10024,A,2026-01-05,5200,Contract Labor,Night shift crew,144.11" in lines
    assert "A-10040,A,2026-03-25,8800,UNCLASSIFIED,Held for review,127.75" in lines
    # Refunds are not filtered out.
    assert "A-10019,A,2026-01-03,5100,Packaging Materials,Credit note damaged corrugate,-125.00" in lines


def test_ingest_orders_by_date_then_system_then_id(records_file: Path) -> None:
    with records_file.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)
    assert [row["record_id"] for row in rows[:4]] == ["C-0401", "C-0423", "A-10001", "A-10019"]


def test_ingest_does_not_deduplicate(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_A, SAMPLE_A, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=84 to {out}\n"


def test_ingest_writes_nothing_when_an_export_cannot_be_read(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_A, str(tmp_path / "missing.csv"), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert not out.exists()


# --- report ---------------------------------------------------------------------

EXPECTED_BY_ACCOUNT = [
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

EXPECTED_BY_MONTH = ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_by_account_counts_refunds_and_rounds_half_even(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == EXPECTED_BY_ACCOUNT


def test_report_by_month(records_file: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == EXPECTED_BY_MONTH


def test_report_accepts_include_refunds_and_prints_the_same(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records_file), "--include-refunds")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == EXPECTED_BY_ACCOUNT


def test_report_requires_by(records_file: Path) -> None:
    result = run("report", "--records", str(records_file))
    assert result.returncode == 2


# --- reconcile ------------------------------------------------------------------


def test_reconcile_default_tolerance(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [*EXPECTED_MISMATCHES, "mismatches=5"]


def test_reconcile_tolerance_flag(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file), "--tolerance", "20")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [EXPECTED_MISMATCHES[0], "mismatches=1"]


def test_reconcile_spread_equal_to_tolerance_agrees(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file), "--tolerance", "57.75")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_rejects_a_tolerance_that_is_not_a_number(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file), "--tolerance", "abc")
    assert result.returncode == 2


# --- validate -------------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *ALL_SAMPLES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert "WARNING" not in result.stderr


def test_validate_rejects_bad_rows_and_checks_them_all(tmp_path: Path) -> None:
    ardent = tmp_path / "a.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Quoted, fine",10.00,USD\n'
        "A-2,2026-01-03,4100,Too many,fields,10.00,USD\n"
        "A-3,2026-02-30,4100,Bad date,10.00,USD\n"
        "A-4,2026-01-03,4100,Bad amount,ten,USD\n"
        "A-5,2026-01-03,41X0,Bad account,10.00,USD\n"
        "A-6,2026-01-03,4100,Fine,-3.50,USD\n",
        encoding="utf-8",
    )
    borough = tmp_path / "b.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Dollars not cents,254.40,USD\n"
        "B,B-2,2026-01-07,4100,Fine,25440,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "c.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,01/13/2026,4100,Month first,10.00,USD\n"
        "C-2,13/01/2026,4100,Day first,10.00,USD\n"
        "C-3,13/01/2026,ABCD,Two problems,x,USD\n"
        "== 3 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout == "checked=11 rejected=7\n"

    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 7
    for file, line in [(ardent, 4), (ardent, 5), (ardent, 6), (ardent, 7), (borough, 2), (calder, 3), (calder, 5)]:
        assert any(f"{file} line {line} " in warning for warning in warnings), (file, line)
    two_problems = next(warning for warning in warnings if f"{calder} line 5 " in warning)
    assert "gross_amount" in two_problems and "ABCD" in two_problems


def test_validate_file_that_cannot_be_read_exits_2(tmp_path: Path) -> None:
    stranger = tmp_path / "unknown.csv"
    stranger.write_text("what,is,this\n1,2,3\n", encoding="utf-8")
    result = run("validate", SAMPLE_A, str(tmp_path / "missing.csv"), str(stranger))
    assert result.returncode == 2
    assert result.stdout == "checked=42 rejected=0\n"


# --- --config -------------------------------------------------------------------


def test_config_changes_report_decimals(tmp_path: Path, records_file: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "month;total",
        "2026-01;13256.48",
        "2026-02;8456.50",
        "2026-03;5870.25",
    ]


def test_config_changes_reconcile_tolerance(tmp_path: Path, records_file: Path) -> None:
    config = write_config(tmp_path, "[reconcile]\ntolerance = 16.5\n")
    result = run("--config", str(config), "reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [*EXPECTED_MISMATCHES[:2], "mismatches=2"]


def test_config_changes_unknown_account_label(tmp_path: Path) -> None:
    config = write_config(tmp_path, '[report]\nunknown_account_label = "NOT MAPPED"\n')
    out = tmp_path / "records.csv"
    result = run("--config", str(config), "ingest", SAMPLE_A, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert "A-10040,A,2026-03-25,8800,NOT MAPPED,Held for review,127.75" in out.read_text(
        encoding="utf-8"
    ).splitlines()


def test_config_changes_validate_pattern(tmp_path: Path) -> None:
    config = write_config(tmp_path, '[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n')
    result = run("--config", str(config), "validate", *ALL_SAMPLES)
    assert result.returncode == 2
    assert result.stdout == "checked=120 rejected=7\n"


def test_config_shows_in_version(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 1\n")
    result = run("--config", str(config), "version")
    assert result.returncode == 0, result.stderr
    assert f"settings={config}" in result.stdout.splitlines()


def test_config_that_does_not_exist_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""


def test_config_leaves_the_environment_as_it_found_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(CONFIG_ENV_VAR, raising=False)
    config = write_config(tmp_path, "[report]\ndecimals = 1\n")
    assert main(["--config", str(config), "version"]) == 0
    assert f"settings={config}" in capsys.readouterr().out.splitlines()
    assert CONFIG_ENV_VAR not in os.environ


def test_nothing_under_config_is_touched(tmp_path: Path, records_file: Path) -> None:
    config_dir = REPO / "config"
    before = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    override = write_config(tmp_path, "[report]\ndecimals = 2\n")
    for args in (
        ("ingest", SAMPLE_A, "--out", str(tmp_path / "again.csv")),
        ("report", "--by", "account", "--records", str(records_file)),
        ("reconcile", "--records", str(records_file)),
        ("validate", *ALL_SAMPLES),
    ):
        run(*args)
        run("--config", str(override), *args)
    after = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    assert after == before
