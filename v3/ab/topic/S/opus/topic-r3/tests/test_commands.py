"""End to end tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]
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


def config_snapshot() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").rglob("*"))
        if path.is_file()
    }


CONFIG_BEFORE = config_snapshot()


@pytest.fixture
def records(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


# --- ingest -----------------------------------------------------------------


def test_ingest_writes_every_posting_in_order(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121
    assert lines[1].startswith("C-0401,C,2026-01-02,")
    assert lines[2].startswith("C-0423,C,2026-01-02,")
    assert lines[3].startswith("A-10001,A,2026-01-03,")


def test_ingest_converts_each_system_and_keeps_text_exactly(records: Path) -> None:
    lines = set(records.read_text(encoding="utf-8").splitlines())
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    assert "B-2221,B,2026-02-23,5100,Packaging Materials,Credit note damaged corrugate,-88.25" in lines
    assert "C-0405,C,2026-03-04,4100,Freight In,Inbound freight consolidation,177.65" in lines
    assert "A-10040,A,2026-03-25,8800,UNCLASSIFIED,Held for review,127.75" in lines
    assert "A-10024,A,2026-01-05,5200,Contract Labor,Night shift crew,144.11" in lines


def test_ingest_output_does_not_depend_on_file_order(tmp_path: Path, records: Path) -> None:
    other = tmp_path / "reversed.csv"
    result = run("ingest", *reversed(SAMPLE_FILES), "--out", str(other))
    assert result.returncode == 0, result.stderr
    assert other.read_bytes() == records.read_bytes()


def test_ingest_keeps_duplicates(tmp_path: Path) -> None:
    out = tmp_path / "twice.csv"
    result = run("ingest", SAMPLE_FILES[1], SAMPLE_FILES[1], "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=78 to {out}\n"


def test_ingest_stops_on_an_unreadable_file_without_writing(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("sys,doc_no,value_date,acct,descr,amount,cur\nB,B-1,2026-01-07,4100,x,1.5,USD\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_FILES[0], str(bad), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert "bad.csv" in result.stderr
    assert not out.exists()


# --- report -----------------------------------------------------------------

BY_ACCOUNT = [
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

BY_MONTH = ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_by_account_counts_refunds_and_rounds_half_even(records: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == BY_ACCOUNT


def test_report_by_month(records: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == BY_MONTH


def test_report_accepts_include_refunds_and_changes_nothing(records: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records), "--include-refunds")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == BY_MONTH


def test_report_requires_by(records: Path) -> None:
    result = run("report", "--records", str(records))
    assert result.returncode == 2


def test_report_on_a_missing_file_fails(tmp_path: Path) -> None:
    result = run("report", "--by", "month", "--records", str(tmp_path / "nope.csv"))
    assert result.returncode != 0
    assert result.stdout == ""


# --- reconcile --------------------------------------------------------------

MISMATCHES = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
]


def test_reconcile_reports_mismatches_with_the_setting_tolerance(records: Path) -> None:
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == MISMATCHES + ["mismatches=5"]


def test_reconcile_tolerance_flag(records: Path) -> None:
    tight = run("reconcile", "--records", str(records), "--tolerance", "0.02")
    assert tight.returncode == 0, tight.stderr
    assert "MISMATCH 6200 2026-01 spread=0.03 A=1100.00 B=1100.03 C=-" in tight.stdout.splitlines()
    assert tight.stdout.splitlines()[-1] == "mismatches=6"

    loose = run("reconcile", "--records", str(records), "--tolerance", "100")
    assert loose.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_rejects_a_bad_tolerance(records: Path) -> None:
    assert run("reconcile", "--records", str(records), "--tolerance", "abc").returncode == 2
    assert run("reconcile", "--records", str(records), "--tolerance", "-1").returncode == 2


# --- validate ---------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert result.stderr == ""


def test_validate_rejects_each_kind_of_bad_row(tmp_path: Path) -> None:
    export = tmp_path / "calder.csv"
    export.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,02/01/2026,4100,fine,10.00,USD\n"
        "C-2,02/01/2026,4100,one field short,10.00\n"
        "C-3,2026-01-02,4100,iso date,10.00,USD\n"
        "C-4,02/01/2026,4100,bad amount,ten,USD\n"
        "C-5,02/01/2026,41X0,bad code,10.00,USD\n"
        "== 5 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout == "checked=5 rejected=4\n"
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 4
    for number, words in ((4, "fields"), (5, "date"), (6, "amount"), (7, "account code")):
        assert any(f"calder.csv line {number}:" in w and words in w for w in warnings), warnings


def test_validate_reads_quoted_ardent_memos_and_borough_cents(tmp_path: Path) -> None:
    export = tmp_path / "borough.csv"
    export.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,fine,25440,USD\n"
        "B,B-2,2026-01-07,4100,dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    result = run("validate", SAMPLE_FILES[0], str(export))
    assert result.returncode == 2
    assert result.stdout == "checked=44 rejected=1\n"
    assert "borough.csv line 3:" in result.stderr


def test_validate_exits_2_on_an_unreadable_file(tmp_path: Path) -> None:
    result = run("validate", SAMPLE_FILES[1], str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout == "checked=39 rejected=0\n"
    assert "missing.csv" in result.stderr


# --- --config ---------------------------------------------------------------


def test_config_option_changes_the_settings_for_one_run(tmp_path: Path, records: Path) -> None:
    override = tmp_path / "quarter-close.toml"
    override.write_text('[report]\ndecimals = 2\nunknown_account_label = "TBD"\n', encoding="utf-8")

    version = run("--config", str(override), "version")
    assert version.returncode == 0, version.stderr
    assert f"settings={override}" in version.stdout.splitlines()

    report = run("--config", str(override), "report", "--by", "account", "--records", str(records))
    assert report.returncode == 0, report.stderr
    assert "4100;Freight In;6248.50" in report.stdout.splitlines()

    out = tmp_path / "tbd.csv"
    ingest = run("--config", str(override), "ingest", SAMPLE_FILES[0], "--out", str(out))
    assert ingest.returncode == 0, ingest.stderr
    assert "A-10040,A,2026-03-25,8800,TBD,Held for review,127.75" in out.read_text(encoding="utf-8").splitlines()


def test_config_option_reaches_reconcile_and_validate(tmp_path: Path, records: Path) -> None:
    override = tmp_path / "strict.toml"
    override.write_text('[reconcile]\ntolerance = 20\n[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n', encoding="utf-8")

    reconcile = run("--config", str(override), "reconcile", "--records", str(records))
    assert reconcile.stdout.splitlines() == [MISMATCHES[0], "mismatches=1"]

    validate = run("--config", str(override), "validate", SAMPLE_FILES[1])
    assert validate.returncode == 2
    assert validate.stdout == "checked=39 rejected=24\n"


def test_config_option_with_a_missing_file_fails() -> None:
    result = run("--config", "/nonexistent/ledgerkit.toml", "version")
    assert result.returncode == 2
    assert result.stdout == ""


def test_nothing_under_config_changed() -> None:
    assert config_snapshot() == CONFIG_BEFORE
