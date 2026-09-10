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

from ledgerkit.analysis import round_for_display  # noqa: E402

SAMPLES = REPO / "samples"
ALL_SAMPLES = [
    str(SAMPLES / "system_c_export.csv"),
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
]


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
def records_file(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *ALL_SAMPLES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# --- ingest -----------------------------------------------------------------


def test_ingest_writes_every_posting_and_creates_parents(tmp_path: Path) -> None:
    out = tmp_path / "a" / "b" / "records.csv"
    result = run("ingest", *ALL_SAMPLES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "record_id,source_system,date,account_code,account_name,description,amount"
    rows = read_rows(out)
    assert len(rows) == 120
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5


def test_ingest_orders_by_date_system_id(records_file: Path) -> None:
    rows = read_rows(records_file)
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)
    assert [row["record_id"] for row in rows[:3]] == ["C-0401", "C-0423", "A-10001"]


def test_ingest_interprets_each_system(records_file: Path) -> None:
    by_id = {row["record_id"]: row for row in read_rows(records_file)}
    # A quoted memo keeps its delimiter and quotes, and is quoted again on output.
    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert '"Rebill, ""Q1 true-up"", carrier"' in records_file.read_text(encoding="utf-8")
    # Borough writes cents.
    assert by_id["B-2201"]["amount"] == "254.40"
    assert by_id["B-2221"]["amount"] == "-88.25"
    # Calder writes day first.
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["C-0412"]["date"] == "2026-03-17"
    # Account names come from the map; unmapped codes get the configured label.
    assert by_id["A-10024"]["account_name"] == "Contract Labor"
    assert by_id["C-0437"]["account_name"] == "UNCLASSIFIED"
    assert by_id["A-10003"] == {
        "record_id": "A-10003",
        "source_system": "A",
        "date": "2026-01-09",
        "account_code": "4100",
        "account_name": "Freight In",
        "description": "Inbound freight consolidation",
        "amount": "226.28",
    }


def test_ingest_fails_without_writing_when_an_input_is_unreadable(tmp_path: Path) -> None:
    junk = tmp_path / "junk.csv"
    junk.write_text("not an export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", ALL_SAMPLES[0], str(junk), "--out", str(out))
    assert result.returncode == 1
    assert result.stdout == ""
    assert not out.exists()


# --- report -----------------------------------------------------------------

EXPECTED_BY_ACCOUNT = [
    "account_code;account_name;total",
    "4100;Freight In;6248",  # exactly 6248.50: half to even goes down
    "4200;Duty and Brokerage;2971",
    "4300;Storage;2886",
    "5100;Packaging Materials;3400",
    "5200;Contract Labor;1748",  # exactly 1747.50: half to even goes up
    "5300;Equipment Rental;1621",
    "6100;Utilities;3577",
    "6200;Insurance;4400",
    "8800;UNCLASSIFIED;315",
    "9000;Suspense;417",
]

EXPECTED_BY_MONTH = [
    "month;total",
    "2026-01;13256",
    "2026-02;8456",  # exactly 8456.50
    "2026-03;5870",
]


def test_report_by_account(records_file: Path) -> None:
    result = run("report", "--by", "account", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == EXPECTED_BY_ACCOUNT


def test_report_by_month(records_file: Path) -> None:
    result = run("report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == EXPECTED_BY_MONTH


def test_report_counts_refunds_with_or_without_the_flag(records_file: Path) -> None:
    plain = run("report", "--by", "account", "--records", str(records_file))
    flagged = run("report", "--by", "account", "--records", str(records_file), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_requires_by(records_file: Path) -> None:
    result = run("report", "--records", str(records_file))
    assert result.returncode == 2


def test_round_for_display_is_half_even() -> None:
    assert round_for_display(Decimal("2.50"), 0) == Decimal("2")
    assert round_for_display(Decimal("3.50"), 0) == Decimal("4")
    assert round_for_display(Decimal("1240.50"), 0) == Decimal("1240")
    assert round_for_display(Decimal("883.50"), 0) == Decimal("884")
    assert str(round_for_display(Decimal("-0.40"), 0)) == "0"


# --- reconcile --------------------------------------------------------------


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


def test_reconcile_tolerance_is_inclusive(records_file: Path) -> None:
    # A spread equal to the tolerance agrees; only a wider spread is reported.
    result = run("reconcile", "--records", str(records_file), "--tolerance", "15.45")
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[-1] == "mismatches=3"
    assert not any(" 5300 2026-03 " in line for line in lines)


def test_reconcile_rejects_a_bad_tolerance(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file), "--tolerance", "lots")
    assert result.returncode == 2


# --- validate ---------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *ALL_SAMPLES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"


def test_validate_rejects_bad_rows_and_keeps_going(tmp_path: Path) -> None:
    export = tmp_path / "calder.csv"
    export.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,fine,1.00,USD\n"
        "C-2,01/13/2026,4100,month first,1.00,USD\n"
        "C-3,01/01/2026,4100,short row\n"
        "C-4,01/01/2026,41X0,bad account,1.00,USD\n"
        "C-5,01/01/2026,4100,bad amount,one,USD\n"
        "== 5 rows ==\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,fine,25440,USD\n"
        "B,B-2,2026-01-07,4100,dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    result = run("validate", str(export), str(borough))
    assert result.returncode == 2
    assert result.stdout == "checked=7 rejected=5\n"
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 5
    for line_number in (4, 5, 6, 7):
        assert any(f"{export} line {line_number}:" in line for line in warnings)
    assert any(f"{borough} line 3:" in line for line in warnings)


def test_validate_handles_quoted_ardent_memos(tmp_path: Path) -> None:
    export = tmp_path / "ardent.csv"
    export.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Rebill, ""Q1"", carrier",239.55,USD\n'
        "A-2,2026-01-03,4100,Rebill, carrier,239.55,USD\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout == "checked=2 rejected=1\n"
    assert f"{export} line 4: expected 6 fields, found 7" in result.stderr


def test_validate_exits_2_on_an_unreadable_file(tmp_path: Path) -> None:
    result = run("validate", ALL_SAMPLES[0], str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout == "checked=39 rejected=0\n"


# --- --config ---------------------------------------------------------------


def test_config_override_applies_to_one_run(tmp_path: Path, records_file: Path) -> None:
    settings_before = (REPO / "config" / "settings.toml").read_bytes()
    override = tmp_path / "override.toml"
    override.write_text(
        '[report]\ndecimals = 2\nunknown_account_label = "TBD"\n'
        '[reconcile]\ntolerance = 20\n'
        '[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n',
        encoding="utf-8",
    )

    report = run("--config", str(override), "report", "--by", "month", "--records", str(records_file))
    assert report.stdout.splitlines() == ["month;total", "2026-01;13256.48", "2026-02;8456.50", "2026-03;5870.25"]

    out = tmp_path / "tbd.csv"
    assert run("--config", str(override), "ingest", *ALL_SAMPLES, "--out", str(out)).returncode == 0
    assert {row["account_name"] for row in read_rows(out) if row["account_code"] == "8800"} == {"TBD"}

    reconcile = run("--config", str(override), "reconcile", "--records", str(records_file))
    assert reconcile.stdout.splitlines()[-1] == "mismatches=1"

    validate = run("--config", str(override), "validate", ALL_SAMPLES[0])
    assert validate.returncode == 2

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    # The next run without --config is back to the checked in settings.
    assert run("report", "--by", "month", "--records", str(records_file)).stdout.splitlines() == EXPECTED_BY_MONTH
    assert (REPO / "config" / "settings.toml").read_bytes() == settings_before
    assert sorted(path.name for path in (REPO / "config").iterdir()) == ["settings.toml"]


def test_config_missing_file_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
