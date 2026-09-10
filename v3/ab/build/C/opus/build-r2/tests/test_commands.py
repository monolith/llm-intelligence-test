"""Tests for the ingest, report, reconcile and validate commands and --config."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
    str(SAMPLES / "system_c_export.csv"),
]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


def run(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
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


def read_output(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


# --- ingest ------------------------------------------------------------------


def test_ingest_merges_all_three_samples(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"

    assert out.read_text(encoding="utf-8").splitlines()[0] == HEADER
    rows = read_output(out)[1:]
    assert len(rows) == 120
    assert rows == sorted(rows, key=lambda row: (row[2], row[1], row[0]))

    by_id = {row[0]: row for row in rows}
    assert by_id["A-10001"] == [
        "A-10001", "A", "2026-01-03", "4100", "Freight In", 'Rebill, "Q1 true-up", carrier', "239.55",
    ]
    assert by_id["B-2201"][2:] == ["2026-01-07", "4100", "Freight In", "Container unload allowance", "254.40"]
    assert by_id["B-2221"][6] == "-88.25"
    assert by_id["C-0401"][2] == "2026-01-02"
    assert by_id["C-0405"][2] == "2026-03-04"
    assert by_id["A-10040"][4] == "UNCLASSIFIED"
    assert by_id["C-0437"][4] == "UNCLASSIFIED"
    assert by_id["A-10024"][4] == "Contract Labor"
    assert sum(1 for row in rows if row[6].startswith("-")) == 5


def test_ingest_output_does_not_depend_on_input_order(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    assert run("ingest", *SAMPLE_FILES, "--out", str(first), cwd=tmp_path).returncode == 0
    assert run("ingest", *reversed(SAMPLE_FILES), "--out", str(second), cwd=tmp_path).returncode == 0
    assert first.read_bytes() == second.read_bytes()


def test_ingest_preserves_descriptions_exactly(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"  Spaced,  ""quoted""  text ",100.00,USD\n',
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        'B,B-1,2026-01-05,4100,6" pipe fittings,1250,USD\n',
        encoding="utf-8",
    )
    out = tmp_path / "records.csv"
    result = run("ingest", str(ardent), str(borough), "--out", str(out), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    rows = read_output(out)[1:]
    assert rows[0][5] == '  Spaced,  "quoted"  text '
    assert rows[1][5] == '6" pipe fittings'
    assert rows[1][6] == "12.50"


def test_ingest_writes_to_out_records_csv_by_default(tmp_path: Path) -> None:
    result = run("ingest", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "wrote=120 to out/records.csv\n"
    assert len(read_output(tmp_path / "out" / "records.csv")) == 121


def test_ingest_keeps_duplicate_postings(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    b_file = str(SAMPLES / "system_b_export.csv")
    result = run("ingest", b_file, b_file, "--out", str(out), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=78 to {out}\n"


def test_ingest_fails_on_an_unreadable_row_and_writes_nothing(tmp_path: Path) -> None:
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-13-45,4100,Bad date,1250,USD\n",
        encoding="utf-8",
    )
    out = tmp_path / "records.csv"
    result = run("ingest", str(borough), "--out", str(out), cwd=tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "borough.csv line 2" in result.stderr
    assert not out.exists()


# --- report ------------------------------------------------------------------


def ingest_samples(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return out


def write_records_file(path: Path, rows: list[tuple[str, str, str, str, str]]) -> Path:
    """Write a normalized file from (id, system, date, code, amount) tuples."""
    lines = [HEADER]
    lines += [f"{rid},{system},{day},{code},Name {code},desc,{amount}" for rid, system, day, code, amount in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


SAMPLE_REPORT_BY_ACCOUNT = [
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

SAMPLE_REPORT_BY_MONTH = [
    "month;total",
    "2026-01;13256",
    "2026-02;8456",
    "2026-03;5870",
]


def test_report_by_account_counts_refunds_and_uses_semicolons(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == SAMPLE_REPORT_BY_ACCOUNT


def test_report_by_month_counts_refunds_and_uses_semicolons(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "month", "--records", str(records), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == SAMPLE_REPORT_BY_MONTH


def test_report_include_refunds_flag_is_accepted_and_changes_nothing(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    for by, expected in (("account", SAMPLE_REPORT_BY_ACCOUNT), ("month", SAMPLE_REPORT_BY_MONTH)):
        result = run("report", "--by", by, "--records", str(records), "--include-refunds", cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == expected


def test_report_reads_out_records_csv_by_default(tmp_path: Path) -> None:
    assert run("ingest", *SAMPLE_FILES, cwd=tmp_path).returncode == 0
    result = run("report", "--by", "month", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == SAMPLE_REPORT_BY_MONTH


def test_report_rounds_half_to_even(tmp_path: Path) -> None:
    records = write_records_file(
        tmp_path / "records.csv",
        [
            ("X-1", "A", "2026-01-01", "1001", "2.50"),
            ("X-2", "A", "2026-01-01", "1002", "3.50"),
            ("X-3", "A", "2026-01-01", "1003", "1240.00"),
            ("X-4", "B", "2026-01-02", "1003", "0.50"),
            ("X-5", "A", "2026-01-01", "1004", "883.25"),
            ("X-6", "C", "2026-01-03", "1004", "0.25"),
        ],
    )
    result = run("report", "--by", "account", "--records", str(records), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1:] == [
        "1001;Name 1001;2",
        "1002;Name 1002;4",
        "1003;Name 1003;1240",
        "1004;Name 1004;884",
    ]


def test_report_requires_by(tmp_path: Path) -> None:
    result = run("report", cwd=tmp_path)
    assert result.returncode == 2
    assert "--by" in result.stderr


def test_report_fails_cleanly_without_a_records_file(tmp_path: Path) -> None:
    result = run("report", "--by", "account", "--records", str(tmp_path / "missing.csv"), cwd=tmp_path)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "missing.csv" in result.stderr


# --- reconcile ---------------------------------------------------------------

SAMPLE_MISMATCHES = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
]


def test_reconcile_reports_sample_mismatches_at_the_default_tolerance(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == SAMPLE_MISMATCHES + ["mismatches=5"]


def test_reconcile_tolerance_flag_overrides_the_setting(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records), "--tolerance", "16", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        SAMPLE_MISMATCHES[0],
        SAMPLE_MISMATCHES[1],
        SAMPLE_MISMATCHES[3],
        "mismatches=3",
    ]
    result = run("reconcile", "--records", str(records), "--tolerance", "100", cwd=tmp_path)
    assert result.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_rules_on_hand_made_records(tmp_path: Path) -> None:
    records = write_records_file(
        tmp_path / "records.csv",
        [
            # Spread exactly equal to the tolerance agrees.
            ("X-1", "A", "2026-01-05", "4100", "10.00"),
            ("X-2", "B", "2026-01-06", "4100", "10.05"),
            # Only one system posted: never compared.
            ("X-3", "A", "2026-01-05", "4200", "10.00"),
            ("X-4", "A", "2026-01-09", "4200", "90.00"),
            # A refund counts: A totals 5.00 against B's 20.00.
            ("X-5", "A", "2026-02-01", "4300", "20.00"),
            ("X-6", "A", "2026-02-02", "4300", "-15.00"),
            ("X-7", "B", "2026-02-03", "4300", "20.00"),
            # Same code, different months are different combinations.
            ("X-8", "B", "2026-03-01", "4300", "1.00"),
            ("X-9", "C", "2026-03-01", "4300", "3.10"),
        ],
    )
    result = run("reconcile", "--records", str(records), "--tolerance", "0.05", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4300 2026-02 spread=15.00 A=5.00 B=20.00 C=-",
        "MISMATCH 4300 2026-03 spread=2.10 A=- B=1.00 C=3.10",
        "mismatches=2",
    ]


def test_reconcile_rejects_a_bad_tolerance(tmp_path: Path) -> None:
    for bad in ("lots", "-1", "nan"):
        result = run("reconcile", "--tolerance", bad, cwd=tmp_path)
        assert result.returncode == 2, bad
        assert "--tolerance" in result.stderr


# --- validate ----------------------------------------------------------------


def warnings_in(stderr: str) -> list[str]:
    return [line for line in stderr.splitlines() if line.startswith("LEDGERKIT WARNING")]


def test_validate_passes_the_samples(tmp_path: Path) -> None:
    result = run("validate", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert warnings_in(result.stderr) == []


def test_validate_rejects_each_kind_of_bad_row_and_keeps_going(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-04,4100,"Quoted, fine",100.00,USD\n'  # line 3: fine
        "A-2,2026-01-04,4100,Unquoted, comma,100.00,USD\n"  # line 4: field count
        "A-3,04/01/2026,4100,Wrong date format,100.00,USD\n"  # line 5: date
        "A-4,2026-01-04,4100,Bad amount,12.3.4,USD\n"  # line 6: amount
        "A-5,2026-01-04,41X0,Bad code,100.00,USD\n",  # line 7: account code
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,25440,USD\n"  # line 2: fine
        "B,B-2,2026-02-30,4100,No such day,25440,USD\n"  # line 3: date
        "B,B-3,2026-01-07,4100,Dollars not cents,254.40,USD\n",  # line 4: amount
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,Day first is right,10.00,USD\n"  # line 3: fine
        "C-2,2026-01-13,4100,ISO is wrong here,10.00,USD\n"  # line 4: date
        "C-3,01/13/2026,410,Month first and short code,x,USD\n"  # line 5: all three
        "== 3 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(borough), str(calder), cwd=tmp_path)
    assert result.returncode == 2
    assert result.stdout == "checked=11 rejected=8\n"

    warnings = warnings_in(result.stderr)
    assert len(warnings) == 8
    expected = [
        (ardent, 4, "expected 6 fields, found 7"),
        (ardent, 5, "YYYY-MM-DD"),
        (ardent, 6, "'12.3.4' is not a number"),
        (ardent, 7, "'41X0' does not match"),
        (borough, 3, "YYYY-MM-DD"),
        (borough, 4, "not an integer number of cents"),
        (calder, 4, "DD/MM/YYYY"),
        (calder, 5, "DD/MM/YYYY"),
    ]
    for warning, (path, line, reason) in zip(warnings, expected, strict=True):
        assert f"{path} line {line}:" in warning
        assert reason in warning
    assert "not a number" in warnings[-1] and "'410' does not match" in warnings[-1]


def test_validate_exits_2_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    stranger = tmp_path / "stranger.csv"
    stranger.write_text("what,is,this\n1,2,3\n", encoding="utf-8")
    result = run(
        "validate", str(SAMPLES / "system_b_export.csv"), str(stranger), str(tmp_path / "gone.csv"),
        cwd=tmp_path,
    )
    assert result.returncode == 2
    assert result.stdout == "checked=39 rejected=0\n"
    warnings = warnings_in(result.stderr)
    assert len(warnings) == 2
    assert "stranger.csv" in warnings[0]
    assert "gone.csv" in warnings[1]


def test_validate_writes_nothing(tmp_path: Path) -> None:
    result = run("validate", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


# --- --config ----------------------------------------------------------------


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "override.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_config_is_reported_by_version(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "version", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert f"settings={config.resolve()}" in result.stdout.splitlines()


def test_config_relative_path_is_read_from_the_working_directory(tmp_path: Path) -> None:
    write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", "override.toml", "version", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert f"settings={(tmp_path / 'override.toml').resolve()}" in result.stdout.splitlines()


def test_config_changes_report_decimals_and_keeps_other_keys(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "report", "--by", "account", "--records", str(records), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "4100;Freight In;6248.50" in lines
    assert "8800;UNCLASSIFIED;314.95" in lines


def test_config_changes_the_unknown_account_label_in_ingest(tmp_path: Path) -> None:
    config = write_config(tmp_path, '[report]\nunknown_account_label = "TO REVIEW"\n')
    out = tmp_path / "records.csv"
    result = run("--config", str(config), "ingest", *SAMPLE_FILES, "--out", str(out), cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    labels = {row[4] for row in read_output(out)[1:] if row[3] == "8800"}
    assert labels == {"TO REVIEW"}


def test_config_changes_the_reconcile_tolerance_and_the_flag_still_wins(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    config = write_config(tmp_path, "[reconcile]\ntolerance = 100\n")
    result = run("--config", str(config), "reconcile", "--records", str(records), cwd=tmp_path)
    assert result.stdout.splitlines() == ["mismatches=0"]
    result = run(
        "--config", str(config), "reconcile", "--records", str(records), "--tolerance", "0.05", cwd=tmp_path
    )
    assert result.stdout.splitlines()[-1] == "mismatches=5"


def test_config_changes_the_validate_pattern(tmp_path: Path) -> None:
    config = write_config(tmp_path, '[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n')
    result = run("--config", str(config), "validate", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 2
    assert result.stdout == "checked=120 rejected=7\n"


def test_config_beats_the_environment_variable(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    elsewhere = tmp_path / "elsewhere.toml"
    elsewhere.write_text("[report]\ndecimals = 1\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(REPO), LEDGERKIT_CONFIG=str(elsewhere))
    result = subprocess.run(
        [sys.executable, "-m", "ledgerkit", "--config", str(config), "version"],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=False,
    )
    assert f"settings={config.resolve()}" in result.stdout.splitlines()


def test_config_works_with_inspect(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "inspect", SAMPLE_FILES[0], cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "system=A" in result.stdout.splitlines()


def test_config_that_does_not_exist_is_an_error(tmp_path: Path) -> None:
    result = run("--config", str(tmp_path / "nope.toml"), "version", cwd=tmp_path)
    assert result.returncode == 2
    assert "nope.toml" in result.stderr
    assert result.stdout == ""


def test_config_that_is_not_toml_is_an_error(tmp_path: Path) -> None:
    config = write_config(tmp_path, "this is = = not toml\n")
    result = run("--config", str(config), "version", cwd=tmp_path)
    assert result.returncode == 2
    assert "cannot read settings" in result.stderr


def test_nothing_under_config_changes(tmp_path: Path) -> None:
    config_dir = REPO / "config"
    before = {path.name: path.read_bytes() for path in sorted(config_dir.iterdir())}

    override = write_config(tmp_path, "[report]\ndecimals = 2\n")
    records = tmp_path / "records.csv"
    runs = [
        ("--config", str(override), "version"),
        ("--config", str(override), "inspect", *SAMPLE_FILES),
        ("--config", str(override), "validate", *SAMPLE_FILES),
        ("--config", str(override), "ingest", *SAMPLE_FILES, "--out", str(records)),
        ("--config", str(override), "report", "--by", "account", "--records", str(records)),
        ("--config", str(override), "reconcile", "--records", str(records)),
    ]
    for args in runs:
        assert run(*args, cwd=tmp_path).returncode == 0, args

    after = {path.name: path.read_bytes() for path in sorted(config_dir.iterdir())}
    assert after == before
