"""Tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [
    SAMPLES / "system_c_export.csv",
    SAMPLES / "system_a_export.csv",
    SAMPLES / "system_b_export.csv",
]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


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


def ingest_samples(out: Path) -> subprocess.CompletedProcess[str]:
    return run("ingest", *map(str, SAMPLE_FILES), "--out", str(out))


def read_output(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_records_file(path: Path, rows: list[tuple[str, ...]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(HEADER.split(","))
        writer.writerows(rows)
    return path


def config_snapshot() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").rglob("*"))
        if path.is_file()
    }


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting_in_date_system_id_order(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = ingest_samples(out)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=120 to {out}"]
    assert out.read_text(encoding="utf-8").splitlines()[0] == HEADER

    rows = read_output(out)
    assert len(rows) == 120
    assert [sum(row["source_system"] == system for row in rows) for system in "ABC"] == [42, 39, 39]
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_writes_to_out_records_csv_by_default(tmp_path: Path) -> None:
    result = run("ingest", str(SAMPLES / "system_b_export.csv"), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["wrote=39 to out/records.csv"]
    assert (tmp_path / "out" / "records.csv").is_file()


def test_ingest_converts_each_systems_amounts_and_dates(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    ingest_samples(out)
    by_id = {row["record_id"]: row for row in read_output(out)}

    # Borough writes whole cents.
    assert (by_id["B-2201"]["date"], by_id["B-2201"]["amount"]) == ("2026-01-07", "254.40")
    assert by_id["B-2221"]["amount"] == "-88.25"
    # Calder writes dates day first.
    assert by_id["C-0401"]["date"] == "2026-01-02"
    assert by_id["C-0417"]["date"] == "2026-02-01"
    assert by_id["C-0409"]["date"] == "2026-01-15"
    # Refunds are kept, and names come from the account map.
    assert by_id["A-10019"]["amount"] == "-125.00"
    assert by_id["A-10024"]["account_name"] == "Contract Labor"
    assert by_id["A-10040"]["account_name"] == "UNCLASSIFIED"


def test_ingest_preserves_a_quoted_description(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    ingest_samples(out)
    by_id = {row["record_id"]: row for row in read_output(out)}
    assert by_id["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert '"Rebill, ""Q1 true-up"", carrier"' in out.read_text(encoding="utf-8")


def test_ingest_keeps_whitespace_and_repeated_postings(tmp_path: Path) -> None:
    export = tmp_path / "ardent.csv"
    export.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        "A-1,2026-01-04,4100,Two  spaces ,10.00,USD\n",
        encoding="utf-8",
    )
    out = tmp_path / "records.csv"
    result = run("ingest", str(export), str(export), "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [f"wrote=2 to {out}"]
    assert [row["description"] for row in read_output(out)] == ["Two  spaces ", "Two  spaces "]


def test_ingest_writes_nothing_when_an_export_cannot_be_read(tmp_path: Path) -> None:
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,2026-01-13,4100,Written month first,1.00,USD\n"
        "== 1 rows ==\n",
        encoding="utf-8",
    )
    out = tmp_path / "records.csv"
    result = run("ingest", str(SAMPLES / "system_a_export.csv"), str(calder), "--out", str(out))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "DD/MM/YYYY" in result.stderr
    assert not out.exists()


# --- report -------------------------------------------------------------------


def test_report_by_account_uses_semicolons_and_rounds_half_to_even(tmp_path: Path) -> None:
    records = write_records_file(
        tmp_path / "records.csv",
        [
            ("A-1", "A", "2026-01-05", "4200", "Duty and Brokerage", "x", "1.25"),
            ("B-1", "B", "2026-01-06", "4200", "Duty and Brokerage", "x", "1.25"),
            ("A-2", "A", "2026-02-01", "4100", "Freight In", "with, comma", "3.50"),
            ("C-1", "C", "2026-02-02", "7777", "UNCLASSIFIED", "x", "1240.50"),
        ],
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;4",
        "4200;Duty and Brokerage;2",
        "7777;UNCLASSIFIED;1240",
    ]


def test_report_by_month_counts_refunds_with_or_without_the_flag(tmp_path: Path) -> None:
    records = write_records_file(
        tmp_path / "records.csv",
        [
            ("A-1", "A", "2026-02-03", "5100", "Packaging Materials", "x", "883.50"),
            ("A-2", "A", "2026-01-03", "5100", "Packaging Materials", "credit", "-125.00"),
            ("B-1", "B", "2026-01-09", "5100", "Packaging Materials", "x", "130.00"),
        ],
    )
    for extra in ([], ["--include-refunds"]):
        result = run("report", "--by", "month", "--records", str(records), *extra)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == ["month;total", "2026-01;5", "2026-02;884"]


def test_report_reads_what_ingest_wrote(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    ingest_samples(out)
    result = run("report", "--by", "account", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert lines[0] == "account_code;account_name;total"
    codes = [line.split(";")[0] for line in lines[1:]]
    assert codes == ["4100", "4200", "4300", "5100", "5200", "5300", "6100", "6200", "8800", "9000"]
    assert any(line.startswith("5200;Contract Labor;") for line in lines)


def test_report_exits_2_without_a_records_file(tmp_path: Path) -> None:
    result = run("report", "--by", "month", "--records", str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout == ""


# --- reconcile ----------------------------------------------------------------


def test_reconcile_finds_the_spec_example_in_the_samples(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    ingest_samples(out)
    result = run("reconcile", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-" in lines
    mismatches = [line for line in lines if line.startswith("MISMATCH ")]
    assert lines == mismatches + [f"mismatches={len(mismatches)}"]
    keys = [tuple(line.split()[1:3]) for line in mismatches]
    assert keys == sorted(keys)


def test_reconcile_applies_the_tolerance_and_counts_refunds(tmp_path: Path) -> None:
    records = write_records_file(
        tmp_path / "records.csv",
        [
            ("A-1", "A", "2026-01-05", "4100", "Freight In", "x", "100.00"),
            ("B-1", "B", "2026-01-06", "4100", "Freight In", "x", "100.05"),
            ("A-2", "A", "2026-02-05", "4100", "Freight In", "x", "100.00"),
            ("A-3", "A", "2026-02-06", "4100", "Freight In", "refund", "-10.00"),
            ("C-1", "C", "2026-02-07", "4100", "Freight In", "x", "90.00"),
            ("A-4", "A", "2026-03-05", "4100", "Freight In", "one system only", "500.00"),
            ("A-5", "A", "2026-01-05", "4000", "UNCLASSIFIED", "x", "1.00"),
            ("C-2", "C", "2026-01-05", "4000", "UNCLASSIFIED", "x", "2.00"),
        ],
    )
    default = run("reconcile", "--records", str(records))
    assert default.returncode == 0, default.stderr
    assert default.stdout.splitlines() == [
        "MISMATCH 4000 2026-01 spread=1.00 A=1.00 B=- C=2.00",
        "mismatches=1",
    ]

    tight = run("reconcile", "--records", str(records), "--tolerance", "0.01")
    assert tight.returncode == 0, tight.stderr
    assert tight.stdout.splitlines() == [
        "MISMATCH 4000 2026-01 spread=1.00 A=1.00 B=- C=2.00",
        "MISMATCH 4100 2026-01 spread=0.05 A=100.00 B=100.05 C=-",
        "mismatches=2",
    ]


def test_reconcile_refuses_a_tolerance_that_is_not_a_number(tmp_path: Path) -> None:
    result = run("reconcile", "--records", str(tmp_path / "records.csv"), "--tolerance", "lots")
    assert result.returncode == 2
    assert result.stdout == ""


# --- validate -----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *map(str, SAMPLE_FILES))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["checked=120 rejected=0"]
    assert "WARNING" not in result.stderr


def test_validate_checks_every_row_and_warns_once_per_bad_row(tmp_path: Path) -> None:
    export = tmp_path / "borough.csv"
    export.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,25440,USD\n"
        "B,B-2,2026-01-07,4100,Too,many,100,USD\n"
        "B,B-3,07/01/2026,4100,Wrong date format,100,USD\n"
        "B,B-4,2026-01-07,4100,Not a number,12x,USD\n"
        "B,B-5,2026-01-07,41A0,Bad code,100,USD\n",
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=5 rejected=4"]
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 4
    for number in (3, 4, 5, 6):
        assert any(f"{export} line {number}:" in warning for warning in warnings)


def test_validate_reads_calder_dates_day_first(tmp_path: Path) -> None:
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,Day first,1.00,USD\n"
        "C-2,2026-01-13,4100,ISO,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(calder))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=2 rejected=1"]
    assert "line 4:" in result.stderr
    assert "line 3:" not in result.stderr


def test_validate_exits_2_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    result = run("validate", str(SAMPLES / "system_b_export.csv"), str(tmp_path / "missing.csv"))
    assert result.returncode == 2
    assert result.stdout.splitlines() == ["checked=39 rejected=0"]
    assert "missing.csv" in result.stderr


# --- --config -----------------------------------------------------------------


def test_config_option_works_with_every_subcommand(tmp_path: Path) -> None:
    before = config_snapshot()
    settings = tmp_path / "quarter-close.toml"
    settings.write_text(
        "[report]\n"
        "decimals = 2\n"
        'unknown_account_label = "TO BE CLASSIFIED"\n'
        "\n"
        "[reconcile]\n"
        "tolerance = 1000000\n"
        "\n"
        "[validate]\n"
        'account_code_pattern = "^4[0-9]{3}$"\n',
        encoding="utf-8",
    )
    config = ["--config", str(settings)]
    out = tmp_path / "records.csv"

    ingest = run(*config, "ingest", *map(str, SAMPLE_FILES), "--out", str(out))
    assert ingest.returncode == 0, ingest.stderr
    assert {row["account_name"] for row in read_output(out) if row["account_code"] == "8800"} == {
        "TO BE CLASSIFIED"
    }

    report = run(*config, "report", "--by", "month", "--records", str(out))
    assert report.returncode == 0, report.stderr
    totals = [line.split(";")[1] for line in report.stdout.splitlines()[1:]]
    assert totals and all(len(total.split(".")[1]) == 2 for total in totals)

    reconcile = run(*config, "reconcile", "--records", str(out))
    assert reconcile.stdout.splitlines() == ["mismatches=0"]

    validate = run(*config, "validate", str(SAMPLES / "system_a_export.csv"))
    assert validate.returncode == 2
    assert "rejected=0" not in validate.stdout

    version = run(*config, "version")
    assert f"settings={settings}" in version.stdout.splitlines()

    assert config_snapshot() == before


def test_config_option_with_a_missing_file_exits_2(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
