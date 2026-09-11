"""Shift-roster checker.

Reads a small plain-text roster, finds scheduling conflicts, and totals hours
per person. See ``SPEC-B.md`` for the roster format, the public API, and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Iterable
from dataclasses import dataclass

__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_TIME_RANGE_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


@dataclass(frozen=True)
class Shift:
    """One shift, as read from a roster line."""

    date: datetime.date
    start: datetime.time
    end: datetime.time
    name: str
    line: int

    @property
    def start_at(self) -> datetime.datetime:
        """The moment the shift starts."""
        return datetime.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime.datetime:
        """The moment the shift ends, one day later than ``date`` when it crosses midnight."""
        end_at = datetime.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += datetime.timedelta(days=1)
        return end_at


class RosterError(ValueError):
    """Raised when a roster line cannot be parsed."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


def _parse_date(text: str, line: int) -> datetime.date:
    match = _DATE_RE.match(text)
    if not match:
        raise RosterError(line, "bad date")
    year, month, day = (int(part) for part in match.groups())
    try:
        return datetime.date(year, month, day)
    except ValueError:
        raise RosterError(line, "bad date") from None


def _parse_time_range(text: str, line: int) -> tuple[datetime.time, datetime.time]:
    match = _TIME_RANGE_RE.match(text)
    if not match:
        raise RosterError(line, "bad time")
    start_hour, start_minute, end_hour, end_minute = (int(part) for part in match.groups())
    try:
        start = datetime.time(start_hour, start_minute)
        end = datetime.time(end_hour, end_minute)
    except ValueError:
        raise RosterError(line, "bad time") from None
    return start, end


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster's text into an ordered list of :class:`Shift`.

    Raises :class:`RosterError` on the first malformed line and parses no
    further.
    """
    shifts: list[Shift] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_number, "bad line")

        date = _parse_date(parts[0], line_number)
        start, end = _parse_time_range(parts[1], line_number)

        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(line_number, "missing name")

        shifts.append(Shift(date=date, start=start, end=end, name=name, line=line_number))
    return shifts


def _ordered_pair(a: Shift, b: Shift) -> tuple[Shift, Shift]:
    return (a, b) if (a.start_at, a.line) <= (b.start_at, b.line) else (b, a)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Return every pair of overlapping shifts belonging to the same person."""
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    conflicts: list[tuple[Shift, Shift]] = []
    for same_person in by_name.values():
        for i in range(len(same_person)):
            for j in range(i + 1, len(same_person)):
                a, b = same_person[i], same_person[j]
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    conflicts.append(_ordered_pair(a, b))

    conflicts.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return conflicts


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours worked per person, rounded once at the end."""
    totals: dict[str, float] = {}
    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600
        totals[shift.name] = totals.get(shift.name, 0.0) + duration
    return {name: round(totals[name], 2) for name in sorted(totals)}
