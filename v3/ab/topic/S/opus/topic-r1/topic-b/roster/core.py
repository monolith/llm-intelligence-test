"""Parsing, conflict detection and hour totals for a plain-text shift roster."""

from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

# ASCII digits only: ``\d`` would also accept other Unicode digits.
_DATE_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_RANGE_RE = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})")


class RosterError(ValueError):
    """A malformed roster line, identified by its 1-based line number."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(line, reason)
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


@dataclass(frozen=True)
class Shift:
    """One roster line: who works, on which date, from when to when."""

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
        """When the shift ends; the next day when ``end`` is before ``start``."""
        end = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end += dt.timedelta(days=1)
        return end


def _parse_date(text: str) -> dt.date | None:
    match = _DATE_RE.fullmatch(text)
    if match is None:
        return None
    try:
        return dt.date(int(match[1]), int(match[2]), int(match[3]))
    except ValueError:
        return None


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _RANGE_RE.fullmatch(text)
    if match is None:
        return None
    start_h, start_m, end_h, end_m = (int(group) for group in match.groups())
    if start_h > 23 or end_h > 23 or start_m > 59 or end_m > 59:
        return None
    return dt.time(start_h, start_m), dt.time(end_h, end_m)


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text into shifts, in line order.

    Raises :class:`RosterError` on the first malformed line.
    """
    shifts: list[Shift] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(number, "bad line")
        date = _parse_date(parts[0])
        if date is None:
            raise RosterError(number, "bad date")
        times = _parse_range(parts[1])
        if times is None:
            raise RosterError(number, "bad time")
        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(number, "missing name")
        shifts.append(Shift(date=date, start=times[0], end=times[1], name=name, line=number))
    return shifts


def _order(shift: Shift) -> tuple[dt.datetime, int]:
    return (shift.start_at, shift.line)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every pair of one person's shifts that overlap by more than an instant.

    Each pair holds the shift with the smaller ``(start_at, line)`` first, and
    the list is sorted by ``(a.name, a.start_at, a.line, b.start_at, b.line)``.
    """
    by_name: dict[str, list[Shift]] = defaultdict(list)
    for shift in shifts:
        by_name[shift.name].append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        group.sort(key=_order)
        for i, first in enumerate(group):
            first_start, first_end = first.start_at, first.end_at
            for j in range(i + 1, len(group)):
                second = group[j]
                # The group is sorted by start, so once one later shift starts
                # at or after ``first`` ends, none of the ones after it overlap.
                if second.start_at >= first_end:
                    break
                if first_start < second.end_at:
                    pairs.append((first, second))

    pairs.sort(key=lambda pair: (pair[0].name, *_order(pair[0]), *_order(pair[1])))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded once to 2 places, keyed in name order."""
    totals: dict[str, dt.timedelta] = defaultdict(dt.timedelta)
    for shift in shifts:
        totals[shift.name] += shift.end_at - shift.start_at
    return {name: round(totals[name].total_seconds() / 3600, 2) for name in sorted(totals)}
