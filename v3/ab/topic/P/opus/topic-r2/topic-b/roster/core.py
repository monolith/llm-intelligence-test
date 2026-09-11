"""Reading a roster, finding conflicting shifts, and totalling hours per person."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

BAD_LINE = "bad line"
BAD_DATE = "bad date"
BAD_TIME = "bad time"
MISSING_NAME = "missing name"

# [0-9] rather than \d: \d also matches non-ASCII digits.
_DATE_PATTERN = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_RANGE_PATTERN = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})")


class RosterError(ValueError):
    """A malformed roster line: its 1-based ``line`` number and the ``reason``."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(line, reason)
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


@dataclass(frozen=True)
class Shift:
    """One shift as written on one roster line."""

    date: dt.date
    start: dt.time
    end: dt.time
    name: str
    line: int

    @property
    def start_at(self) -> dt.datetime:
        """When the shift starts."""
        return dt.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> dt.datetime:
        """When the shift ends: the next day when ``end`` is earlier than ``start``."""
        end_at = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += dt.timedelta(days=1)
        return end_at


def _parse_date(text: str) -> dt.date | None:
    match = _DATE_PATTERN.fullmatch(text)
    if match is None:
        return None
    year, month, day = (int(group) for group in match.groups())
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _RANGE_PATTERN.fullmatch(text)
    if match is None:
        return None
    start_hour, start_minute, end_hour, end_minute = (int(group) for group in match.groups())
    if max(start_hour, end_hour) > 23 or max(start_minute, end_minute) > 59:
        return None
    return dt.time(start_hour, start_minute), dt.time(end_hour, end_minute)


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text into shifts, in line order.

    Blank lines and lines starting with ``#`` are skipped.  The first malformed
    line raises :class:`RosterError` and nothing after it is parsed.
    """
    shifts: list[Shift] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(number, BAD_LINE)
        day = _parse_date(parts[0])
        if day is None:
            raise RosterError(number, BAD_DATE)
        times = _parse_range(parts[1])
        if times is None:
            raise RosterError(number, BAD_TIME)
        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(number, MISSING_NAME)
        start, end = times
        shifts.append(Shift(date=day, start=start, end=end, name=name, line=number))
    return shifts


def _order(shift: Shift) -> tuple[dt.datetime, int]:
    return (shift.start_at, shift.line)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every pair of one person's shifts that overlap by more than an instant.

    Each unordered pair appears once, earlier ``(start_at, line)`` first, and the
    list is sorted by ``(a.name, a.start_at, a.line, b.start_at, b.line)``.
    """
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        group.sort(key=_order)
        for index, first in enumerate(group):
            first_end = first.end_at
            for second in group[index + 1 :]:
                # Sorted by start, so once one starts at or after first ends,
                # every later one does too.
                if second.start_at >= first_end:
                    break
                if first.start_at < second.end_at:
                    pairs.append((first, second))

    pairs.sort(key=lambda pair: (pair[0].name, *_order(pair[0]), *_order(pair[1])))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded once to two places, keyed in name order."""
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + (shift.end_at - shift.start_at)
    return {name: round(totals[name] / dt.timedelta(hours=1), 2) for name in sorted(totals)}
