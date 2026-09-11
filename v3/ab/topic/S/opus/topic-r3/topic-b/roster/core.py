"""Parsing, conflict detection and hour totals for a plain-text shift roster."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_RANGE_RE = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})")


class RosterError(ValueError):
    """A malformed roster line."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(line, reason)
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


@dataclass(frozen=True)
class Shift:
    """One shift, as read from one roster line."""

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
    if not _DATE_RE.fullmatch(text):
        return None
    try:
        return dt.date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return None


def _parse_time(hours: str, minutes: str) -> dt.time | None:
    hour, minute = int(hours), int(minutes)
    if hour > 23 or minute > 59:
        return None
    return dt.time(hour, minute)


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _RANGE_RE.fullmatch(text)
    if match is None:
        return None
    start = _parse_time(match.group(1), match.group(2))
    end = _parse_time(match.group(3), match.group(4))
    if start is None or end is None:
        return None
    return start, end


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


def _order_key(shift: Shift) -> tuple[dt.datetime, int]:
    return (shift.start_at, shift.line)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every pair of one person's shifts that overlap by more than an instant."""
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        group.sort(key=_order_key)
        for i, a in enumerate(group):
            a_start, a_end = a.start_at, a.end_at
            for b in group[i + 1 :]:
                b_start = b.start_at
                # Sorted by start, so nothing later can start before ``a`` ends.
                if b_start >= a_end:
                    break
                if a_start < b.end_at:
                    pairs.append((a, b))

    pairs.sort(key=lambda p: (p[0].name, p[0].start_at, p[0].line, p[1].start_at, p[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded once to two places, keyed in name order."""
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + (shift.end_at - shift.start_at)
    return {name: round(totals[name].total_seconds() / 3600, 2) for name in sorted(totals)}
