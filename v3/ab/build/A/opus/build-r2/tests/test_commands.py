"""Tests for ingest, report, reconcile, validate and the global --config option."""

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

from ledgerkit.core.records import RECORD_COLUMNS  # noqa: E402
from ledgerkit.core.totals import round_for_display  # noqa: E402
from ledgerkit.parsers import system_a  # noqa: E402

SAMPLES = REPO / "samples"
ALL_SAMPLES = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]


def run(*args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def records_file(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("ingest") / "records.csv"
    result = run("ingest", *reversed(ALL_SAMPLES), "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


def read_output(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# --- readers -----------------------------------------------------------------


def test_system_a_reads_quoted_memos() -> None:
    rows = system_a.read_rows(SAMPLES / "system_a_export.csv")
    assert len(rows) == 42
    assert rows[0]["memo"] == 'Rebill, "Q1 true-up", carrier'
    assert rows[0]["amount"] == "239.55"


# --- ingest ------------------------------------------------------------------


def test_ingest_writes_every_posting(tmp_path: Path) -> None:
    out = tmp_path / "deep" / "er" / "records.csv"
    result = run("ingest", *ALL_SAMPLES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == ",".join(RECORD_COLUMNS)
    rows = read_output(out)
    assert len(rows) == 120
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5


def test_ingest_converts_each_system(records_file: Path) -> None:
    rows = {row["record_id"]: row for row in read_output(records_file)}
    # A: quoted memo preserved exactly.
    assert rows["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    # B: integer cents become dollars.
    assert rows["B-2201"]["amount"] == "254.40"
    assert rows["B-2201"]["source_system"] == "B"
    # C: dates are day first.
    assert rows["C-0401"]["date"] == "2026-01-02"
    assert rows["C-0438"]["date"] == "2026-02-01"
    # Account names come from the map; unknown codes get the configured label.
    assert rows["C-0423"]["account_name"] == "Contract Labor"
    assert rows["C-0438"]["account_name"] == "UNCLASSIFIED"


def test_ingest_order_is_date_system_id(records_file: Path) -> None:
    rows = read_output(records_file)
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_uses_unknown_label_from_config(tmp_path: Path) -> None:
    override = tmp_path / "label.toml"
    override.write_text('[report]\nunknown_account_label = "TBD"\n', encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("--config", str(override), "ingest", *ALL_SAMPLES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    names = {row["account_name"] for row in read_output(out) if row["account_code"] == "8800"}
    assert names == {"TBD"}


# --- report ------------------------------------------------------------------


def test_report_by_account_semicolons_refunds_counted(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    assert "4100;Freight In;6248" in lines  # 6248.50 rounds half to even
    assert "5100;Packaging Materials;3400" in lines  # includes -365.00 of refunds
    assert "5200;Contract Labor;1748" in lines  # 1747.50 rounds half to even
    assert "8800;UNCLASSIFIED;315" in lines
    codes = [line.split(";")[0] for line in lines[1:]]
    assert codes == sorted(codes)


def test_report_by_month(records_file: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_include_refunds_flag_is_accepted(records_file: Path) -> None:
    plain = run("report", "--by", "month", "--records", str(records_file))
    flagged = run("report", "--by", "month", "--records", str(records_file), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_decimals_from_config(records_file: Path, tmp_path: Path) -> None:
    override = tmp_path / "two.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")
    result = run("--config", str(override), "report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1:] == ["2026-01;13256.48", "2026-02;8456.50", "2026-03;5870.25"]


@pytest.mark.parametrize(
    ("exact", "shown"),
    [("2.50", "2"), ("3.50", "4"), ("1240.50", "1240"), ("883.50", "884"), ("-0.40", "0")],
)
def test_round_for_display_is_half_even(exact: str, shown: str) -> None:
    assert str(round_for_display(Decimal(exact), 0)) == shown


# --- reconcile ---------------------------------------------------------------


def test_reconcile_default_tolerance(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
        "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
        "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
        "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
        "mismatches=5",
    ]


def test_reconcile_tolerance_flag_and_config(records_file: Path, tmp_path: Path) -> None:
    flagged = run("reconcile", "--records", str(records_file), "--tolerance", "20")
    assert flagged.stdout.splitlines() == [
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "mismatches=1",
    ]
    override = tmp_path / "tol.toml"
    override.write_text("[reconcile]\ntolerance = 100\n", encoding="utf-8")
    configured = run("--config", str(override), "reconcile", "--records", str(records_file))
    assert configured.stdout.splitlines() == ["mismatches=0"]


# --- validate ----------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *ALL_SAMPLES)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]
    assert "WARNING" not in result.stderr


def test_validate_reports_every_bad_row(tmp_path: Path) -> None:
    ardent = tmp_path / "a.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        "A-1,2026-01-04,4100,ok,100.00,USD\n"
        "A-2,2026-13-04,4100,bad date,1.00,USD\n"
        "A-3,2026-01-05,41X0,bad code,abc,USD\n"
        'A-4,2026-01-06,4100,"too, many",1.00,USD,extra\n'
        'A-5,2026-01-07,4100,"quoted, fine",2.00,USD\n',
        encoding="utf-8",
    )
    calder = tmp_path / "c.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,day first,1.00,USD\n"
        "C-2,01/13/2026,4100,month first,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(calder))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=7 rejected=4"]
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 4
    assert any("a.csv line 4" in line and "date" in line for line in warnings)
    assert any("a.csv line 5" in line and "account code" in line and "amount" in line for line in warnings)
    assert any("a.csv line 6" in line and "fields" in line for line in warnings)
    assert any("c.csv line 4" in line for line in warnings)


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    result = run("validate", str(tmp_path / "missing.csv"), ALL_SAMPLES[1])
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


def test_validate_pattern_from_config(tmp_path: Path) -> None:
    override = tmp_path / "pattern.toml"
    override.write_text('[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n', encoding="utf-8")
    result = run("--config", str(override), "validate", *ALL_SAMPLES)
    assert result.returncode == 2
    # 8800 and 9000 postings no longer match.
    assert result.stdout.startswith("checked=120 rejected=")
    assert result.stdout.strip() != "checked=120 rejected=0"


# --- --config ----------------------------------------------------------------


def test_config_option_names_the_settings_file(tmp_path: Path) -> None:
    override = tmp_path / "run.toml"
    override.write_text("[report]\ndecimals = 1\n", encoding="utf-8")
    result = run("--config", str(override), "version")
    assert result.returncode == 0, result.stderr
    assert f"settings={override}" in result.stdout.splitlines()


def test_config_option_missing_file_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert "--config" in result.stderr


def test_config_directory_is_untouched(records_file: Path, tmp_path: Path) -> None:
    config_dir = REPO / "config"
    before = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    override = tmp_path / "run.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")
    run("--config", str(override), "report", "--by", "account", "--records", str(records_file))
    run("--config", str(override), "validate", *ALL_SAMPLES)
    after = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    assert after == before
