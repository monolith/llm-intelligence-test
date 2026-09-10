"""Totals and cross-system comparisons over normalized records.

Everything here works on :class:`~ledgerkit.core.records.Record` values read back
from the normalized file, never on the exports themselves.  Totals are kept
exact while they are added up and are rounded once, half to even, when they are
laid out for display; see ``docs/CONVENTIONS.md``.

The functions that produce lines return them; printing is the command line's job.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

from ledgerkit.config import Settings
from ledgerkit.core import fields
from ledgerkit.core.records import Record
from ledgerkit.parsers import SYSTEMS

REPORT_SEPARATOR = ";"
MISSING_TOTAL = "-"
RECONCILE_DECIMALS = 2


@dataclass(frozen=True)
class AccountTotal:
    """The total of every posting to one account code."""

    account_code: str
    account_name: str
    total: Decimal


@dataclass(frozen=True)
class MonthTotal:
    """The total of every posting in one ``YYYY-MM`` month."""

    month: str
    total: Decimal


@dataclass(frozen=True)
class Mismatch:
    """An account and month on which the systems that posted to it disagree.

    ``totals`` holds one total per system letter that posted to the combination;
    a system that did not post to it has no entry.
    """

    account_code: str
    month: str
    spread: Decimal
    totals: Mapping[str, Decimal]


def round_total(value: Decimal, decimals: int) -> Decimal:
    """Round a total to ``decimals`` places, half to even.

    A total that rounds to zero comes back as plain zero, never negative zero.
    """
    rounded = value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)
    if rounded == 0:
        return rounded.copy_abs()
    return rounded


def totals_by_account(records: Iterable[Record]) -> list[AccountTotal]:
    """Total the records by account code, codes ascending.

    Every record counts, refunds included.  The account name is the one the
    normalized file carries for the code.
    """
    totals: dict[str, Decimal] = defaultdict(Decimal)
    names: dict[str, str] = {}
    for record in records:
        totals[record.account_code] += record.amount
        names.setdefault(record.account_code, record.account_name)
    return [AccountTotal(code, names[code], totals[code]) for code in sorted(totals)]


def totals_by_month(records: Iterable[Record]) -> list[MonthTotal]:
    """Total the records by posting month, months ascending.  Refunds count."""
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for record in records:
        totals[record.month()] += record.amount
    return [MonthTotal(month, totals[month]) for month in sorted(totals)]


def find_mismatches(records: Iterable[Record], tolerance: Decimal) -> list[Mismatch]:
    """Find the account and month combinations the systems disagree on.

    Postings are totalled per account code, month and system, refunds included.
    Only combinations at least two systems posted to are compared, and one is a
    mismatch when its largest system total minus its smallest is greater than
    ``tolerance``.  Results come back ordered by account code, then month.
    """
    groups: dict[tuple[str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for record in records:
        groups[(record.account_code, record.month())][record.source_system] += record.amount

    mismatches: list[Mismatch] = []
    for (code, month), by_system in sorted(groups.items()):
        if len(by_system) < 2:
            continue
        spread = max(by_system.values()) - min(by_system.values())
        if spread > tolerance:
            mismatches.append(Mismatch(code, month, spread, dict(by_system)))
    return mismatches


def _report_line(values: list[str]) -> str:
    return fields.join_record(values, REPORT_SEPARATOR)


def account_report(totals: Iterable[AccountTotal], settings: Settings) -> list[str]:
    """The lines of ``report --by account``: a header, then one line per account."""
    lines = [_report_line(["account_code", "account_name", "total"])]
    for item in totals:
        shown = settings.format_amount(round_total(item.total, settings.decimals))
        lines.append(_report_line([item.account_code, item.account_name, shown]))
    return lines


def month_report(totals: Iterable[MonthTotal], settings: Settings) -> list[str]:
    """The lines of ``report --by month``: a header, then one line per month."""
    lines = [_report_line(["month", "total"])]
    for item in totals:
        shown = settings.format_amount(round_total(item.total, settings.decimals))
        lines.append(_report_line([item.month, shown]))
    return lines


def _cents(value: Decimal) -> str:
    return f"{round_total(value, RECONCILE_DECIMALS):.{RECONCILE_DECIMALS}f}"


def format_mismatch(mismatch: Mismatch) -> str:
    """One ``MISMATCH`` line, with ``-`` for a system that did not post."""
    amounts = " ".join(
        f"{system}={_cents(mismatch.totals[system])}"
        if system in mismatch.totals
        else f"{system}={MISSING_TOTAL}"
        for system in SYSTEMS
    )
    return f"MISMATCH {mismatch.account_code} {mismatch.month} spread={_cents(mismatch.spread)} {amounts}"
