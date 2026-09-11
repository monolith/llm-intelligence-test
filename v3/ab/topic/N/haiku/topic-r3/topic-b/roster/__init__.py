"""Shift-roster checker.

Public API: Shift, RosterError, parse_roster, find_conflicts, hours_by_person.
Command line: python -m roster check <file>
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import Iterable


class RosterError(ValueError):
    """Exception raised for roster parsing errors."""

    def __init__(self, line: int, reason: str):
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


@dataclass(frozen=True)
class Shift:
    """A single shift in the roster."""

    date: datetime.date
    start: datetime.time
    end: datetime.time
    name: str
    line: int

    @property
    def start_at(self) -> datetime.datetime:
        """Start of shift as a datetime."""
        return datetime.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime.datetime:
        """End of shift as a datetime, adjusting for midnight crossing."""
        end_date = self.date if self.end >= self.start else self.date + datetime.timedelta(days=1)
        return datetime.datetime.combine(end_date, self.end)


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text and return list of Shift objects.

    Raises RosterError on the first malformed line.
    """
    shifts: list[Shift] = []

    for line_num, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()

        if not stripped or stripped[0] == "#":
            continue

        parts = stripped.split(None, 2)

        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_str = parts[0], parts[1]

        # Parse date
        if not _is_valid_date(date_str):
            raise RosterError(line_num, "bad date")

        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

        # Parse time range
        if not _is_valid_time_range(time_str):
            raise RosterError(line_num, "bad time")

        start_str, end_str = time_str.split("-")
        start = datetime.datetime.strptime(start_str, "%H:%M").time()
        end = datetime.datetime.strptime(end_str, "%H:%M").time()

        # Parse name
        if len(parts) < 3:
            raise RosterError(line_num, "missing name")

        name = parts[2].strip()
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(Shift(date=date, start=start, end=end, name=name, line=line_num))

    return shifts


def _is_valid_date(date_str: str) -> bool:
    """Check if string is a valid YYYY-MM-DD date."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return False
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _is_valid_time_range(time_str: str) -> bool:
    """Check if string is a valid HH:MM-HH:MM time range."""
    if not re.match(r"^\d{2}:\d{2}-\d{2}:\d{2}$", time_str):
        return False
    try:
        start_str, end_str = time_str.split("-")
        datetime.datetime.strptime(start_str, "%H:%M")
        datetime.datetime.strptime(end_str, "%H:%M")
        return True
    except ValueError:
        return False


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find all conflicting shifts (overlapping shifts for the same person).

    Conflicts are determined by: a.start_at < b.end_at and b.start_at < a.end_at
    """
    shift_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    # Group shifts by person
    by_person: dict[str, list[Shift]] = {}
    for shift in shift_list:
        if shift.name not in by_person:
            by_person[shift.name] = []
        by_person[shift.name].append(shift)

    # Find conflicts within each person's shifts
    for name in by_person:
        person_shifts = by_person[name]
        for i, shift_a in enumerate(person_shifts):
            for shift_b in person_shifts[i + 1 :]:
                if shift_a.start_at < shift_b.end_at and shift_b.start_at < shift_a.end_at:
                    # Ensure the shift with smaller (start_at, line) comes first
                    if (shift_a.start_at, shift_a.line) <= (shift_b.start_at, shift_b.line):
                        conflicts.append((shift_a, shift_b))
                    else:
                        conflicts.append((shift_b, shift_a))

    # Sort conflicts by (name, a.start_at, a.line, b.start_at, b.line)
    conflicts.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))

    return conflicts


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Calculate total hours per person.

    Rounds once at the end to 2 decimal places.
    Keys are sorted by name.
    """
    shift_list = list(shifts)

    totals: dict[str, float] = {}
    for shift in shift_list:
        if shift.name not in totals:
            totals[shift.name] = 0.0

        # Calculate duration in hours
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        totals[shift.name] += duration

    # Round each person's total once at the end
    result = {}
    for name in sorted(totals.keys()):
        result[name] = round(totals[name], 2)

    return result


__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
