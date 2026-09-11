"""Tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.parsers import system_a  # noqa: E402

SAMPLES = REPO / "samples"
EXPORTS = [SAMPLES / name for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]
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


def ingest_samples(out: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return run(*extra, "ingest", *map(str, EXPORTS), "--out", str(out))


def write_normalized(path: Path, rows: list[str]) -> Path:
    path.write_text("\n".join([HEADER, *rows]) + "\n", encoding="utf-8")
    return path


def config_digest() -> str:
    digest = hashlib.sha256()
    for path in sorted((REPO / "config").rglob("*")):
        digest.update(str(path.relative_to(REPO)).encode("utf-8"))
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


# --- readers -----------------------------------------------------------------


def test_system_a_reads_quoted_memos() -> None:
    rows = system_a.read_rows(SAMPLES / "system_a_export.csv")
    assert len(rows) == 42
    assert rows[0]["memo"] == 'Rebill, "Q1 true-up", carrier'
    assert rows[0]["amount"] == "239.55"


# --- ingest ------------------------------------------------------------------


def test_ingest_writes_every_posting_normalized(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = ingest_samples(out)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"

    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121
    # Quoted memo survives exactly, and is quoted again on the way out.
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines
    # Borough cents become dollars; Borough refunds are kept.
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    assert "B-2221,B,2026-02-23,5100,Packaging Materials,Credit note damaged corrugate,-88.25" in lines
    # Calder dates are day first.
    assert "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54" in lines
    assert "C-0408,C,2026-03-13,4100,Freight In,Fuel surcharge inbound,80.94" in lines
    # The later 5200 name wins; unknown codes get the configured label.
    assert "A-10024,A,2026-01-05,5200,Contract Labor,Night shift crew,144.11" in lines
    assert "A-10040,A,2026-03-25,8800,UNCLASSIFIED,Held for review,127.75" in lines

    with out.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5


def test_ingest_output_does_not_depend_on_file_order(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    assert ingest_samples(first).returncode == 0
    result = run("ingest", *map(str, reversed(EXPORTS)), "--out", str(second))
    assert result.returncode == 0, result.stderr
    assert first.read_bytes() == second.read_bytes()


# --- report ------------------------------------------------------------------


def test_report_by_account_uses_semicolons_rounds_half_even_and_counts_refunds(tmp_path: Path) -> None:
    records = write_normalized(
        tmp_path / "records.csv",
        [
            "a1,A,2026-01-05,4100,Freight In,x,2.50",
            "a2,A,2026-01-06,4200,Duty and Brokerage,x,3.00",
            "b1,B,2026-02-06,4200,Duty and Brokerage,x,0.50",
            "a3,A,2026-02-07,5100,Packaging Materials,x,10.00",
            "a4,A,2026-02-08,5100,Packaging Materials,refund,-1.00",
            'c1,C,2026-03-01,8800,"Odd; name",x,883.50',
        ],
    )
    expected = [
        "account_code;account_name;total",
        "4100;Freight In;2",
        "4200;Duty and Brokerage;4",
        "5100;Packaging Materials;9",
        '8800;"Odd; name";884',
    ]
    plain = run("report", "--by", "account", "--records", str(records))
    assert plain.returncode == 0, plain.stderr
    assert plain.stdout.splitlines() == expected
    flagged = run("report", "--by", "account", "--records", str(records), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout.splitlines() == expected


def test_report_by_month(tmp_path: Path) -> None:
    records = write_normalized(
        tmp_path / "records.csv",
        [
            "a1,A,2026-02-05,4100,Freight In,x,1240.50",
            "a2,A,2026-01-06,4200,Duty and Brokerage,x,3.00",
            "a3,A,2026-01-07,5100,Packaging Materials,refund,-0.40",
        ],
    )
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["month;total", "2026-01;3", "2026-02;1240"]


def test_report_on_ingested_samples(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    assert ingest_samples(out).returncode == 0
    result = run("report", "--by", "account", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    codes = [line.split(";")[0] for line in lines[1:]]
    assert codes == ["4100", "4200", "4300", "5100", "5200", "5300", "6100", "6200", "8800", "9000"]


# --- reconcile ---------------------------------------------------------------


def test_reconcile_reports_only_disagreements_between_two_or_more_systems(tmp_path: Path) -> None:
    records = write_normalized(
        tmp_path / "records.csv",
        [
            "a1,A,2026-02-02,4200,Duty and Brokerage,x,455.00",
            "b1,B,2026-02-03,4200,Duty and Brokerage,x,500.00",
            "b2,B,2026-02-04,4200,Duty and Brokerage,x,12.75",
            "a2,A,2026-01-02,4100,Freight In,x,100.00",
            "c1,C,2026-01-03,4100,Freight In,x,100.05",
            "a3,A,2026-01-04,5100,Packaging Materials,x,50.00",
            "c2,C,2026-01-05,5100,Packaging Materials,x,60.00",
            "c3,C,2026-01-06,5100,Packaging Materials,refund,-10.00",
            "a4,A,2026-03-01,6100,Utilities,only one system,999.00",
            "a5,A,2026-01-09,4100,Freight In,x,1.00",
            "b3,B,2026-01-09,4100,Freight In,x,1.00",
        ],
    )
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4100 2026-01 spread=100.00 A=101.00 B=1.00 C=100.05",
        "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
        "mismatches=2",
    ]

    # A spread equal to the tolerance counts as agreement.
    loose = run("reconcile", "--records", str(records), "--tolerance", "57.75")
    assert loose.returncode == 0, loose.stderr
    assert loose.stdout.splitlines() == [
        "MISMATCH 4100 2026-01 spread=100.00 A=101.00 B=1.00 C=100.05",
        "mismatches=1",
    ]


def test_reconcile_on_ingested_samples_ends_with_count(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    assert ingest_samples(out).returncode == 0
    result = run("reconcile", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[-1] == f"mismatches={len(lines) - 1}"
    assert all(line.startswith("MISMATCH ") for line in lines[:-1])


# --- validate ----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *map(str, EXPORTS))
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert result.stderr == ""


def test_validate_rejects_every_bad_row_and_names_file_and_line(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Quoted, fine",1.00,USD\n'
        "A-2,2026-01-03,4100,Unquoted, comma,1.00,USD\n"
        "A-3,2026-13-01,4100,Bad month,1.00,USD\n"
        "A-4,2026-01-03,41A0,Bad code,abc,USD\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,25440,USD\n"
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
    result = run("validate", str(ardent), str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout == "checked=8 rejected=5\n"
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 5
    for name, number in [("ardent.csv", 4), ("ardent.csv", 5), ("ardent.csv", 6), ("borough.csv", 3), ("calder.csv", 4)]:
        assert any(f"{name} line {number}:" in line for line in warnings), (name, number)
    a4 = next(line for line in warnings if "ardent.csv line 6:" in line)
    assert "'abc'" in a4 and "'41A0'" in a4


def test_validate_exits_2_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    stranger = tmp_path / "stranger.csv"
    stranger.write_text("who,knows\n1,2\n", encoding="utf-8")
    result = run("validate", str(SAMPLES / "system_b_export.csv"), str(stranger), str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout == "checked=39 rejected=0\n"
    assert "stranger.csv" in result.stderr and "missing.csv" in result.stderr


# --- --config ----------------------------------------------------------------


def test_config_option_changes_settings_for_one_run(tmp_path: Path) -> None:
    before = config_digest()
    override = tmp_path / "run.toml"
    override.write_text('[report]\ndecimals = 2\nunknown_account_label = "NOT MAPPED"\n', encoding="utf-8")

    out = tmp_path / "records.csv"
    assert ingest_samples(out, "--config", str(override)).returncode == 0
    assert "A-10040,A,2026-03-25,8800,NOT MAPPED,Held for review,127.75" in out.read_text(encoding="utf-8")

    report = run("--config", str(override), "report", "--by", "month", "--records", str(out))
    assert report.returncode == 0, report.stderr
    assert all(len(line.split(";")[1].split(".")[1]) == 2 for line in report.stdout.splitlines()[1:])

    version = run("--config", str(override), "version")
    assert f"settings={override}" in version.stdout.splitlines()

    strict = tmp_path / "strict.toml"
    strict.write_text('[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n', encoding="utf-8")
    validate = run("--config", str(strict), "validate", *map(str, EXPORTS))
    assert validate.returncode == 2
    assert validate.stdout == "checked=120 rejected=7\n"

    tight = tmp_path / "tight.toml"
    tight.write_text("[reconcile]\ntolerance = 100000\n", encoding="utf-8")
    reconcile = run("--config", str(tight), "reconcile", "--records", str(out))
    assert reconcile.stdout == "mismatches=0\n"

    assert config_digest() == before


def test_config_option_with_missing_file_fails(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "absent.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "absent.toml" in result.stderr
