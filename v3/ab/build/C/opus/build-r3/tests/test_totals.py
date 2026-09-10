"""Unit tests for the report and reconcile arithmetic."""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.config import Settings  # noqa: E402
from ledgerkit.core.records import Record  # noqa: E402
from ledgerkit.reconcile import reconcile_lines  # noqa: E402
from ledgerkit.report import report_lines, round_total  # noqa: E402


def settings(decimals: int = 0, label: str = "UNCLASSIFIED") -> Settings:
    return Settings(
        decimals=decimals,
        unknown_account_label=label,
        tolerance=Decimal("0.05"),
        account_code_pattern="^[0-9]{4}$",
        source_path=Path("test.toml"),
    )


def record(record_id: str, system: str, day: date, code: str, amount: str, name: str = "Name") -> Record:
    return Record(
        record_id=record_id,
        source_system=system,
        date=day,
        account_code=code,
        account_name=name,
        description="",
        amount=Decimal(amount),
    )


def test_round_total_rounds_half_to_even() -> None:
    assert round_total(Decimal("2.50"), 0) == Decimal("2")
    assert round_total(Decimal("3.50"), 0) == Decimal("4")
    assert round_total(Decimal("1240.50"), 0) == Decimal("1240")
    assert round_total(Decimal("883.50"), 0) == Decimal("884")
    assert round_total(Decimal("0.125"), 2) == Decimal("0.12")


def test_round_total_never_shows_negative_zero() -> None:
    assert settings().format_amount(round_total(Decimal("-0.40"), 0)) == "0"
    assert settings(2).format_amount(round_total(Decimal("-0.004"), 2)) == "0.00"


def test_report_rounds_the_total_not_the_postings() -> None:
    # Three postings of 0.50 each: rounding each first would give 0 + 0 + 0.
    rows = [record(f"A-{n}", "A", date(2026, 1, n), "4100", "0.50") for n in (1, 2, 3)]
    assert report_lines(rows, "month", settings()) == ["month;total", "2026-01;2"]


def test_report_honours_decimals() -> None:
    rows = [record("A-1", "A", date(2026, 1, 1), "4100", "10.25")]
    assert report_lines(rows, "month", settings(2))[1] == "2026-01;10.25"
    assert report_lines(rows, "month", settings(1))[1] == "2026-01;10.2"


def test_report_quotes_a_name_that_contains_the_delimiter() -> None:
    rows = [record("A-1", "A", date(2026, 1, 1), "8800", "5.00", name="Unknown; review")]
    assert report_lines(rows, "account", settings())[1] == '8800;"Unknown; review";5'


def test_reconcile_ignores_combinations_only_one_system_posted_to() -> None:
    rows = [
        record("A-1", "A", date(2026, 1, 5), "4100", "100.00"),
        record("A-2", "A", date(2026, 2, 5), "4100", "999.00"),
        record("B-1", "B", date(2026, 1, 9), "4100", "90.00"),
    ]
    assert reconcile_lines(rows, Decimal("0.05")) == [
        "MISMATCH 4100 2026-01 spread=10.00 A=100.00 B=90.00 C=-",
        "mismatches=1",
    ]


def test_reconcile_counts_refunds_and_orders_by_account_then_month() -> None:
    rows = [
        record("C-1", "C", date(2026, 3, 1), "5100", "10.00"),
        record("A-1", "A", date(2026, 3, 2), "5100", "10.00"),
        record("A-2", "A", date(2026, 3, 3), "5100", "-4.00"),
        record("A-3", "A", date(2026, 1, 3), "5100", "1.00"),
        record("B-3", "B", date(2026, 1, 3), "5100", "2.00"),
        record("A-4", "A", date(2026, 1, 3), "4100", "1.00"),
        record("C-4", "C", date(2026, 1, 3), "4100", "3.00"),
    ]
    assert reconcile_lines(rows, Decimal("0")) == [
        "MISMATCH 4100 2026-01 spread=2.00 A=1.00 B=- C=3.00",
        "MISMATCH 5100 2026-01 spread=1.00 A=1.00 B=2.00 C=-",
        "MISMATCH 5100 2026-03 spread=4.00 A=6.00 B=- C=10.00",
        "mismatches=3",
    ]
