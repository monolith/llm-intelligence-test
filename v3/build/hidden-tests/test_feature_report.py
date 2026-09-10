"""Feature tests for `report`.

Only the delimiter test cares which delimiter the report uses.  The others read
the line whichever way it was written, so that a wrong delimiter costs one item
rather than all of them.
"""

from __future__ import annotations

from conftest import IngestRun, run_cli

# Totals with refunds counted in, rounded to whole dollars.
ACCOUNT_TOTALS = {
    "4100": "6248",
    "4200": "2971",
    "4300": "2886",
    "5100": "3400",
    "5200": "1748",
    "5300": "1621",
    "6100": "3577",
    "6200": "4400",
    "8800": "315",
    "9000": "417",
}

MONTH_TOTALS = {"2026-01": "13256", "2026-02": "8456", "2026-03": "5870"}

# The three accounts that carry refunds.  Leaving refunds out gives 3765, 3619, 346.
REFUND_BEARING = {"5100": "3400", "6100": "3577", "8800": "315"}


def _fields(line: str) -> list[str]:
    return line.split(";") if ";" in line else line.split(",")


def _report(ingested: IngestRun, *args: str) -> list[str]:
    proc = run_cli(["report", *args, "--records", str(ingested.records_path)], cwd=ingested.work)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout.splitlines()


def _totals(lines: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in lines[1:]:
        parts = _fields(line)
        if len(parts) < 2:
            continue
        out[parts[0]] = parts[-1]
    return out


def test_report_by_account_uses_the_semicolon_delimiter(ingested: IngestRun) -> None:
    lines = _report(ingested, "--by", "account")
    assert lines[0] == "account_code;account_name;total"
    assert all(line.count(";") == 2 for line in lines), lines


def test_report_by_account_totals_round_half_to_even(ingested: IngestRun) -> None:
    totals = _totals(_report(ingested, "--by", "account"))
    # 6248.50 goes down to the even 6248; 1747.50 goes up to the even 1748.
    assert totals.get("4100") == "6248"
    assert totals.get("5200") == "1748"


def test_report_by_account_counts_refunds_by_default(ingested: IngestRun) -> None:
    totals = _totals(_report(ingested, "--by", "account"))
    assert {code: totals.get(code) for code in REFUND_BEARING} == REFUND_BEARING


def test_report_by_month_totals(ingested: IngestRun) -> None:
    totals = _totals(_report(ingested, "--by", "month"))
    assert totals == MONTH_TOTALS
