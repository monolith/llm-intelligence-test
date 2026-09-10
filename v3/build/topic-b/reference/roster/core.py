"""Parsing, conflict detection and hour totals for the roster format."""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass

__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]

_ONE_DAY = dt.timedelta(days=1)


@dataclass(frozen=True)
class Shift:
    """One rostered shift, as written on one line."""

    date: dt.date
    start: dt.time
    end: dt.time
    name: str
    line: int

    @property
    def start_at(self) -> dt.datetime:
        return dt.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> dt.datetime:
        stamp = dt.datetime.combine(self.date, self.end)
        return stamp + _ONE_DAY if self.end < self.start else stamp

    @property
    def duration(self) -> dt.timedelta:
        return self.end_at - self.start_at


class RosterError(ValueError):
    """A roster line that does not fit the format."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


def _parse_date(field: str) -> dt.date | None:
    if len(field) != 10 or field[4] != "-" or field[7] != "-":
        return None
    year, month, day = field[:4], field[5:7], field[8:10]
    if not (year.isdigit() and month.isdigit() and day.isdigit()):
        return None
    try:
        return dt.date(int(year), int(month), int(day))
    except ValueError:
        return None


def _parse_time(field: str) -> dt.time | None:
    if len(field) != 5 or field[2] != ":":
        return None
    hour, minute = field[:2], field[3:5]
    if not (hour.isdigit() and minute.isdigit()):
        return None
    try:
        return dt.time(int(hour), int(minute))
    except ValueError:
        return None


def _parse_range(field: str) -> tuple[dt.time, dt.time] | None:
    if len(field) != 11 or field[5] != "-":
        return None
    start = _parse_time(field[:5])
    end = _parse_time(field[6:])
    if start is None or end is None:
        return None
    return start, end


def parse_roster(text: str) -> list[Shift]:
    """Turn roster text into shifts, in line order.

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
        span = _parse_range(parts[1])
        if span is None:
            raise RosterError(number, "bad time")
        name = parts[2].strip() if len(parts) > 2 else ""
        if not name:
            raise RosterError(number, "missing name")
        shifts.append(Shift(date=date, start=span[0], end=span[1], name=name, line=number))
    return shifts


def _overlap(a: Shift, b: Shift) -> bool:
    return a.start_at < b.end_at and b.start_at < a.end_at


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of same-person shifts whose times overlap."""
    by_person: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_person.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_person.values():
        ordered = sorted(group, key=lambda s: (s.start_at, s.line))
        for index, first in enumerate(ordered):
            for second in ordered[index + 1 :]:
                if _overlap(first, second):
                    pairs.append((first, second))

    pairs.sort(key=lambda p: (p[0].name, p[0].start_at, p[0].line, p[1].start_at, p[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded to two places once at the end."""
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + shift.duration
    return {name: round(totals[name].total_seconds() / 3600.0, 2) for name in sorted(totals)}
