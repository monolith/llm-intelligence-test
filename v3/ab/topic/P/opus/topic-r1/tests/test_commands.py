"""Tests for ingest, report, reconcile, validate and the global --config option."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.core.values import round_half_even  # noqa: E402

SAMPLES = REPO / "samples"
# Deliberately not in A, B, C order: ingest takes files in any order.
SAMPLE_FILES = [
    str(SAMPLES / "system_c_export.csv"),
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
]

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

MISMATCHES = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
]


def run(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    env.pop("LEDGERKIT_LOG_LEVEL", None)
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
    assert result.stdout == f"wrote=120 to {out}\n"
    return out


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "override.toml"
    path.write_text(text, encoding="utf-8")
    return path


def config_dir_fingerprint() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").rglob("*"))
        if path.is_file()
    }


# --- ingest ------------------------------------------------------------------


def test_ingest_writes_every_posting_normalized(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "record_id,source_system,date,account_code,account_name,description,amount"

    rows = list(csv.reader(lines[1:]))
    assert len(rows) == 120
    by_id = {row[0]: row for row in rows}
    # Borough writes cents; the output is dollars.
    assert by_id["B-2201"] == [
        "B-2201", "B", "2026-01-07", "4100", "Freight In", "Container unload allowance", "254.40"
    ]
    assert by_id["B-2221"][6] == "-88.25"
    # Calder writes day first.
    assert by_id["C-0401"][2] == "2026-01-02"
    assert by_id["C-0408"][2] == "2026-03-13"
    # Ardent's quoted memo survives, quoted again in the output.
    assert by_id["A-10001"][5] == 'Rebill, "Q1 true-up", carrier'
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines
    assert by_id["A-10019"][6] == "-125.00"
    assert by_id["A-10024"][4] == "Contract Labor"
    assert by_id["A-10040"][4] == "UNCLASSIFIED"
    assert sum(row[6].startswith("-") for row in rows) == 5
    keys = [(row[2], row[1], row[0]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_keeps_duplicates_when_a_file_is_named_twice(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    b_export = str(SAMPLES / "system_b_export.csv")
    result = run("ingest", b_export, b_export, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=78 to {out}\n"


def test_ingest_and_report_default_to_out_records_csv(tmp_path: Path) -> None:
    ingested = run("ingest", *SAMPLE_FILES, cwd=tmp_path)
    assert ingested.returncode == 0, ingested.stderr
    assert ingested.stdout == "wrote=120 to out/records.csv\n"
    assert (tmp_path / "out" / "records.csv").is_file()

    report = run("report", "--by", "month", cwd=tmp_path)
    assert report.returncode == 0, report.stderr
    assert report.stdout.splitlines() == ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_ingest_writes_nothing_when_an_input_is_unreadable(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_FILES[0], str(tmp_path / "missing.csv"), "--out", str(out))
    assert result.returncode == 2
    assert result.stdout == ""
    assert not out.exists()


# --- report ------------------------------------------------------------------


def test_report_by_account_counts_refunds_and_uses_semicolons(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ACCOUNT_REPORT


def test_report_include_refunds_is_still_accepted(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records), "--include-refunds")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ACCOUNT_REPORT


def test_report_requires_by(tmp_path: Path) -> None:
    result = run("report", "--records", str(ingest_samples(tmp_path)))
    assert result.returncode != 0
    assert result.stdout == ""


def test_round_half_even_matches_the_conventions_table() -> None:
    shown = [round_half_even(Decimal(text), 0) for text in ("2.50", "3.50", "1240.50", "883.50")]
    assert shown == [Decimal(2), Decimal(4), Decimal(1240), Decimal(884)]
    assert str(round_half_even(Decimal("-0.4"), 0)) == "0"


# --- reconcile ---------------------------------------------------------------


def test_reconcile_reports_mismatches_at_the_default_tolerance(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [*MISMATCHES, "mismatches=5"]


def test_reconcile_tolerance_is_inclusive(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records), "--tolerance", "16.75")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [MISMATCHES[0], "mismatches=1"]


# --- validate ----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"


def test_validate_rejects_each_kind_of_bad_row_and_keeps_going(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Fine, quoted",10.00,USD\n'
        "A-2,2026-01-05,4100,Too,many,10.00,USD\n"
        "A-3,2026-02-30,4100,Bad date,10.00,USD\n"
        "A-4,2026-01-06,4100,Bad amount,ten,USD\n"
        "A-5,2026-01-07,41A0,Bad code,10.00,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,2026-01-02,4100,ISO date in a Calder file,1.00,USD\n"
        "C-2,13/01/2026,4100,Fine,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Dollars not cents,12.50,USD\n"
        "B,B-2,2026-01-07,4100,Fine,1250,USD\n",
        encoding="utf-8",
    )

    result = run("validate", str(ardent), str(calder), str(borough))
    assert result.returncode == 2
    assert result.stdout == "checked=9 rejected=6\n"
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 6
    for path, number in [(ardent, 4), (ardent, 5), (ardent, 6), (ardent, 7), (calder, 3), (borough, 2)]:
        assert any(f"{path} line {number}:" in line for line in warnings), (path, number)


def test_validate_fails_on_a_file_it_cannot_read(tmp_path: Path) -> None:
    result = run("validate", SAMPLE_FILES[0], str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout == "checked=39 rejected=0\n"


# --- --config ----------------------------------------------------------------


def test_config_changes_report_decimals_and_leaves_config_dir_alone(tmp_path: Path) -> None:
    before = config_dir_fingerprint()
    records = ingest_samples(tmp_path)
    override = write_config(tmp_path, "[report]\ndecimals = 2\n")

    result = run("--config", str(override), "report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "4100;Freight In;6248.50" in lines
    assert "5200;Contract Labor;1747.50" in lines
    assert config_dir_fingerprint() == before


def test_config_changes_reconcile_tolerance(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    override = write_config(tmp_path, "[reconcile]\ntolerance = 20\n")
    result = run("--config", str(override), "reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [MISMATCHES[0], "mismatches=1"]


def test_config_changes_the_unknown_account_label_for_ingest(tmp_path: Path) -> None:
    override = write_config(tmp_path, '[report]\nunknown_account_label = "UNMAPPED"\n')
    out = tmp_path / "records.csv"
    result = run("--config", str(override), "ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert ",8800,UNMAPPED," in out.read_text(encoding="utf-8")


def test_config_changes_the_validate_pattern(tmp_path: Path) -> None:
    override = write_config(tmp_path, '[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n')
    result = run("--config", str(override), "validate", str(SAMPLES / "system_b_export.csv"))
    assert result.returncode == 2
    # 15 of the 39 Borough rows are on 4xxx codes.
    assert result.stdout == "checked=39 rejected=24\n"


def test_config_is_shown_by_version(tmp_path: Path) -> None:
    override = write_config(tmp_path, "")
    result = run("--config", str(override), "version")
    assert result.returncode == 0, result.stderr
    assert f"settings={override}" in result.stdout.splitlines()


def test_config_pointing_at_a_missing_file_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
