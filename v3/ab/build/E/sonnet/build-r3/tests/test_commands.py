"""Tests for the five commands SPEC.md adds: ingest, report, reconcile, validate
and the global ``--config`` flag.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
ALL_SAMPLES = [
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
    str(SAMPLES / "system_c_export.csv"),
]


def run(*args: str, cwd: Path, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ingest_merges_all_three_systems_and_keeps_refunds(tmp_path: Path) -> None:
    result = run("ingest", *ALL_SAMPLES, "--out", "records.csv", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "wrote=120 to records.csv"

    lines = (tmp_path / "records.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    assert len(lines) == 121

    # A-10001 has a quoted, comma-containing memo; A-10019 is a refund and must
    # survive ingest (ingest keeps every posting, unlike normalize()'s default).
    assert any(line.startswith("A-10001,") and '"Rebill, ""Q1 true-up"", carrier"' in line for line in lines)
    assert any(line.startswith("A-10019,") and line.endswith(",-125.00") for line in lines)


def test_ingest_creates_missing_parent_directories(tmp_path: Path) -> None:
    result = run("ingest", *ALL_SAMPLES, "--out", "nested/dir/records.csv", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "nested" / "dir" / "records.csv").is_file()


def test_report_by_account_uses_semicolons_and_includes_refunds_by_default(tmp_path: Path) -> None:
    ingest = run("ingest", *ALL_SAMPLES, "--out", "records.csv", cwd=tmp_path)
    assert ingest.returncode == 0, ingest.stderr

    result = run("report", "--by", "account", "--records", "records.csv", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    assert "," not in lines[0]
    # 5100 (Packaging Materials) includes the -125.00 refund from A-10019.
    packaging = next(line for line in lines if line.startswith("5100;"))
    assert packaging == "5100;Packaging Materials;3400"


def test_report_by_month_ascending(tmp_path: Path) -> None:
    ingest = run("ingest", *ALL_SAMPLES, "--out", "records.csv", cwd=tmp_path)
    assert ingest.returncode == 0, ingest.stderr

    result = run("report", "--by", "month", "--records", "records.csv", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "month;total"
    months = [line.split(";")[0] for line in lines[1:]]
    assert months == sorted(months)
    assert months[0] == "2026-01"


def test_reconcile_reports_the_spec_example_mismatch(tmp_path: Path) -> None:
    ingest = run("ingest", *ALL_SAMPLES, "--out", "records.csv", cwd=tmp_path)
    assert ingest.returncode == 0, ingest.stderr

    result = run("reconcile", "--records", "records.csv", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-" in lines
    assert lines[-1].startswith("mismatches=")
    count = int(lines[-1].split("=")[1])
    assert count == len(lines) - 1


def test_validate_rejects_bad_rows_and_does_not_stop_at_the_first(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad_a.csv"
    bad_file.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        "A-1,2026-01-03,4100,Fine row,100.00,USD\n"
        "A-2,2026-13-40,4100,Bad date,50.00,USD\n"
        "A-3,2026-01-05,42AB,Bad account,25.00,USD\n"
        "A-4,2026-01-06,4100,Bad amount,notanumber,USD\n"
        "A-5,2026-01-07,4100,Too few fields\n",
        encoding="utf-8",
    )
    result = run("validate", str(bad_file), cwd=tmp_path)
    assert result.returncode == 2
    assert result.stdout.strip() == "checked=5 rejected=4"
    assert result.stderr.count("WARNING") == 4


def test_validate_passes_clean_samples(tmp_path: Path) -> None:
    result = run("validate", *ALL_SAMPLES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "checked=120 rejected=0"


def test_config_flag_changes_settings_for_one_run(tmp_path: Path) -> None:
    ingest = run("ingest", *ALL_SAMPLES, "--out", "records.csv", cwd=tmp_path)
    assert ingest.returncode == 0, ingest.stderr

    custom = tmp_path / "custom.toml"
    custom.write_text("[report]\ndecimals = 2\n", encoding="utf-8")

    result = run("--config", str(custom), "report", "--by", "account", "--records", "records.csv", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    packaging = next(line for line in result.stdout.splitlines() if line.startswith("5100;"))
    assert packaging == "5100;Packaging Materials;3400.00"

    version = run("--config", str(custom), "version", cwd=tmp_path)
    assert version.stdout.splitlines()[1] == f"settings={custom}"
