"""Tests for ingest, report, reconcile, validate and --config."""

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

from ledgerkit.reports import round_for_display  # noqa: E402

SAMPLES = REPO / "samples"
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


def run(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def ingest_samples(tmp_path: Path) -> Path:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    return out


def write_records(path: Path, rows: list[str]) -> Path:
    path.write_text(HEADER + "\n" + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


# --- ingest -------------------------------------------------------------------


def test_ingest_keeps_every_posting_in_order(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121
    keys = [(line.split(",")[2], line.split(",")[1], line.split(",")[0]) for line in lines[1:]]
    assert keys == sorted(keys)


def test_ingest_preserves_quoted_memo_exactly(tmp_path: Path) -> None:
    lines = ingest_samples(tmp_path).read_text(encoding="utf-8").splitlines()
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines


def test_ingest_converts_units_dates_and_names(tmp_path: Path) -> None:
    lines = ingest_samples(tmp_path).read_text(encoding="utf-8").splitlines()
    # Borough writes cents.
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    # Calder writes dates day first.
    assert "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54" in lines
    # 5200 is Contract Labor; 8800 is unmapped.
    assert all(",5200,Contract Labor," in line for line in lines if line.split(",")[3] == "5200")
    assert any(",8800,UNCLASSIFIED," in line for line in lines)


def test_ingest_keeps_refunds(tmp_path: Path) -> None:
    lines = ingest_samples(tmp_path).read_text(encoding="utf-8").splitlines()[1:]
    assert any(line.rsplit(",", 1)[1].startswith("-") for line in lines)


def test_ingest_default_out_path(tmp_path: Path) -> None:
    result = run("ingest", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "out" / "records.csv").is_file()


# --- report -------------------------------------------------------------------


def test_round_half_to_even_table() -> None:
    for exact, shown in (("2.50", "2"), ("3.50", "4"), ("1240.50", "1240"), ("883.50", "884")):
        assert str(round_for_display(Decimal(exact), 0)) == shown
    assert str(round_for_display(Decimal("-0.4"), 0)) == "0"


def test_report_by_account_uses_semicolons_and_counts_refunds(tmp_path: Path) -> None:
    records = write_records(
        tmp_path / "r.csv",
        [
            "X1,A,2026-01-03,4100,Freight In,a,2.00",
            "X2,B,2026-01-04,4100,Freight In,b,0.50",
            "X3,C,2026-02-04,5200,Contract Labor,c,5.00",
            "X4,A,2026-02-05,5200,Contract Labor,d,-1.50",
        ],
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;2",
        "5200;Contract Labor;4",
    ]


def test_report_by_month_and_include_refunds_flag_is_accepted(tmp_path: Path) -> None:
    records = write_records(
        tmp_path / "r.csv",
        [
            "X1,A,2026-02-03,4100,Freight In,a,883.00",
            "X2,B,2026-02-04,4100,Freight In,b,0.50",
            "X3,C,2026-01-04,5200,Contract Labor,c,5.00",
            "X4,A,2026-01-05,5200,Contract Labor,d,-2.50",
        ],
    )
    plain = run("report", "--by", "month", "--records", str(records))
    flagged = run("report", "--by", "month", "--records", str(records), "--include-refunds")
    assert plain.returncode == 0, plain.stderr
    assert plain.stdout.splitlines() == ["month;total","2026-01;2", "2026-02;884"]
    assert flagged.stdout == plain.stdout


def test_report_on_samples(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    assert "5200;Contract Labor;1748" in lines
    assert "8800;UNCLASSIFIED;315" in lines


# --- reconcile ----------------------------------------------------------------


def test_reconcile_on_samples(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-"
    assert lines[-1] == "mismatches=5"


def test_reconcile_tolerance_and_single_system_combinations(tmp_path: Path) -> None:
    records = write_records(
        tmp_path / "r.csv",
        [
            "X1,A,2026-01-03,4100,Freight In,a,10.00",
            "X2,B,2026-01-04,4100,Freight In,b,10.05",
            "X3,A,2026-01-05,4200,Duty and Brokerage,c,10.00",
            "X4,C,2026-01-06,4200,Duty and Brokerage,d,11.00",
            "X5,C,2026-01-07,4200,Duty and Brokerage,e,-1.00",
            "X6,A,2026-01-08,4300,Storage,f,99.00",
        ],
    )
    default = run("reconcile", "--records", str(records))
    assert default.stdout.splitlines() == ["mismatches=0"]
    tight = run("reconcile", "--records", str(records), "--tolerance", "0.01")
    assert tight.stdout.splitlines() == [
        "MISMATCH 4100 2026-01 spread=0.05 A=10.00 B=10.05 C=-",
        "mismatches=1",
    ]


# --- validate -----------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_reports_every_bad_row_with_line_numbers(tmp_path: Path) -> None:
    ardent = tmp_path / "a.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Quoted, with comma",100.00,USD\n'
        "A-2,2026-13-04,4100,bad date,100.00,USD\n"
        "A-3,2026-01-04,41X0,bad code,ten,USD\n"
        "A-4,2026-01-04,4100,too,many,1.00,USD\n",
        encoding="utf-8",
    )
    borough = tmp_path / "b.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,fine,25440,USD\n"
        "B,B-2,2026-01-07,4100,dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "c.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,day first is fine,1.00,USD\n"
        "C-2,01/13/2026,4100,month first is not,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=8 rejected=5"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 5
    assert any(f"{ardent} line 4 " in w and "date" in w for w in warnings)
    assert any(f"{ardent} line 5 " in w and "amount" in w and "account code" in w for w in warnings)
    assert any(f"{ardent} line 6 " in w and "fields" in w for w in warnings)
    assert any(f"{borough} line 3 " in w for w in warnings)
    assert any(f"{calder} line 4 " in w for w in warnings)


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    result = run("validate", str(tmp_path / "missing.csv"), SAMPLE_FILES[1])
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config -----------------------------------------------------------------


def _config_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted((REPO / "config").rglob("*")):
        digest.update(str(path).encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


def test_config_option_changes_settings_for_one_run(tmp_path: Path) -> None:
    before = _config_digest()
    override = tmp_path / "override.toml"
    override.write_text(
        '[report]\ndecimals = 2\nunknown_account_label = "NOT MAPPED"\n'
        "[reconcile]\ntolerance = 100\n"
        '[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n',
        encoding="utf-8",
    )
    cfg = ("--config", str(override))

    version = run(*cfg, "version")
    assert f"settings={override}" in version.stdout.splitlines()

    out = tmp_path / "records.csv"
    assert run(*cfg, "ingest", *SAMPLE_FILES, "--out", str(out)).returncode == 0
    assert ",8800,NOT MAPPED," in out.read_text(encoding="utf-8")

    report = run(*cfg, "report", "--by", "month", "--records", str(out))
    assert all(len(line.split(";")[1].split(".")[1]) == 2 for line in report.stdout.splitlines()[1:])

    assert run(*cfg, "reconcile", "--records", str(out)).stdout.splitlines() == ["mismatches=0"]

    validate = run(*cfg, "validate", SAMPLE_FILES[1])
    assert validate.returncode == 2

    assert _config_digest() == before


def test_config_is_restored_after_main(tmp_path: Path) -> None:
    from ledgerkit.cli import main
    from ledgerkit.config import CONFIG_ENV_VAR

    override = tmp_path / "o.toml"
    override.write_text("[report]\ndecimals = 1\n", encoding="utf-8")
    saved = os.environ.pop(CONFIG_ENV_VAR, None)
    try:
        assert main(["--config", str(override), "version"]) == 0
        assert CONFIG_ENV_VAR not in os.environ
    finally:
        if saved is not None:
            os.environ[CONFIG_ENV_VAR] = saved
