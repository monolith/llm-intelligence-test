"""Tests for ingest, report, reconcile, validate and the global --config option."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
EXPORTS = [
    str(SAMPLES / "system_c_export.csv"),
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


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


def config_digest() -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").iterdir())
    }


# --- ingest ---------------------------------------------------------------------


def test_ingest_writes_every_posting_in_order(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *EXPORTS, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121
    assert lines[1:4] == [
        "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54",
        "C-0423,C,2026-01-02,5200,Contract Labor,Relief crew dock,101.24",
        'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55',
    ]


def test_ingest_converts_each_system(tmp_path: Path) -> None:
    lines = ingest_samples(tmp_path).read_text(encoding="utf-8").splitlines()
    # Borough writes cents; a Borough refund stays negative.
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    assert "B-2221,B,2026-02-23,5100,Packaging Materials,Credit note damaged corrugate,-88.25" in lines
    # Calder writes dates day first.
    assert "C-0409,C,2026-01-15,4200,Duty and Brokerage,Tariff reclass,151.18" in lines
    # Refunds are kept, and unknown codes get the configured label.
    assert "A-10019,A,2026-01-03,5100,Packaging Materials,Credit note damaged corrugate,-125.00" in lines
    assert "C-0437,C,2026-02-27,8800,UNCLASSIFIED,Unposted supplier charge,104.43" in lines


def test_ingest_rejects_an_unreadable_export_without_writing(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("nonsense\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", str(bad), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert not out.exists()


# --- report ---------------------------------------------------------------------

ACCOUNT_REPORT = [
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


def test_report_by_account_counts_refunds_and_uses_semicolons(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ACCOUNT_REPORT


def test_report_accepts_include_refunds_and_it_changes_nothing(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records), "--include-refunds")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ACCOUNT_REPORT


def test_report_by_month(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    # 2026-02 is exactly 8456.50, which rounds half to even.
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_rounds_half_to_even(tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    records.write_text(
        HEADER + "\n"
        "A-1,A,2026-01-01,1000,X,a,2.50\n"
        "A-2,A,2026-01-01,2000,Y,b,3.50\n"
        "A-3,A,2026-01-01,3000,Z,c,-0.40\n",
        encoding="utf-8",
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1:] == ["1000;X;2", "2000;Y;4", "3000;Z;0"]


# --- reconcile ------------------------------------------------------------------


def test_reconcile_reports_mismatches(tmp_path: Path) -> None:
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


def test_reconcile_tolerance_is_inclusive(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    # 6200 in 2026-01: A=1100.00, B=1100.03, a spread of exactly 0.03.
    at_limit = run("reconcile", "--records", str(records), "--tolerance", "0.03").stdout
    below = run("reconcile", "--records", str(records), "--tolerance", "0.02").stdout
    assert "MISMATCH 6200 2026-01" not in at_limit
    assert "MISMATCH 6200 2026-01 spread=0.03 A=1100.00 B=1100.03 C=-" in below.splitlines()
    wide = run("reconcile", "--records", str(records), "--tolerance", "100")
    assert wide.stdout.splitlines() == ["mismatches=0"]


# --- validate -------------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *EXPORTS)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]
    assert "WARNING" not in result.stderr


def test_validate_rejects_bad_rows_and_keeps_going(tmp_path: Path) -> None:
    bad_a = tmp_path / "bad_a.csv"
    bad_a.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        "A-1,2026-01-03,4100,fine,1.00,USD\n"
        "A-2,2026-13-03,4100,bad date,1.00,USD\n"
        "A-3,2026-01-03,41X0,bad code,1.00,USD\n"
        'A-4,2026-01-03,4100,"quoted, fine",abc,USD\n'
        "A-5,2026-01-03,4100,short\n",
        encoding="utf-8",
    )
    bad_c = tmp_path / "bad_c.csv"
    bad_c.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,01/13/2026,4100,month first,1.00,USD\n"
        "C-2,13/01/2026,4100,day first,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(bad_a), str(bad_c))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=7 rejected=5"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 5
    for line_number in (4, 5, 6, 7):
        assert any(f"bad_a.csv line {line_number}:" in w for w in warnings)
    assert any("bad_c.csv line 3:" in w for w in warnings)


def test_validate_exits_2_for_an_unreadable_file(tmp_path: Path) -> None:
    result = run("validate", str(tmp_path / "missing.csv"), str(SAMPLES / "system_b_export.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config -------------------------------------------------------------------


def test_config_option_changes_settings_for_one_run(tmp_path: Path) -> None:
    before = config_digest()
    override = tmp_path / "override.toml"
    override.write_text('[report]\ndecimals = 2\nunknown_account_label = "TBD"\n', encoding="utf-8")

    version = run("--config", str(override), "version")
    assert version.returncode == 0, version.stderr
    assert f"settings={override}" in version.stdout.splitlines()

    out = tmp_path / "records.csv"
    ingest = run("--config", str(override), "ingest", *EXPORTS, "--out", str(out))
    assert ingest.returncode == 0, ingest.stderr
    assert "C-0437,C,2026-02-27,8800,TBD,Unposted supplier charge,104.43" in out.read_text(encoding="utf-8")

    report = run("--config", str(override), "report", "--by", "account", "--records", str(out))
    assert report.returncode == 0, report.stderr
    assert "4100;Freight In;6248.50" in report.stdout.splitlines()

    # The next run without --config is back on the checked in settings.
    plain = run("report", "--by", "account", "--records", str(out))
    assert "4100;Freight In;6248" in plain.stdout.splitlines()
    assert config_digest() == before


def test_config_option_sets_reconcile_tolerance(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    override = tmp_path / "override.toml"
    override.write_text("[reconcile]\ntolerance = 20\n", encoding="utf-8")
    result = run("--config", str(override), "reconcile", "--records", str(records))
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "mismatches=1",
    ]


def test_config_option_rejects_a_missing_file(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "missing.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
