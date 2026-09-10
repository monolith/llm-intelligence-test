"""Tests for ingest, report, reconcile, validate and --config, run against the samples."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.core.totals import round_total  # noqa: E402

SAMPLES = REPO / "samples"
EXPORTS = [str(SAMPLES / f"system_{letter}_export.csv") for letter in "abc"]


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
    result = run("ingest", *EXPORTS, "--out", str(out))
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


def test_ingest_writes_every_posting_normalized(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", EXPORTS[2], EXPORTS[0], EXPORTS[1], "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    body = lines[1:]
    assert len(body) == 120
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in body
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in body
    assert "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54" in body
    assert "C-0438,C,2026-02-01,8800,UNCLASSIFIED,Awaiting reclass,113.97" in body
    assert any(",5200,Contract Labor," in line for line in body)
    assert sum(1 for line in body if line.rsplit(",", 1)[1].startswith("-")) == 5


def test_ingest_orders_by_date_then_system_then_id(tmp_path: Path) -> None:
    import csv

    out = ingest_samples(tmp_path)
    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_fails_on_an_unreadable_export(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.csv"
    bogus.write_text("not,an,export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", EXPORTS[0], str(bogus), "--out", str(out))
    assert result.returncode != 0
    assert not out.exists()


# --- report -------------------------------------------------------------------


def test_report_by_account_uses_semicolons_and_counts_refunds(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records))
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


def test_report_by_month(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_include_refunds_is_accepted_and_changes_nothing(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    plain = run("report", "--by", "month", "--records", str(records))
    flagged = run("report", "--by", "month", "--records", str(records), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_missing_records_file_fails(tmp_path: Path) -> None:
    result = run("report", "--by", "account", "--records", str(tmp_path / "absent.csv"))
    assert result.returncode != 0


def test_round_total_is_half_to_even() -> None:
    assert round_total(Decimal("2.50"), 0) == Decimal("2")
    assert round_total(Decimal("3.50"), 0) == Decimal("4")
    assert round_total(Decimal("1240.50"), 0) == Decimal("1240")
    assert round_total(Decimal("883.50"), 0) == Decimal("884")
    assert str(round_total(Decimal("-0.40"), 0)) == "0"


# --- reconcile ----------------------------------------------------------------


def test_reconcile_reports_the_sample_mismatches(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
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


def test_reconcile_tolerance_flag_overrides_the_setting(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records), "--tolerance", "0.02")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[-1] == "mismatches=6"
    assert any(line.startswith("MISMATCH 6200 2026-01 spread=0.03 ") for line in lines)


# --- validate -----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *EXPORTS)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_rejects_bad_rows_and_keeps_going(tmp_path: Path) -> None:
    export = tmp_path / "calder.csv"
    export.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,02/01/2026,4100,Fine row,10.00,USD\n"
        "C-2,01/13/2026,4100,Month first date,10.00,USD\n"
        "C-3,02/01/2026,41X0,Bad code,ten,USD\n"
        "C-4,02/01/2026,4100,Too,many,10.00,USD\n"
        "== 4 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=4 rejected=3"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 3
    assert all("calder.csv" in line for line in warnings)
    assert "line 4 " in warnings[0]
    assert "line 5 " in warnings[1] and "41X0" in warnings[1] and "'ten'" in warnings[1]
    assert "line 6 " in warnings[2] and "fields" in warnings[2]


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    result = run("validate", EXPORTS[1], str(tmp_path / "absent.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config -----------------------------------------------------------------


def test_config_option_changes_settings_for_one_run(tmp_path: Path) -> None:
    before = config_digest()
    records = ingest_samples(tmp_path)
    override = tmp_path / "two-places.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")

    result = run("--config", str(override), "report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert "4100;Freight In;6248.50" in result.stdout.splitlines()

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    tight = tmp_path / "tight.toml"
    tight.write_text("[reconcile]\ntolerance = 0.02\n", encoding="utf-8")
    reconcile = run("--config", str(tight), "reconcile", "--records", str(records))
    assert reconcile.stdout.splitlines()[-1] == "mismatches=6"

    strict = tmp_path / "strict.toml"
    strict.write_text('[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n', encoding="utf-8")
    validate = run("--config", str(strict), "validate", EXPORTS[1])
    assert validate.returncode == 2

    assert config_digest() == before


def test_config_option_with_missing_file_fails(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "absent.toml"), "version")
    assert result.returncode == 2
