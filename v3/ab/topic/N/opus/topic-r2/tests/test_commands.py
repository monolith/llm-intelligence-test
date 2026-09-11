"""End to end tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit import cli  # noqa: E402
from ledgerkit.config import CONFIG_ENV_VAR  # noqa: E402

SAMPLES = REPO / "samples"
EXPORTS = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop(CONFIG_ENV_VAR, None)
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
    out = tmp_path_factory.mktemp("ingest") / "nested" / "records.csv"
    result = run("ingest", *EXPORTS, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    return out


def write_records(path: Path, rows: list[tuple[str, str, str, str, str]]) -> Path:
    """Write a small normalized file from (id, system, date, account, amount) tuples."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["record_id", "source_system", "date", "account_code", "account_name", "description", "amount"])
        for record_id, system, day, code, amount in rows:
            writer.writerow([record_id, system, day, code, "Name", "memo", amount])
    return path


# --- ingest ------------------------------------------------------------------


def test_ingest_keeps_every_posting_including_refunds(records_file: Path) -> None:
    with records_file.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 120
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5
    assert {row["source_system"] for row in rows} == {"A", "B", "C"}


def test_ingest_header_order_and_conversions(records_file: Path) -> None:
    lines = records_file.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    with records_file.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    by_id = {row["record_id"]: row for row in rows}

    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert by_id["B-2201"]["amount"] == "254.40"
    assert by_id["B-2201"]["date"] == "2026-01-07"
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["A-10041"]["account_name"] == "UNCLASSIFIED"
    assert {row["account_name"] for row in rows if row["account_code"] == "5200"} == {"Contract Labor"}

    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_unreadable_file_writes_nothing(tmp_path: Path) -> None:
    junk = tmp_path / "junk.csv"
    junk.write_text("not an export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", str(junk), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert not out.exists()


# --- report ------------------------------------------------------------------


def test_report_by_account(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records_file))
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


def test_report_by_month_rounds_half_to_even(records_file: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_include_refunds_is_accepted_and_changes_nothing(records_file: Path) -> None:
    without = run("report", "--by", "account", "--records", str(records_file))
    with_flag = run("report", "--by", "account", "--records", str(records_file), "--include-refunds")
    assert with_flag.returncode == 0, with_flag.stderr
    assert with_flag.stdout == without.stdout


def test_report_half_even_table_from_conventions(tmp_path: Path) -> None:
    records = write_records(
        tmp_path / "records.csv",
        [
            ("X1", "A", "2026-01-05", "4100", "2.50"),
            ("X2", "A", "2026-01-05", "4200", "3.50"),
            ("X3", "A", "2026-01-05", "4300", "1240.50"),
            ("X4", "A", "2026-01-05", "5100", "883.25"),
            ("X5", "B", "2026-01-06", "5100", "0.25"),
        ],
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    totals = [line.split(";")[2] for line in result.stdout.splitlines()[1:]]
    assert totals == ["2", "4", "1240", "884"]


# --- reconcile ---------------------------------------------------------------


def test_reconcile_samples(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-"
    assert lines[-1] == "mismatches=5"
    assert len(lines) == 6


def test_reconcile_tolerance_flag(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file), "--tolerance", "16")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[-1] == "mismatches=3"


def test_reconcile_only_compares_combinations_two_systems_posted_to(tmp_path: Path) -> None:
    records = write_records(
        tmp_path / "records.csv",
        [
            ("X1", "A", "2026-01-05", "4100", "100.00"),
            ("X2", "B", "2026-01-05", "4100", "100.05"),
            ("X3", "A", "2026-02-05", "4100", "500.00"),
            ("X4", "C", "2026-01-05", "4200", "10.00"),
            ("X5", "A", "2026-01-05", "4200", "20.00"),
            ("X6", "A", "2026-01-06", "4200", "-10.00"),
        ],
    )
    result = run("reconcile", "--records", str(records))
    assert result.stdout.splitlines() == ["mismatches=0"]


# --- validate ----------------------------------------------------------------


def test_validate_samples_pass() -> None:
    result = run("validate", *EXPORTS)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]


def test_validate_reports_every_bad_row(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Freight, inbound",100.00,USD\n'
        "A-2,2026-01-05,4100,Too,many,1.00,USD\n"
        "A-3,2026-13-05,4100,Bad date,1.00,USD\n"
        "A-4,2026-01-05,4100,Bad amount,ten,USD\n"
        "A-5,2026-01-05,41X0,Bad code,1.00,USD\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,25440,USD\n"
        "B,B-2,2026-01-07,4100,Not cents,12.50,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,02/01/2026,4100,Fine,1.00,USD\n"
        "C-2,01/13/2026,4100,Month first,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=9 rejected=6"]

    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 6
    expected = [
        ("ardent.csv line 4", "expected 6 fields, found 7"),
        ("ardent.csv line 5", "2026-13-05"),
        ("ardent.csv line 6", "'ten'"),
        ("ardent.csv line 7", "41X0"),
        ("borough.csv line 3", "12.50"),
        ("calder.csv line 4", "01/13/2026"),
    ]
    for (where, what), warning in zip(expected, warnings, strict=True):
        assert where in warning and what in warning, warning


def test_validate_unreadable_file_exits_2(tmp_path: Path) -> None:
    result = run("validate", str(tmp_path / "missing.csv"), EXPORTS[1])
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]


# --- --config ----------------------------------------------------------------


def _config_digest() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").rglob("*"))
        if path.is_file()
    }


def test_config_overrides_settings_for_one_run(records_file: Path, tmp_path: Path) -> None:
    before = _config_digest()
    override = tmp_path / "quarter-close.toml"
    override.write_text("[report]\ndecimals = 2\n\n[reconcile]\ntolerance = 16\n", encoding="utf-8")

    report = run("--config", str(override), "report", "--by", "month", "--records", str(records_file))
    assert report.returncode == 0, report.stderr
    assert report.stdout.splitlines() == ["month;total", "2026-01;13256.48", "2026-02;8456.50", "2026-03;5870.25"]

    reconcile = run("--config", str(override), "reconcile", "--records", str(records_file))
    assert reconcile.stdout.splitlines()[-1] == "mismatches=3"

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    strict = tmp_path / "strict.toml"
    strict.write_text('[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n', encoding="utf-8")
    validate = run("--config", str(strict), "validate", EXPORTS[1])
    assert validate.returncode == 2

    assert _config_digest() == before


def test_config_missing_file_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert "--config" in result.stderr


def test_config_does_not_leak_into_the_caller(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(CONFIG_ENV_VAR, raising=False)
    override = tmp_path / "o.toml"
    override.write_text("[report]\ndecimals = 1\n", encoding="utf-8")
    assert cli.main(["--config", str(override), "version"]) == 0
    assert CONFIG_ENV_VAR not in os.environ
