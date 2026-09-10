"""Unit tests for report rounding and the reconcile comparison."""

from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit.core.records import Record  # noqa: E402
from ledgerkit.reports import find_mismatches, format_mismatch, round_total  # noqa: E402


@pytest.mark.parametrize(
    ("exact", "shown"),
    [("2.50", "2"), ("3.50", "4"), ("1240.50", "1240"), ("883.50", "884"), ("-2.50", "-2")],
)
def test_round_total_is_half_even(exact: str, shown: str) -> None:
    assert str(round_total(Decimal(exact), 0)) == shown


def test_round_total_never_gives_negative_zero() -> None:
    assert str(round_total(Decimal("-0.40"), 0)) == "0"


def record(system: str, code: str, amount: str) -> Record:
    return Record(
        record_id=f"{system}-1",
        source_system=system,
        date=date(2026, 1, 5),
        account_code=code,
        account_name="x",
        description="x",
        amount=Decimal(amount),
    )


def test_single_system_combinations_are_not_compared() -> None:
    assert find_mismatches([record("A", "4100", "100.00")], Decimal("0.05")) == []


def test_refunds_count_toward_reconciliation() -> None:
    records = [record("A", "4100", "100.00"), record("B", "4100", "100.00"), record("B", "4100", "-10.00")]
    [mismatch] = find_mismatches(records, Decimal("0.05"))
    assert format_mismatch(mismatch) == "MISMATCH 4100 2026-01 spread=10.00 A=100.00 B=90.00 C=-"
