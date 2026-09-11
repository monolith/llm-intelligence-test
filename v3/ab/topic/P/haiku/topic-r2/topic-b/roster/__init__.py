"""Shift-roster checker.

Public API: Shift, RosterError, parse_roster, find_conflicts, hours_by_person.
CLI: python -m roster check <file>
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


class RosterError(ValueError):
    """Raised when parsing a roster line fails."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")


@dataclass(frozen=True)
class Shift:
    """One shift in the roster."""

    date: date
    start: time
    end: time
    name: str
    line: int

    @property
    def start_at(self) -> datetime:
        """Start as a datetime."""
        return datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime:
        """End as a datetime, adjusted for midnight crossing."""
        end_date = self.date if self.end >= self.start else self.date + timedelta(days=1)
        return datetime.combine(end_date, self.end)


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster text into shifts.

    Raises RosterError on the first malformed line.
    """
    shifts: list[Shift] = []

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped[0] == "#":
            continue

        # Split into at most 3 parts: date, time range, name
        parts = stripped.split(None, 2)

        # Check for bad line
        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_range_str = parts[0], parts[1]

        # Parse date
        try:
            parsed_date = _parse_date(date_str)
        except ValueError:
            raise RosterError(line_num, "bad date")

        # Parse time range
        try:
            start_time, end_time = _parse_time_range(time_range_str)
        except ValueError:
            raise RosterError(line_num, "bad time")

        # Get name
        name = parts[2].strip() if len(parts) > 2 else ""
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(Shift(date=parsed_date, start=start_time, end=end_time, name=name, line=line_num))

    return shifts


def _parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD format."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError("bad date format")
    try:
        year, month, day = map(int, date_str.split("-"))
        return date(year, month, day)
    except ValueError:
        raise ValueError("invalid date")


def _parse_time_range(time_range_str: str) -> tuple[time, time]:
    """Parse HH:MM-HH:MM format."""
    if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", time_range_str):
        raise ValueError("bad time format")

    start_str, end_str = time_range_str.split("-")
    start_hour, start_min = map(int, start_str.split(":"))
    end_hour, end_min = map(int, end_str.split(":"))

    if not (0 <= start_hour <= 23 and 0 <= start_min <= 59):
        raise ValueError("invalid start time")
    if not (0 <= end_hour <= 23 and 0 <= end_min <= 59):
        raise ValueError("invalid end time")

    return time(start_hour, start_min), time(end_hour, end_min)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find all conflicting shifts for the same person."""
    shifts_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    # Group shifts by name
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts_list:
        if shift.name not in by_name:
            by_name[shift.name] = []
        by_name[shift.name].append(shift)

    # Find conflicts within each person
    for name in sorted(by_name.keys()):
        person_shifts = by_name[name]
        for i, shift_a in enumerate(person_shifts):
            for shift_b in person_shifts[i + 1 :]:
                if _shifts_overlap(shift_a, shift_b):
                    # Order by (start_at, line)
                    if (shift_a.start_at, shift_a.line) < (shift_b.start_at, shift_b.line):
                        conflicts.append((shift_a, shift_b))
                    else:
                        conflicts.append((shift_b, shift_a))

    # Sort conflicts by (name, start_at, line, end_start_at, end_line)
    conflicts.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))

    return conflicts


def _shifts_overlap(shift_a: Shift, shift_b: Shift) -> bool:
    """Check if two shifts of the same person overlap."""
    return shift_a.start_at < shift_b.end_at and shift_b.start_at < shift_a.end_at


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person."""
    totals: dict[str, float] = {}

    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        if shift.name not in totals:
            totals[shift.name] = 0.0
        totals[shift.name] += duration

    # Round each person's total once at the end
    result: dict[str, float] = {}
    for name in sorted(totals.keys()):
        result[name] = round(totals[name], 2)

    return result


__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
