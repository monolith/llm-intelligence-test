"""Shift-roster checker."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable


class RosterError(ValueError):
    """Raised when a roster line is malformed."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")


@dataclass(frozen=True)
class Shift:
    """One shift in a roster."""

    date: dt.date
    start: dt.time
    end: dt.time
    name: str
    line: int

    @property
    def start_at(self) -> dt.datetime:
        """Start as a datetime."""
        return dt.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> dt.datetime:
        """End as a datetime, adjusted for midnight crossing."""
        end_date = self.date if self.end >= self.start else self.date + dt.timedelta(days=1)
        return dt.datetime.combine(end_date, self.end)


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster from text.

    Raises RosterError on the first malformed line.
    """
    shifts: list[Shift] = []

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Split on whitespace
        parts = stripped.split(None, 2)

        # Check for minimum parts
        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_str = parts[0], parts[1]

        # Parse date - must be exactly YYYY-MM-DD format
        if len(date_str) != 10 or date_str[4] != "-" or date_str[7] != "-":
            raise RosterError(line_num, "bad date")

        try:
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise RosterError(line_num, "bad date")

        # Parse time range
        if "-" not in time_str:
            raise RosterError(line_num, "bad time")

        time_parts = time_str.split("-")
        if len(time_parts) != 2:
            raise RosterError(line_num, "bad time")

        # Check format strictly: must be HH:MM-HH:MM
        start_str, end_str = time_parts[0], time_parts[1]
        if len(start_str) != 5 or len(end_str) != 5 or start_str[2] != ":" or end_str[2] != ":":
            raise RosterError(line_num, "bad time")

        try:
            start_time = dt.datetime.strptime(start_str, "%H:%M").time()
            end_time = dt.datetime.strptime(end_str, "%H:%M").time()
        except ValueError:
            raise RosterError(line_num, "bad time")

        # Parse name
        if len(parts) < 3:
            raise RosterError(line_num, "missing name")

        name = parts[2].strip()
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(Shift(date=date, start=start_time, end=end_time, name=name, line=line_num))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find overlapping shifts for the same person.

    Returns a sorted list of conflict pairs.
    """
    shifts_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    # Check all pairs of shifts
    for i, shift_a in enumerate(shifts_list):
        for shift_b in shifts_list[i + 1 :]:
            # Only check shifts for the same person
            if shift_a.name != shift_b.name:
                continue

            # Check overlap using the formula from spec
            if shift_a.start_at < shift_b.end_at and shift_b.start_at < shift_a.end_at:
                # Order by (start_at, line)
                if (shift_a.start_at, shift_a.line) <= (shift_b.start_at, shift_b.line):
                    conflicts.append((shift_a, shift_b))
                else:
                    conflicts.append((shift_b, shift_a))

    # Sort by (name, start_at, line, b.start_at, b.line)
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
    """Return total hours per person.

    Rounds the final total to 2 decimal places.
    """
    totals: dict[str, float] = {}

    for shift in shifts:
        duration_seconds = (shift.end_at - shift.start_at).total_seconds()
        duration_hours = duration_seconds / 3600

        if shift.name not in totals:
            totals[shift.name] = 0.0
        totals[shift.name] += duration_hours

    # Round each total to 2 decimals and sort by name
    result = {}
    for name in sorted(totals.keys()):
        result[name] = round(totals[name], 2)

    return result


__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
