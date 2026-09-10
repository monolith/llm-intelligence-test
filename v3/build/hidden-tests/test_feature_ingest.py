"""Feature tests for `ingest`."""

from __future__ import annotations

from pathlib import Path

from conftest import SAMPLES, IngestRun, run_cli

EXPECTED_HEADER = "record_id,source_system,date,account_code,account_name,description,amount"
EXPECTED_RECORD_COUNT = 120

EXPECTED_REFUNDS = {
    "A-10019": "-125.00",
    "A-10023": "-151.75",
    "A-10037": "-42.00",
    "A-10041": "-31.20",
    "B-2221": "-88.25",
}

QUOTED_DESCRIPTION = 'Rebill, "Q1 true-up", carrier'
QUOTED_RAW_LINE = 'A-10001,A,2026-01-03,4100,Freight In,"Rebill, ""Q1 true-up"", carrier",239.55'


def test_ingest_writes_records_with_the_specified_header(ingested: IngestRun) -> None:
    assert ingested.records_path.is_file(), ingested.proc.stderr
    assert ingested.raw_lines[0] == EXPECTED_HEADER


def test_ingest_keeps_every_posting(ingested: IngestRun) -> None:
    assert len(ingested.rows) == EXPECTED_RECORD_COUNT
    assert f"wrote={EXPECTED_RECORD_COUNT}" in ingested.proc.stdout


def test_ingest_reads_system_b_amounts_as_dollars(ingested: IngestRun) -> None:
    assert ingested.by_id("B-2201")["amount"] == "254.40"
    assert ingested.by_id("B-2239")["amount"] == "57.25"


def test_ingest_reads_system_c_dates_day_first(ingested: IngestRun) -> None:
    assert ingested.by_id("C-0418")["date"] == "2026-02-03"
    assert ingested.by_id("C-0401")["date"] == "2026-01-02"
    assert ingested.by_id("C-0439")["date"] == "2026-03-10"


def test_ingest_keeps_refund_rows(ingested: IngestRun) -> None:
    found = {row["record_id"]: row["amount"] for row in ingested.rows if row["amount"].startswith("-")}
    assert found == EXPECTED_REFUNDS


def test_ingest_preserves_a_quoted_description(ingested: IngestRun) -> None:
    assert ingested.by_id("A-10001")["description"] == QUOTED_DESCRIPTION
    assert ingested.by_id("A-10002")["description"] == "Drayage, port apron to DC"


def test_ingest_names_account_5200_from_the_live_map(ingested: IngestRun) -> None:
    names = {row["account_name"] for row in ingested.rows if row["account_code"] == "5200"}
    assert names == {"Contract Labor"}


def test_ingest_labels_unmapped_account_codes(ingested: IngestRun) -> None:
    names = {row["account_name"] for row in ingested.rows if row["account_code"] == "8800"}
    assert names == {"UNCLASSIFIED"}


def test_ingest_orders_rows_by_date_then_system_then_id(ingested: IngestRun) -> None:
    assert ingested.rows, ingested.proc.stderr
    keys = [(row["date"], row["source_system"], row["record_id"]) for row in ingested.rows]
    assert keys == sorted(keys)


def test_ingest_reflects_a_changed_input_file(tmp_path: Path) -> None:
    work = tmp_path / "work"
    work.mkdir()
    export = work / "ardent.csv"
    export.write_text(
        (SAMPLES / "system_a_export.csv").read_text(encoding="utf-8"), encoding="utf-8"
    )

    first = run_cli(["ingest", str(export), "--out", "out/first.csv"], cwd=work)
    assert (work / "out" / "first.csv").is_file(), first.stderr
    before = len((work / "out" / "first.csv").read_text(encoding="utf-8").splitlines())

    with export.open("a", encoding="utf-8") as handle:
        handle.write("A-19999,2026-03-31,4100,Late inbound freight,10.00,USD\n")

    second = run_cli(["ingest", str(export), "--out", "out/second.csv"], cwd=work)
    assert (work / "out" / "second.csv").is_file(), second.stderr
    after = (work / "out" / "second.csv").read_text(encoding="utf-8")
    assert len(after.splitlines()) == before + 1
    assert "A-19999" in after


def test_records_file_stays_comma_separated(ingested: IngestRun) -> None:
    assert ";" not in ingested.raw_lines[0]
    assert QUOTED_RAW_LINE in ingested.raw_lines
