"""Tests for ingest, report, reconcile, validate and the global --config option."""

from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import sys
from collections import defaultdict
from decimal import ROUND_HALF_EVEN, Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
# Deliberately not in A, B, C order: ingest has to cope with any order.
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_c_export.csv", "system_a_export.csv", "system_b_export.csv")]
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


def ingest_samples(tmp_path: Path) -> Path:
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    return out


def read_output(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_normalized(path: Path, rows: list[str]) -> Path:
    path.write_text(HEADER + "\n" + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def config_digest() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((REPO / "config").rglob("*"))
        if path.is_file()
    }


# --- ingest ------------------------------------------------------------------


def test_ingest_writes_every_posting_in_order(tmp_path: Path) -> None:
    out = tmp_path / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {out}\n"

    raw = out.read_bytes()
    assert b"\r" not in raw
    assert raw.decode("utf-8").splitlines()[0] == HEADER

    rows = read_output(out)
    assert len(rows) == 120
    assert len({row["record_id"] for row in rows}) == 120
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_converts_each_system_correctly(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    rows = {row["record_id"]: row for row in read_output(out)}

    # Borough writes whole cents.
    assert rows["B-2201"]["amount"] == "254.40"
    assert rows["B-2221"]["amount"] == "-88.25"
    # Calder writes day first.
    assert rows["C-0401"]["date"] == "2026-01-02"
    assert rows["C-0409"]["date"] == "2026-01-15"
    # Ardent memos keep their commas and quotes, and are quoted in the output.
    assert rows["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert '"Rebill, ""Q1 true-up"", carrier"' in out.read_text(encoding="utf-8")
    assert rows["A-10019"]["amount"] == "-125.00"
    # Names come from the map; 5200 is the FY-2 name; unknown codes get the label.
    assert rows["A-10024"]["account_name"] == "Contract Labor"
    assert rows["A-10040"]["account_code"] == "8800"
    assert rows["A-10040"]["account_name"] == "UNCLASSIFIED"
    assert rows["C-0438"]["account_name"] == "UNCLASSIFIED"


def test_ingest_creates_parent_directories(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "deeper" / "records.csv"
    result = run("ingest", *SAMPLE_FILES, "--out", str(out))
    assert result.returncode == 0, result.stderr
    assert out.is_file()


def test_ingest_defaults_to_out_records_csv(tmp_path: Path) -> None:
    result = run("ingest", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert result.stdout == f"wrote=120 to {Path('out') / 'records.csv'}\n"
    assert len(read_output(tmp_path / "out" / "records.csv")) == 120


def test_ingest_fails_on_unrecognized_file(tmp_path: Path) -> None:
    bogus = tmp_path / "bogus.csv"
    bogus.write_text("not,an,export\n", encoding="utf-8")
    out = tmp_path / "records.csv"
    result = run("ingest", str(bogus), "--out", str(out))
    assert result.returncode != 0
    assert result.stdout == ""
    assert not out.exists()


# --- report ------------------------------------------------------------------


def expected_totals(rows: list[dict[str, str]], key: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        totals[row[key]] += Decimal(row["amount"])
    return totals


def whole(value: Decimal) -> str:
    return str(value.quantize(Decimal(1), rounding=ROUND_HALF_EVEN))


def test_report_by_account_uses_semicolons_and_counts_refunds(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    rows = read_output(out)
    result = run("report", "--by", "account", "--records", str(out))
    assert result.returncode == 0, result.stderr

    names = {row["account_code"]: row["account_name"] for row in rows}
    totals = expected_totals(rows, "account_code")
    expected = ["account_code;account_name;total"] + [
        f"{code};{names[code]};{whole(totals[code])}" for code in sorted(totals)
    ]
    assert result.stdout.splitlines() == expected
    assert any(line.startswith("8800;UNCLASSIFIED;") for line in expected)


def test_report_by_month(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    rows = read_output(out)
    result = run("report", "--by", "month", "--records", str(out))
    assert result.returncode == 0, result.stderr

    totals = expected_totals([{**row, "month": row["date"][:7]} for row in rows], "month")
    expected = ["month;total"] + [f"{month};{whole(totals[month])}" for month in sorted(totals)]
    assert result.stdout.splitlines() == expected
    assert [line.split(";")[0] for line in expected[1:]] == ["2026-01", "2026-02", "2026-03"]


def test_report_rounds_totals_half_to_even_once(tmp_path: Path) -> None:
    records = write_normalized(
        tmp_path / "records.csv",
        [
            "X1,A,2026-01-01,4100,Freight In,a,2.50",
            "X2,A,2026-01-01,4200,Duty and Brokerage,b,3.50",
            "X3,A,2026-01-01,4300,Storage,c,1240.50",
            # Rounded posting by posting this would be 883 + 0 = 883.
            "X4,A,2026-01-01,5100,Packaging Materials,d,883.25",
            "X5,B,2026-01-01,5100,Packaging Materials,e,0.25",
            # Refunds count.
            "X6,A,2026-01-01,5200,Contract Labor,f,10.00",
            "X7,C,2026-01-01,5200,Contract Labor,g,-4.00",
            # A total that rounds to zero is shown as 0, not -0.
            "X8,A,2026-01-01,6100,Utilities,h,-0.40",
        ],
    )
    result = run("report", "--by", "account", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "account_code;account_name;total",
        "4100;Freight In;2",
        "4200;Duty and Brokerage;4",
        "4300;Storage;1240",
        "5100;Packaging Materials;884",
        "5200;Contract Labor;6",
        "6100;Utilities;0",
    ]


def test_report_accepts_include_refunds_and_it_changes_nothing(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    plain = run("report", "--by", "account", "--records", str(out))
    flagged = run("report", "--by", "account", "--records", str(out), "--include-refunds")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_report_requires_by(tmp_path: Path) -> None:
    result = run("report", "--records", str(tmp_path / "records.csv"))
    assert result.returncode == 2


# --- reconcile ---------------------------------------------------------------


def test_reconcile_samples_finds_the_4200_february_mismatch(tmp_path: Path) -> None:
    out = ingest_samples(tmp_path)
    result = run("reconcile", "--records", str(out))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-" in lines
    body = lines[:-1]
    assert all(line.startswith("MISMATCH ") for line in body)
    assert lines[-1] == f"mismatches={len(body)}"
    order = [(line.split()[1], line.split()[2]) for line in body]
    assert order == sorted(order)


def test_reconcile_tolerance_is_strict_and_refunds_count(tmp_path: Path) -> None:
    records = write_normalized(
        tmp_path / "records.csv",
        [
            # Spread exactly 0.05: agrees at the default tolerance.
            "R1,A,2026-01-05,4100,Freight In,x,100.00",
            "R2,B,2026-01-06,4100,Freight In,x,100.05",
            # Spread 0.06: disagrees.
            "R3,A,2026-01-05,4200,Duty and Brokerage,x,100.00",
            "R4,C,2026-01-07,4200,Duty and Brokerage,x,100.06",
            # Only one system posted: never reported.
            "R5,A,2026-01-05,4300,Storage,x,999.00",
            # The refund brings A to 40.00.
            "R6,A,2026-01-05,4400,X,x,50.00",
            "R7,A,2026-01-20,4400,X,x,-10.00",
            "R8,B,2026-01-09,4400,X,x,50.00",
        ],
    )
    result = run("reconcile", "--records", str(records))
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        "MISMATCH 4200 2026-01 spread=0.06 A=100.00 B=- C=100.06",
        "MISMATCH 4400 2026-01 spread=10.00 A=40.00 B=50.00 C=-",
        "mismatches=2",
    ]

    wide = run("reconcile", "--records", str(records), "--tolerance", "0.06")
    assert wide.stdout.splitlines()[-1] == "mismatches=1"

    exact = run("reconcile", "--records", str(records), "--tolerance", "0")
    assert exact.stdout.splitlines()[0] == "MISMATCH 4100 2026-01 spread=0.05 A=100.00 B=100.05 C=-"
    assert exact.stdout.splitlines()[-1] == "mismatches=3"


def test_reconcile_rejects_a_non_numeric_tolerance(tmp_path: Path) -> None:
    result = run("reconcile", "--records", str(tmp_path / "records.csv"), "--tolerance", "lots")
    assert result.returncode == 2
    assert "tolerance" in result.stderr


# --- validate ----------------------------------------------------------------


def test_validate_accepts_the_samples() -> None:
    result = run("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert "WARNING" not in result.stderr


def test_validate_checks_every_row(tmp_path: Path) -> None:
    ardent = tmp_path / "ardent.csv"
    ardent.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Rebill, ""Q1"", carrier",239.55,USD\n'
        "A-2,2026-13-01,4100,Bad date,1.00,USD\n"
        "A-3,2026-01-03,4100,Too many,fields,1.00,USD\n"
        "A-4,2026-01-03,4100,Bad amount,1.0x,USD\n"
        "A-5,2026-01-03,41A0,Bad account,1.00,USD\n"
        "A-6,2026-01-03,4100,Fine,-1.00,USD\n",
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
        "C-1,13/01/2026,4100,Day first is fine,1.00,USD\n"
        "C-2,01/13/2026,4100,Month first is not,1.00,USD\n"
        "== 2 rows ==\n",
        encoding="utf-8",
    )
    result = run("validate", str(ardent), str(borough), str(calder))
    assert result.returncode == 2
    assert result.stdout == "checked=10 rejected=6\n"

    warnings = [line for line in result.stderr.splitlines() if line.startswith("LEDGERKIT WARNING")]
    assert len(warnings) == 6
    expected = [
        ("ardent.csv", "line 4"),
        ("ardent.csv", "line 5"),
        ("ardent.csv", "line 6"),
        ("ardent.csv", "line 7"),
        ("borough.csv", "line 3"),
        ("calder.csv", "line 4"),
    ]
    for warning, (name, line) in zip(warnings, expected, strict=True):
        assert name in warning and f"{line}:" in warning, warning
    assert "expected 6 fields, found 7" in warnings[1]


def test_validate_exits_2_when_a_file_cannot_be_read(tmp_path: Path) -> None:
    missing = run("validate", str(tmp_path / "nope.csv"))
    assert missing.returncode == 2
    assert missing.stdout == "checked=0 rejected=0\n"

    bogus = tmp_path / "bogus.csv"
    bogus.write_text("not,an,export\n", encoding="utf-8")
    unknown = run("validate", str(bogus), str(SAMPLES / "system_b_export.csv"))
    assert unknown.returncode == 2
    assert unknown.stdout == "checked=39 rejected=0\n"


def test_validate_writes_nothing(tmp_path: Path) -> None:
    result = run("validate", *SAMPLE_FILES, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []


# --- --config ----------------------------------------------------------------


def test_config_overrides_settings_for_one_run(tmp_path: Path) -> None:
    before = config_digest()
    override = tmp_path / "quarter-close.toml"
    override.write_text(
        '[report]\ndecimals = 2\nunknown_account_label = "TBD"\n\n[reconcile]\ntolerance = 1000000\n',
        encoding="utf-8",
    )

    version = run("--config", str(override), "version")
    assert version.returncode == 0, version.stderr
    assert f"settings={override}" in version.stdout.splitlines()

    out = tmp_path / "records.csv"
    ingest = run("--config", str(override), "ingest", *SAMPLE_FILES, "--out", str(out))
    assert ingest.returncode == 0, ingest.stderr
    rows = {row["record_id"]: row for row in read_output(out)}
    assert rows["A-10040"]["account_name"] == "TBD"

    report = run("--config", str(override), "report", "--by", "month", "--records", str(out))
    assert report.returncode == 0, report.stderr
    assert all(len(line.split(";")[1].split(".")[1]) == 2 for line in report.stdout.splitlines()[1:])

    reconcile = run("--config", str(override), "reconcile", "--records", str(out))
    assert reconcile.stdout == "mismatches=0\n"

    strict = tmp_path / "strict.toml"
    strict.write_text('[validate]\naccount_code_pattern = "^4[0-9]{3}$"\n', encoding="utf-8")
    validate = run("--config", str(strict), "validate", str(SAMPLES / "system_b_export.csv"))
    assert validate.returncode == 2

    assert config_digest() == before
    assert not (REPO / ".ledgerkit-cache").exists()


def test_without_config_the_checked_in_settings_apply() -> None:
    result = run("version")
    assert result.stdout.splitlines()[1] == f"settings={REPO / 'config' / 'settings.toml'}"
