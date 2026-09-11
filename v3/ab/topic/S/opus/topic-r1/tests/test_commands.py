"""End to end tests for the SPEC.md commands, run through ``python -m ledgerkit``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.core.fields import split_record  # noqa: E402

SAMPLES = REPO / "samples"
EXPORTS = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]
HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


def run(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
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


@pytest.fixture
def records_file(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *EXPORTS, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


# --- ingest ------------------------------------------------------------------


def test_ingest_writes_every_posting_and_creates_parent_directories(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "deeper" / "records.csv"
    result = run("ingest", *EXPORTS, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"
    lines = out.read_text(encoding="utf-8").splitlines()
    assert lines[0] == HEADER
    assert len(lines) == 121


def test_ingest_converts_each_system_and_keeps_text_exactly(records_file: Path) -> None:
    lines = set(records_file.read_text(encoding="utf-8").splitlines())
    # Ardent: quoted memo with the delimiter and doubled quotes survives the round trip.
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55' in lines
    # Borough: cents become dollars, refunds included.
    assert "B-2201,B,2026-01-07,4100,Freight In,Container unload allowance,254.40" in lines
    assert "B-2221,B,2026-02-23,5100,Packaging Materials,Credit note damaged corrugate,-88.25" in lines
    # Calder: dates are day first.
    assert "C-0401,C,2026-01-02,4100,Freight In,Container unload allowance,386.54" in lines
    # Refunds stay, unmapped codes get the label, 5200 has its current name.
    assert "A-10019,A,2026-01-03,5100,Packaging Materials,Credit note damaged corrugate,-125.00" in lines
    assert "A-10040,A,2026-03-25,8800,UNCLASSIFIED,Held for review,127.75" in lines
    assert "B-2222,B,2026-02-26,5200,Contract Labor,Night shift crew,135.69" in lines


def test_ingest_orders_by_date_then_system_then_id(records_file: Path) -> None:
    rows = [split_record(line) for line in records_file.read_text(encoding="utf-8").splitlines()[1:]]
    keys = [(row[2], row[1], row[0]) for row in rows]
    assert keys == sorted(keys)
    assert [row[0] for row in rows[:3]] == ["C-0401", "C-0423", "A-10001"]


def test_ingest_output_does_not_depend_on_argument_order(tmp_path: Path) -> None:
    forward, backward = tmp_path / "forward.csv", tmp_path / "backward.csv"
    assert run("ingest", *EXPORTS, "--out", str(forward)).returncode == 0
    assert run("ingest", *reversed(EXPORTS), "--out", str(backward)).returncode == 0
    assert forward.read_bytes() == backward.read_bytes()


def test_ingest_defaults_to_out_records_csv(tmp_path: Path) -> None:
    result = run("ingest", *EXPORTS, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "wrote=120 to out/records.csv\n"
    assert (tmp_path / "out" / "records.csv").is_file()


def test_ingest_writes_nothing_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    stray = tmp_path / "stray.csv"
    stray.write_text("not,an,export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", *EXPORTS, str(stray), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert "stray.csv" in result.stderr
    assert not out.exists()


# --- report ------------------------------------------------------------------

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
MONTH_REPORT = ["month;total", "2026-01;13256", "2026-02;8456", "2026-03;5870"]


def test_report_by_account_counts_refunds_and_rounds_half_to_even(records_file: Path) -> None:
    # 4100 is exactly 6248.50 and 5200 exactly 1747.50: half to even gives 6248 and 1748.
    result = run("report", "--by", "account", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ACCOUNT_REPORT


def test_report_by_month(records_file: Path) -> None:
    # 2026-02 is exactly 8456.50 with its refund counted: half to even gives 8456.
    result = run("report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == MONTH_REPORT


def test_report_include_refunds_is_accepted_and_changes_nothing(records_file: Path) -> None:
    for by, expected in (("account", ACCOUNT_REPORT), ("month", MONTH_REPORT)):
        result = run("report", "--by", by, "--records", str(records_file), "--include-refunds")
        assert result.returncode == 0, result.stderr
        assert result.stdout.splitlines() == expected


def test_report_reads_out_records_csv_by_default(tmp_path: Path) -> None:
    assert run("ingest", *EXPORTS, cwd=tmp_path).returncode == 0
    result = run("report", "--by", "month", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == MONTH_REPORT


def test_report_needs_by_and_a_readable_records_file(tmp_path: Path) -> None:
    assert run("report", "--records", str(tmp_path / "x.csv")).returncode == 2
    missing = run("report", "--by", "month", "--records", str(tmp_path / "missing.csv"))
    assert missing.returncode != 0
    assert missing.stdout == ""
    assert "missing.csv" in missing.stderr


@pytest.mark.parametrize(
    ("exact", "decimals", "shown"),
    [
        ("2.50", 0, "2"),
        ("3.50", 0, "4"),
        ("1240.50", 0, "1240"),
        ("883.50", 0, "884"),
        ("-0.40", 0, "0"),
        ("1.005", 2, "1.00"),
        ("1.015", 2, "1.02"),
    ],
)
def test_round_total_rounds_half_to_even(exact: str, decimals: int, shown: str) -> None:
    from decimal import Decimal

    from ledgerkit.report import round_total

    assert f"{round_total(Decimal(exact), decimals):.{decimals}f}" == shown


# --- reconcile ---------------------------------------------------------------

SAMPLE_MISMATCHES = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
]


def test_reconcile_reports_the_sample_mismatches(records_file: Path) -> None:
    result = run("reconcile", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [*SAMPLE_MISMATCHES, "mismatches=5"]


def test_reconcile_tolerance_flag_and_a_spread_equal_to_it_agrees(records_file: Path) -> None:
    wide = run("reconcile", "--records", str(records_file), "--tolerance", "20")
    assert wide.stdout.splitlines() == [SAMPLE_MISMATCHES[0], "mismatches=1"]
    edge = run("reconcile", "--records", str(records_file), "--tolerance", "57.75")
    assert edge.stdout.splitlines() == ["mismatches=0"]


def test_reconcile_counts_refunds_and_ignores_single_system_combinations(tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    records.write_text(
        HEADER + "\n"
        "A-1,A,2026-01-05,4100,Freight In,charge,100.00\n"
        "A-2,A,2026-01-06,4100,Freight In,refund,-10.00\n"
        "B-1,B,2026-01-07,4100,Freight In,charge,90.00\n"
        "C-1,C,2026-01-07,4200,Duty and Brokerage,only C posted here,5.00\n",
        encoding="utf-8",
    )
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["mismatches=0"]


@pytest.mark.parametrize("bad", ["abc", "-1", "NaN"])
def test_reconcile_rejects_a_bad_tolerance(records_file: Path, bad: str) -> None:
    result = run("reconcile", "--records", str(records_file), f"--tolerance={bad}")
    assert result.returncode == 2
    assert result.stdout == ""


# --- validate ----------------------------------------------------------------


def test_validate_passes_the_samples() -> None:
    result = run("validate", *EXPORTS)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert result.stderr == ""


def test_validate_checks_every_row_and_warns_once_per_rejected_row(tmp_path: Path) -> None:
    export = tmp_path / "ardent.csv"
    export.write_text(
        "# ARDENT LEDGER EXPORT\n"  # line 1
        "entry_id,posted_on,account,memo,amount,currency\n"  # line 2
        "A-1,2026-01-05,4100,fine,1.00,USD\n"  # line 3
        "A-2,2026-01-05,4100,short a field,1.00\n"  # line 4: field count
        "A-3,2026-02-30,4100,no such day,1.00,USD\n"  # line 5: date
        "A-4,2026-01-05,4100,words,abc,USD\n"  # line 6: amount
        "A-5,2026-01-05,41X0,odd code,1.00,USD\n"  # line 7: account code
        'A-6,2026-01-05,4100,"quoted, with a comma",1.00,USD\n'  # line 8: fine
        "A-7,01/05/2026,4100,two problems,1.2.3,USD\n",  # line 9: date and amount
        encoding="utf-8",
    )
    result = run("validate", str(export))
    assert result.returncode == 2
    assert result.stdout == "checked=7 rejected=5\n"
    warnings = [line for line in result.stderr.splitlines() if "WARNING" in line]
    assert len(warnings) == 5
    for number, problem in ((4, "fields"), (5, "date"), (6, "amount"), (7, "account code"), (9, "date")):
        assert any(f"{export} line {number}:" in line and problem in line for line in warnings)
    line_9 = next(line for line in warnings if f"{export} line 9:" in line)
    assert "amount" in line_9


def test_validate_reads_each_system_its_own_way(tmp_path: Path) -> None:
    borough = tmp_path / "borough.csv"
    borough.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,cents,25440,USD\n"
        "B,B-2,2026-01-07,4100,dollars,254.40,USD\n",
        encoding="utf-8",
    )
    calder = tmp_path / "calder.csv"
    calder.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,13/01/2026,4100,day first,1.00,USD\n"
        "C-2,2026-01-13,4100,iso,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout == "checked=4 rejected=2\n"
    assert f"{borough} line 3:" in result.stderr
    assert f"{calder} line 4:" in result.stderr


def test_validate_carries_on_past_an_unreadable_file(tmp_path: Path) -> None:
    result = run("validate", str(tmp_path / "missing.csv"), EXPORTS[0])
    assert result.returncode == 2
    assert result.stdout == "checked=42 rejected=0\n"
    assert "missing.csv" in result.stderr


# --- --config ----------------------------------------------------------------


def _config_snapshot() -> dict[str, bytes]:
    return {str(path): path.read_bytes() for path in sorted((REPO / "config").rglob("*")) if path.is_file()}


def _settings_file(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "run.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_config_changes_report_decimals(records_file: Path, tmp_path: Path) -> None:
    settings = _settings_file(tmp_path, "[report]\ndecimals = 2\n")
    result = run("--config", str(settings), "report", "--by", "month", "--records", str(records_file))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "month;total",
        "2026-01;13256.48",
        "2026-02;8456.50",
        "2026-03;5870.25",
    ]


def test_config_changes_the_unknown_account_label(tmp_path: Path) -> None:
    settings = _settings_file(tmp_path, '[report]\nunknown_account_label = "TO BE CLASSIFIED"\n')
    out = tmp_path / "records.csv"
    result = run("--config", str(settings), "ingest", *EXPORTS, "--out", str(out))
    assert result.returncode == 0, result.stderr
    text = out.read_text(encoding="utf-8")
    assert "A-10040,A,2026-03-25,8800,TO BE CLASSIFIED,Held for review,127.75" in text
    assert "UNCLASSIFIED" not in text


def test_config_changes_the_tolerance_and_the_flag_overrides_it(records_file: Path, tmp_path: Path) -> None:
    settings = _settings_file(tmp_path, "[reconcile]\ntolerance = 20\n")
    from_config = run("--config", str(settings), "reconcile", "--records", str(records_file))
    assert from_config.stdout.splitlines()[-1] == "mismatches=1"
    from_flag = run(
        "--config", str(settings), "reconcile", "--records", str(records_file), "--tolerance", "0.05"
    )
    assert from_flag.stdout.splitlines()[-1] == "mismatches=5"


def test_config_changes_the_account_code_pattern(tmp_path: Path) -> None:
    settings = _settings_file(tmp_path, '[validate]\naccount_code_pattern = "^[0-9]{3}$"\n')
    result = run("--config", str(settings), "validate", *EXPORTS)
    assert result.returncode == 2
    assert result.stdout == "checked=120 rejected=120\n"


def test_config_is_reported_by_version_and_must_exist(tmp_path: Path) -> None:
    settings = _settings_file(tmp_path, "")
    version = run("--config", str(settings), "version")
    assert version.returncode == 0, version.stderr
    assert f"settings={settings}" in version.stdout.splitlines()
    missing = run("--config", str(tmp_path / "nope.toml"), "version")
    assert missing.returncode == 2
    assert "nope.toml" in missing.stderr


def test_config_leaves_the_environment_as_it_found_it(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from ledgerkit.cli import main
    from ledgerkit.config import CONFIG_ENV_VAR

    settings = _settings_file(tmp_path, "")
    before = os.environ.get(CONFIG_ENV_VAR)
    assert main(["--config", str(settings), "version"]) == 0
    assert f"settings={settings}" in capsys.readouterr().out
    assert os.environ.get(CONFIG_ENV_VAR) == before


def test_nothing_under_config_changes(tmp_path: Path) -> None:
    before = _config_snapshot()
    settings = _settings_file(tmp_path, "[report]\ndecimals = 1\n")
    out = tmp_path / "records.csv"
    assert run("--config", str(settings), "ingest", *EXPORTS, "--out", str(out)).returncode == 0
    assert run("--config", str(settings), "report", "--by", "account", "--records", str(out)).returncode == 0
    assert run("--config", str(settings), "reconcile", "--records", str(out)).returncode == 0
    assert run("--config", str(settings), "validate", *EXPORTS).returncode == 0
    assert run("report", "--by", "month", "--records", str(out)).returncode == 0
    assert _config_snapshot() == before
