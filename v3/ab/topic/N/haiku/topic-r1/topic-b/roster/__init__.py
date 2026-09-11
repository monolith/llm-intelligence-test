"""Shift-roster checker."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable


class RosterError(ValueError):
    """Raised when parsing a roster line fails."""

    def __init__(self, line: int, reason: str):
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


@dataclass(frozen=True)
class Shift:
    """A single shift assignment."""

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
        end_datetime = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_datetime += dt.timedelta(days=1)
        return end_datetime


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text and return list of shifts.

    Raises RosterError on the first malformed line.
    """
    shifts = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        line = line.strip()

        # Skip empty lines and comments
        if not line or line[0] == "#":
            continue

        # Split into at most 3 parts
        parts = line.split(None, 2)

        # Check for bad line (fewer than 2 parts)
        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_range = parts[0], parts[1]

        # Validate and parse date
        try:
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise RosterError(line_num, "bad date")

        # Validate and parse time range
        # Time range must be exactly HH:MM-HH:MM
        if len(time_range) != 11 or time_range[5] != "-":
            raise RosterError(line_num, "bad time")

        time_parts = time_range.split("-")
        if len(time_parts) != 2:
            raise RosterError(line_num, "bad time")

        try:
            start = dt.datetime.strptime(time_parts[0], "%H:%M").time()
            end = dt.datetime.strptime(time_parts[1], "%H:%M").time()
        except ValueError:
            raise RosterError(line_num, "bad time")

        # Extract and validate name
        if len(parts) < 3:
            raise RosterError(line_num, "missing name")

        name = parts[2].strip()
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(Shift(date=date, start=start, end=end, name=name, line=line_num))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find all overlapping shifts for the same person.

    Returns list of (shift1, shift2) tuples, sorted by (name, start_at, line, ...).
    """
    shifts_list = list(shifts)
    conflicts = []

    # For each pair of shifts
    for i, shift_a in enumerate(shifts_list):
        for shift_b in shifts_list[i + 1 :]:
            # Only check shifts for the same person
            if shift_a.name != shift_b.name:
                continue

            # Check for overlap: a.start_at < b.end_at and b.start_at < a.end_at
            if shift_a.start_at < shift_b.end_at and shift_b.start_at < shift_a.end_at:
                # Ensure shift with smaller (start_at, line) comes first
                if (shift_a.start_at, shift_a.line) <= (shift_b.start_at, shift_b.line):
                    conflicts.append((shift_a, shift_b))
                else:
                    conflicts.append((shift_b, shift_a))

    # Sort by (name, start_at, line, start_at, line)
    conflicts.sort(
        key=lambda pair: (
            pair[0].name,
            pair[0].start_at,
            pair[0].line,
            pair[1].start_at,
            pair[1].line,
        )
    )

    return conflicts


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Calculate total hours for each person.

    Returns dict with names as keys (sorted) and total hours as values.
    """
    hours_dict: dict[str, float] = {}

    for shift in shifts:
        duration = shift.end_at - shift.start_at
        hours = duration.total_seconds() / 3600.0

        if shift.name not in hours_dict:
            hours_dict[shift.name] = 0.0
        hours_dict[shift.name] += hours

    # Round each person's total once, then sort by name
    result = {}
    for name in sorted(hours_dict.keys()):
        result[name] = round(hours_dict[name], 2)

    return result
