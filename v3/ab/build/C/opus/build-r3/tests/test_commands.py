"""End to end tests for ingest, report, reconcile, validate and --config."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.cli import main  # noqa: E402

SAMPLES = REPO / "samples"
SAMPLE_FILES = [
    str(SAMPLES / "system_a_export.csv"),
    str(SAMPLES / "system_b_export.csv"),
    str(SAMPLES / "system_c_export.csv"),
]
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


def ingest_samples(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


def read_output(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


# --- ingest -------------------------------------------------------------------


def test_ingest_writes_every_posting_and_reports_it(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "dir" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121


def test_ingest_keeps_refunds(tmp_path: Path) -> None:
    rows = read_output(ingest_samples(tmp_path))
    refunds = sorted(row["record_id"] for row in rows if row["amount"].startswith("-"))
    assert refunds == ["A-10019", "A-10023", "A-10037", "A-10041", "B-2221"]


def test_ingest_converts_each_system(tmp_path: Path) -> None:
    rows = {row["record_id"]: row for row in read_output(ingest_samples(tmp_path))}
    # Borough amounts are cents.
    assert rows["B-2201"]["amount"] == "254.40"
    assert rows["B-2221"]["amount"] == "-88.25"
    assert rows["B-2238"]["amount"] == "1100.03"
    # Calder dates are day first.
    assert rows["C-0401"]["date"] == "2026-01-02"
    assert rows["C-0408"]["date"] == "2026-03-13"
    assert rows["A-10001"]["amount"] == "239.55"
    assert rows["A-10001"]["date"] == "2026-01-03"
    assert {row["source_system"] for row in rows.values()} == {"A", "B", "C"}


def test_ingest_preserves_quoted_descriptions(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    rows = {row["record_id"]: row for row in read_output(out)}
    assert rows["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert rows["A-10002"]["description"] == "Drayage, port apron to DC"
    assert '"Rebill, ""Q1 true-up"", carrier"' in out.read_text(encoding="utf-8")


def test_ingest_names_accounts(tmp_path: Path) -> None:
    rows = {row["record_id"]: row for row in read_output(ingest_samples(tmp_path))}
    assert rows["A-10001"]["account_name"] == "Freight In"
    assert rows["A-10024"]["account_name"] == "Contract Labor"
    assert rows["A-10040"]["account_code"] == "8800"
    assert rows["A-10040"]["account_name"] == "UNCLASSIFIED"


def test_ingest_orders_by_date_system_id_whatever_the_input_order(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    assert run("ingest", *SAMPLE_FILES, "--out", str(first)).returncode == 0
    assert run("ingest", *reversed(SAMPLE_FILES), "--out", str(second)).returncode == 0
    assert first.read_bytes() == second.read_bytes()
    rows = read_output(first)
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)
    assert [row["record_id"] for row in rows[:4]] == ["C-0401", "C-0423", "A-10001", "A-10019"]


def test_ingest_writes_nothing_when_an_export_cannot_be_read(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    bad.write_text("not an export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", SAMPLE_FILES[0], str(bad), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert "bad.csv" in result.stderr
    assert not out.exists()


# --- report -------------------------------------------------------------------

REPORT_BY_ACCOUNT = [
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
REPORT_BY_MONTH = ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_by_account_counts_refunds_and_uses_semicolons(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == REPORT_BY_ACCOUNT


def test_report_by_month_rounds_half_to_even(tmp_path: Path) -> None:
    # February totals exactly 8456.50, which shows as 8456, not 8457.
    records = ingest_samples(tmp_path)
    result = run("report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == REPORT_BY_MONTH


def test_report_include_refunds_is_accepted_and_changes_nothing(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    for by, expected in (("account", REPORT_BY_ACCOUNT), ("month", REPORT_BY_MONTH)):
        result = run("report", "--by", by, "--records", str(records), "--include-refunds")
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == expected


def test_report_reads_the_default_records_path(tmp_path: Path) -> None:
    assert run("ingest", *SAMPLE_FILES, "--out", str(tmp_path / "out" / "records.csv")).returncode == 0
    env = dict(os.environ, PYTHONPATH=str(REPO))
    env.pop("LEDGERKIT_CONFIG", None)
    result = subprocess.run(
        [sys.executable, "-m", "ledgerkit", "report", "--by", "month"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == REPORT_BY_MONTH


def test_report_requires_by_and_fails_on_a_missing_file(tmp_path: Path) -> None:
    assert run("report").returncode == 2
    result = run("report", "--by", "account", "--records", str(tmp_path / "missing.csv"))
    assert result.returncode != 0
    assert result.stdout == ""
    assert "missing.csv" in result.stderr


# --- reconcile ----------------------------------------------------------------

RECONCILE_DEFAULT = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    # A's 498.25 includes the -42.00 meter correction credit: refunds count.
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
    "mismatches=5",
]


def test_reconcile_uses_the_settings_tolerance_by_default(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == RECONCILE_DEFAULT


def test_reconcile_tolerance_is_inclusive(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    # A spread of exactly 16.30 agrees at a tolerance of 16.30.
    result = run("reconcile", "--records", str(records), "--tolerance", "16.30")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [RECONCILE_DEFAULT[0], RECONCILE_DEFAULT[1], "mismatches=2"]


def test_reconcile_always_prints_the_count(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(records), "--tolerance", "100")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_rejects_a_tolerance_that_is_not_a_number(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    assert run("reconcile", "--records", str(records), "--tolerance", "abc").returncode == 2


# --- validate -----------------------------------------------------------------


def write_bad_exports(tmp_path: Path) -> tuple[Path, Path, Path]:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Rebill, ""x"", carrier",239.55,USD\n'
        "A-2,2026-01-04,4100,Short row,10.00\n"
        "A-3,2026-02-30,4100,Bad date,10.00,USD\n"
        "A-4,2026-01-05,4100,Bad amount,ten,USD\n"
        "A-5,2026-01-06,41X0,Bad code,10.00,USD\n"
        "A-6,03/01/2026,99,Three problems,1.2.3,USD\n",
        encoding="utf-8",
    )
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,25440,USD\n"
        "B,B-2,2026-01-08,4100,Dollars not cents,254.40,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,02/01/2026,4100,Fine,386.54,USD\n"
        "C-2,01/13/2026,4100,Month first,10.00,USD\n"
        "C-3,2026-01-02,4100,ISO date,10.00,USD\n"
        "== 3 rows ==\n",
        encoding="utf-8",
    )
    return ardent, borough, calder


def test_validate_passes_the_samples() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert result.stderr == ""


def test_validate_checks_every_row_and_warns_once_per_rejected_row(tmp_path: Path) -> None:
    ardent, borough, calder = write_bad_exports(tmp_path)
    before = sorted(tmp_path.iterdir())
    result = run("validate", str(ardent), str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout == "checked=11 rejected=8\n"
    warnings = [line for line in result.stderr.splitlines() if " WARNING " in line]
    assert len(warnings) == 8
    assert sorted(tmp_path.iterdir()) == before


def test_validate_names_the_file_line_and_problem(tmp_path: Path) -> None:
    ardent, borough, calder = write_bad_exports(tmp_path)
    stderr = run("validate", str(ardent), str(borough), str(calder)).stderr
    assert f"{ardent} line 4: expected 6 fields, found 5" in stderr
    assert f"{ardent} line 5: date '2026-02-30'" in stderr
    assert f"{ardent} line 6: amount 'ten' is not a number" in stderr
    assert f"{ardent} line 7: account code '41X0' does not match" in stderr
    assert f"{borough} line 3: Borough amount '254.40' is not an integer number of cents" in stderr
    assert f"{calder} line 4: date '01/13/2026'" in stderr
    assert f"{calder} line 5: date '2026-01-02'" in stderr
    line_8 = next(line for line in stderr.splitlines() if f"{ardent} line 8:" in line)
    assert "date '03/01/2026'" in line_8
    assert "amount '1.2.3'" in line_8
    assert "account code '99'" in line_8
    for good in (f"{ardent} line 3:", f"{borough} line 2:", f"{calder} line 3:"):
        assert good not in stderr


def test_validate_exits_2_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    unknown = tmp_path / "unknown.csv"
    unknown.write_text("not an export\n", encoding="utf-8")
    missing = tmp_path / "missing.csv"
    result = run("validate", SAMPLE_FILES[1], str(unknown), str(missing))
    assert result.returncode == 2
    assert result.stdout == "checked=39 rejected=0\n"
    assert "unknown.csv" in result.stderr
    assert "missing.csv" in result.stderr


# --- --config -----------------------------------------------------------------


def write_config(tmp_path: Path, text: str) -> Path:
    config = tmp_path / "run.toml"
    config.write_text(text, encoding="utf-8")
    return config


def test_config_is_what_version_reports(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[1] == f"settings={config}"


def test_config_sets_report_decimals_and_leaves_other_keys_alone(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "report", "--by", "month", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "month;total",
        "2026-01;13256.48",
        "2026-02;8456.50",
        "2026-03;5870.25",
    ]
    by_account = run("--config", str(config), "report", "--by", "account", "--records", str(records))
    assert "8800;UNCLASSIFIED;314.95" in by_account.stdout.splitlines()


def test_config_sets_the_unknown_account_label_for_ingest(tmp_path: Path) -> None:
    config = write_config(tmp_path, '[report]\nunknown_account_label = "Needs review"\n')
    out = tmp_path / "records.csv"
    result = run("--config", str(config), "ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    rows = {row["record_id"]: row for row in read_output(out)}
    assert rows["A-10040"]["account_name"] == "Needs review"
    assert rows["A-10001"]["account_name"] == "Freight In"


def test_config_sets_the_reconcile_tolerance_and_the_flag_still_wins(tmp_path: Path) -> None:
    records = ingest_samples(tmp_path)
    config = write_config(tmp_path, "[reconcile]\ntolerance = 20\n")
    result = run("--config", str(config), "reconcile", "--records", str(records))
    assert result.stdout.splitlines() == [RECONCILE_DEFAULT[0], "mismatches=1"]
    flagged = run("--config", str(config), "reconcile", "--records", str(records), "--tolerance", "0.05")
    assert flagged.stdout.splitlines() == RECONCILE_DEFAULT


def test_config_sets_the_validate_account_pattern(tmp_path: Path) -> None:
    config = write_config(tmp_path, '[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n')
    result = run("--config", str(config), "validate", *SAMPLE_FILES)
    assert result.returncode == 2
    assert result.stdout == "checked=120 rejected=7\n"


def test_config_works_with_inspect(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(config), "inspect", SAMPLE_FILES[0])
    assert result.returncode == 0, result.stderr
    assert "system=A" in result.stdout.splitlines()


def test_config_that_does_not_exist_is_an_error(tmp_path: Path) -> None:
    missing = tmp_path / "nope.toml"
    result = run("--config", str(missing), "version")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "nope.toml" in result.stderr


def test_config_does_not_outlive_the_run(tmp_path: Path) -> None:
    config = write_config(tmp_path, "[report]\ndecimals = 2\n")
    saved = os.environ.pop("LEDGERKIT_CONFIG", None)
    try:
        assert main(["--config", str(config), "version"]) == 0
        assert "LEDGERKIT_CONFIG" not in os.environ
        os.environ["LEDGERKIT_CONFIG"] = "/elsewhere.toml"
        assert main(["--config", str(config), "version"]) == 0
        assert os.environ["LEDGERKIT_CONFIG"] == "/elsewhere.toml"
    finally:
        os.environ.pop("LEDGERKIT_CONFIG", None)
        if saved is not None:
            os.environ["LEDGERKIT_CONFIG"] = saved


def test_nothing_under_config_is_touched(tmp_path: Path) -> None:
    config_dir = REPO / "config"
    before = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    override = write_config(tmp_path, "[report]\ndecimals = 1\n")
    records = ingest_samples(tmp_path)
    for args in (
        ("version",),
        ("inspect", *SAMPLE_FILES),
        ("ingest", *SAMPLE_FILES, "--out", str(tmp_path / "again.csv")),
        ("report", "--by", "account", "--records", str(records)),
        ("reconcile", "--records", str(records)),
        ("validate", *SAMPLE_FILES),
    ):
        run(*args)
        run("--config", str(override), *args)
    result = run("ingest", *SAMPLE_FILES, "--out", str(config_dir / "records.csv"))
    assert result.returncode != 0
    after = {path.name: path.read_bytes() for path in config_dir.iterdir()}
    assert after == before
