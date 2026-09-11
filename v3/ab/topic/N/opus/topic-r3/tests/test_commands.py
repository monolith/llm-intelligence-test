"""Tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.report import round_total  # noqa: E402

SAMPLES = REPO / "samples"
SAMPLE_A = SAMPLES / "system_a_export.csv"
SAMPLE_B = SAMPLES / "system_b_export.csv"
SAMPLE_C = SAMPLES / "system_c_export.csv"
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


def run(*args: str | Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *map(str, args)],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture
def records_file(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_A, SAMPLE_B, SAMPLE_C, "--out", out)
    assert result.returncode == 0, result.stderr
    return out


def read_output(path: Path) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row["record_id"]: row for row in csv.DictReader(handle)}


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting_and_creates_parents(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", SAMPLE_C, SAMPLE_A, SAMPLE_B, "--out", out)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121


def test_ingest_converts_each_system(records_file: Path) -> None:
    rows = read_output(records_file)
    # Ardent: quoted memo preserved exactly.
    assert rows["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert rows["A-10001"]["amount"] == "239.55"
    assert rows["A-10019"]["amount"] == "-125.00"
    # Borough: whole cents become dollars.
    assert rows["B-2201"]["amount"] == "254.40"
    assert rows["B-2221"]["amount"] == "-88.25"
    # Calder: day first dates.
    assert rows["C-0401"]["date"] == "2026-01-02"
    assert rows["C-0408"]["date"] == "2026-03-13"
    # Account names come from the map, with the label for unknown codes.
    assert rows["A-10024"]["account_name"] == "Contract Labor"
    assert rows["A-10040"]["account_name"] == "UNCLASSIFIED"
    assert {row["source_system"] for row in rows.values()} == {"A", "B", "C"}


def test_ingest_quotes_descriptions_that_need_it(records_file: Path) -> None:
    text = records_file.read_text(encoding="utf-8")
    assert '"Rebill, ""Q1 true-up"", carrier"' in text


def test_ingest_orders_by_date_system_then_id(records_file: Path) -> None:
    with records_file.open(encoding="utf-8", newline="") as handle:
        keys = [(row["date"], row["source_system"], row["record_id"]) for row in csv.DictReader(handle)]
    assert keys == sorted(keys)
    assert keys[:4] == [
        ("2026-01-02", "C", "C-0401"),
        ("2026-01-02", "C", "C-0423"),
        ("2026-01-03", "A", "A-10001"),
        ("2026-01-03", "A", "A-10019"),
    ]


def test_ingest_fails_cleanly_on_an_unreadable_file(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_A, tmp_path / "missing.csv", "--out", out)
    assert result.returncode != 0
    assert result.stdout == ""
    assert not out.exists()


# --- report -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("exact", "shown"),
    [("2.50", "2"), ("3.50", "4"), ("1240.50", "1240"), ("883.50", "884"), ("-0.40", "0")],
)
def test_round_total_is_half_even(exact: str, shown: str) -> None:
    assert str(round_total(Decimal(exact), 0)) == shown


def test_report_by_account(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", records_file)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;6248",  # 6248.50, half to even
        "4200;Duty and Brokerage;2971",
        "4300;Storage;2886",
        "5100;Packaging Materials;3400",  # refunds counted
        "5200;Contract Labor;1748",
        "5300;Equipment Rental;1621",
        "6100;Utilities;3577",
        "6200;Insurance;4400",
        "8800;UNCLASSIFIED;315",
        "9000;Suspense;417",
    ]


def test_report_by_month(records_file: Path) -> None:
    result = run("report", "--by", "month", "--records", records_file)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_include_refunds_is_accepted_and_changes_nothing(records_file: Path) -> None:
    plain = run("report", "--by", "month", "--records", records_file)
    flagged = run("report", "--by", "month", "--records", records_file, "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


# --- reconcile ----------------------------------------------------------------


def test_reconcile_default_tolerance(records_file: Path) -> None:
    result = run("reconcile", "--records", records_file)
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
    wide = run("reconcile", "--records", records_file, "--tolerance", "20")
    assert wide.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "mismatches=1",
    ]
    exact = run("reconcile", "--records", records_file, "--tolerance", "0")
    assert "MISMATCH 6200 2026-01 spread=0.03 A=1100.00 B=1100.03 C=-" in exact.stdout.splitlines()
    assert exact.stdout.splitlines()[-1] == "mismatches=6"


# --- validate -----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", SAMPLE_A, SAMPLE_B, SAMPLE_C)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_rejects_every_bad_row(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Quoted, fine",100.00,USD\n'
        "A-2,2026-01-05,4100,Too many,fields,1.00,USD\n"
        "A-3,2026-13-05,4100,Bad month,1.00,USD\n"
        "A-4,2026-01-05,4100,Bad amount,one dollar,USD\n"
        "A-5,2026-01-05,41X0,Bad code,1.00,USD\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Cents,25440,USD\n"
        "B,B-2,2026-01-07,4100,Dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,Day first,1.00,USD\n"
        "C-2,01/13/2026,4100,Month first,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", ardent, borough, calder)
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=9 rejected=6"]
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 6
    for name, number in [
        ("ardent.csv", 4),
        ("ardent.csv", 5),
        ("ardent.csv", 6),
        ("ardent.csv", 7),
        ("borough.csv", 3),
        ("calder.csv", 4),
    ]:
        assert any(f"{name} line {number} " in line for line in warnings), (name, number)


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    result = run("validate", SAMPLE_B, tmp_path / "missing.csv")
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config -----------------------------------------------------------------


def snapshot_config() -> dict[str, bytes]:
    return {str(path): path.read_bytes() for path in sorted((REPO / "config").rglob("*")) if path.is_file()}


def test_config_applies_to_every_subcommand(tmp_path: Path, records_file: Path) -> None:
    before = snapshot_config()
    override = tmp_path / "quarter-close.toml"
    override.write_text(
        '[report]\ndecimals = 2\nunknown_account_label = "TBD"\n'
        "[reconcile]\ntolerance = 20\n"
        '[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n',
        encoding="utf-8",
    )

    version = run("--config", override, "version")
    assert f"settings={override}" in version.stdout.splitlines()

    out = tmp_path / "override-records.csv"
    assert run("--config", override, "ingest", SAMPLE_A, "--out", out).returncode == 0
    assert read_output(out)["A-10040"]["account_name"] == "TBD"

    shown = run("--config", override, "report", "--by", "account", "--records", records_file)
    assert "4100;Freight In;6248.50" in shown.stdout.splitlines()
    assert "8800;TBD;314.95" in shown.stdout.splitlines()

    reconciled = run("--config", override, "reconcile", "--records", records_file)
    assert reconciled.stdout.splitlines()[-1] == "mismatches=1"

    checked = run("--config", override, "validate", SAMPLE_B)
    assert checked.returncode == 2
    assert checked.stdout.splitlines() == ["checked=39 rejected=24"]

    assert snapshot_config() == before
    assert not (REPO / "config" / "quarter-close.toml").exists()


def test_config_missing_file_is_an_error(tmp_path: Path) -> None:
    result = run("--config", tmp_path / "nope.toml", "version")
    assert result.returncode == 2
    assert result.stdout == ""
