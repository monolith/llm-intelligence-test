"""Tests for ``ledgerkit validate``."""

from __future__ import annotations

from pathlib import Path

from conftest import SAMPLE_FILES, Runner


def test_validate_passes_the_samples(ledgerkit: Runner, tmp_path: Path) -> None:
    result = ledgerkit("validate", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "checked=120 rejected=0\n"
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


def test_validate_reports_every_bad_row(ledgerkit: Runner, tmp_path: Path) -> None:
    a = tmp_path / "a.csv"
    a.write_text(
        "# ARDENT LEDGER EXPORT\n"
        "entry_id,posted_on,account,memo,amount,currency\n"
        'A-1,2026-01-03,4100,"Rebill, ""Q1"", carrier",239.55,USD\n'  # line 3: fine
        "A-2,2026-13-03,4100,Bad month,1.00,USD\n"  # line 4: date
        "A-3,2026-01-03,4100,Too,many,fields,USD\n",  # line 5: field count
        encoding="utf-8",
    )
    b = tmp_path / "b.csv"
    b.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Fine,25440,USD\n"  # line 2: fine
        "B,B-2,2026-01-07,41A0,Bad account,100,USD\n"  # line 3: account
        "B,B-3,2026-01-07,4100,Dollars not cents,12.50,USD\n",  # line 4: amount
        encoding="utf-8",
    )
    c = tmp_path / "c.csv"
    c.write_text(
        "CALDER EXPORT v3\n"
        "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
        "C-1,15/01/2026,4100,Day first is fine,1.00,USD\n"  # line 3: fine
        "C-2,2026-01-15,4100,ISO is wrong here,1.00,USD\n"  # line 4: date
        "C-3,15/01/2026,4100,Not a number,abc,USD\n"  # line 5: amount
        "== 5 rows ==\n",
        encoding="utf-8",
    )
    result = ledgerkit("validate", str(a), str(b), str(c))
    assert result.returncode == 2
    assert result.stdout == "checked=9 rejected=6\n"

    warnings = result.stderr.splitlines()
    assert len(warnings) == 6
    assert all(line.startswith("LEDGERKIT WARNING ") for line in warnings)
    expected = [("a.csv", 4, "posted_on"), ("a.csv", 5, "expected 6 fields"), ("b.csv", 3, "acct"),
                ("b.csv", 4, "amount"), ("c.csv", 4, "txn_date"), ("c.csv", 5, "gross_amount")]
    for line, (name, number, reason) in zip(warnings, expected, strict=True):
        assert f"{name} line {number}:" in line
        assert reason in line


def test_validate_exits_2_when_a_file_cannot_be_read(ledgerkit: Runner, tmp_path: Path) -> None:
    unknown = tmp_path / "unknown.csv"
    unknown.write_text("what,is,this\n", encoding="utf-8")
    result = ledgerkit("validate", SAMPLE_FILES[0], str(tmp_path / "missing.csv"), str(unknown))
    assert result.returncode == 2
    assert result.stdout == "checked=42 rejected=0\n"
    assert "missing.csv" in result.stderr
    assert "unknown.csv" in result.stderr


def test_validate_uses_the_account_code_pattern_setting(ledgerkit: Runner, tmp_path: Path) -> None:
    override = tmp_path / "strict.toml"
    override.write_text('[validate]\naccount_code_pattern = "^[4-6][0-9]{3}$"\n', encoding="utf-8")
    result = ledgerkit("--config", str(override), "validate", *SAMPLE_FILES)
    assert result.returncode == 2
    # 8800 and 9000 no longer match.
    rejected = int(result.stdout.strip().split("rejected=")[1])
    assert rejected == result.stderr.count("does not match")
    assert rejected > 0
