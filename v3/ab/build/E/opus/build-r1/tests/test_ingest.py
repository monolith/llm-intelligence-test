"""Tests for ``ledgerkit ingest``."""

from __future__ import annotations

import csv
from pathlib import Path

from conftest import SAMPLE_FILES, SAMPLES, Runner

HEADER = "record_id,source_system,date,account_code,account_name,description,amount"


def read_output(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ingest_writes_every_sample_posting(ledgerkit: Runner, tmp_path: Path) -> None:
    result = ledgerkit("ingest", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "wrote=120 to out/records.csv\n"

    out = tmp_path / "out" / "records.csv"
    assert out.read_text(encoding="utf-8").splitlines()[0] == HEADER
    rows = read_output(out)
    assert len(rows) == 120
    assert sum(1 for row in rows if row["source_system"] == "A") == 42
    assert sum(1 for row in rows if row["source_system"] == "B") == 39
    assert sum(1 for row in rows if row["source_system"] == "C") == 39
    assert sum(1 for row in rows if row["amount"].startswith("-")) == 5


def test_ingest_orders_by_date_then_system_then_id(ingested: Path) -> None:
    rows = read_output(ingested)
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in rows]
    assert keys == sorted(keys)


def test_ingest_converts_each_system(ingested: Path) -> None:
    rows = {row["record_id"]: row for row in read_output(ingested)}
    # A: decimal dollars, quoted memo preserved exactly.
    assert rows["A-10001"]["description"] == 'Rebill, "Q1 true-up", carrier'
    assert rows["A-10001"]["amount"] == "239.55"
    # B: integer cents become dollars.
    assert rows["B-2201"]["amount"] == "254.40"
    assert rows["B-2201"]["date"] == "2026-01-07"
    # C: dates are day first.
    assert rows["C-0409"]["date"] == "2026-01-15"
    assert rows["C-0401"]["date"] == "2026-01-02"
    # Account names come from the map; 5200 is Contract Labor, unknown codes get the label.
    assert rows["C-0438"]["account_code"] == "8800"
    assert rows["C-0438"]["account_name"] == "UNCLASSIFIED"
    assert {row["account_name"] for row in rows.values() if row["account_code"] == "5200"} == {"Contract Labor"}


def test_ingest_quotes_descriptions_that_need_it(ingested: Path) -> None:
    text = ingested.read_text(encoding="utf-8")
    assert 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55\n' in text


def test_ingest_keeps_duplicates_refunds_and_whitespace(ledgerkit: Runner, tmp_path: Path) -> None:
    export = tmp_path / "b.csv"
    export.write_text(
        "sys,doc_no,value_date,acct,descr,amount,cur\n"
        "B,B-1,2026-01-07,4100,Two  spaces,100,USD\n"
        "B,B-1,2026-01-07,4100,Two  spaces,100,USD\n"
        "B,B-2,2026-01-06,4100,Refund,-8825,USD\n",
        encoding="utf-8",
    )
    result = ledgerkit("ingest", str(export), "--out", "nested/dir/records.csv")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "wrote=3 to nested/dir/records.csv\n"
    rows = read_output(tmp_path / "nested" / "dir" / "records.csv")
    assert [row["record_id"] for row in rows] == ["B-2", "B-1", "B-1"]
    assert rows[0]["amount"] == "-88.25"
    assert rows[1]["description"] == "Two  spaces"


def test_ingest_fails_on_an_unreadable_file(ledgerkit: Runner, tmp_path: Path) -> None:
    result = ledgerkit("ingest", str(SAMPLES / "system_a_export.csv"), str(tmp_path / "missing.csv"))
    assert result.returncode != 0
    assert result.stdout == ""
    assert "missing.csv" in result.stderr
    assert not (tmp_path / "out").exists()
