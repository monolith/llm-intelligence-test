"""Shift-roster checker.

Parses shift rosters, finds scheduling conflicts, and totals hours per person.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass


class RosterError(ValueError):
    """Raised when a roster line is malformed."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")


@dataclass(frozen=True)
class Shift:
    """One shift on the roster."""

    date: dt.date
    start: dt.time
    end: dt.time
    name: str
    line: int

    @property
    def start_at(self) -> dt.datetime:
        """Start as a naive datetime."""
        return dt.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> dt.datetime:
        """End as a naive datetime, adjusted for midnight crossing."""
        end_date = self.date if self.end >= self.start else self.date + dt.timedelta(days=1)
        return dt.datetime.combine(end_date, self.end)


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster from text.

    Returns shifts in order, each with its 1-based line number.
    Raises RosterError on the first malformed line.
    """
    shifts: list[Shift] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped[0] == "#":
            continue

        # Split into at most 3 parts: date, time range, name
        parts = stripped.split(None, 2)

        if len(parts) < 2:
            raise RosterError(line_no, "bad line")

        date_str, time_str = parts[0], parts[1]

        # Parse date
        try:
            year, month, day = date_str.split("-")
            if len(year) != 4 or len(month) != 2 or len(day) != 2:
                raise ValueError()
            date = dt.date(int(year), int(month), int(day))
        except (ValueError, IndexError):
            raise RosterError(line_no, "bad date")

        # Parse time range
        if "-" not in time_str:
            raise RosterError(line_no, "bad time")

        try:
            start_str, end_str = time_str.split("-", 1)
            if len(start_str) != 5 or len(end_str) != 5 or ":" not in start_str or ":" not in end_str:
                raise ValueError()
            start_h, start_m = start_str.split(":")
            end_h, end_m = end_str.split(":")
            start = dt.time(int(start_h), int(start_m))
            end = dt.time(int(end_h), int(end_m))
        except (ValueError, IndexError):
            raise RosterError(line_no, "bad time")

        # Parse name
        if len(parts) < 3:
            raise RosterError(line_no, "missing name")
        name = parts[2].strip()
        if not name:
            raise RosterError(line_no, "missing name")

        shifts.append(Shift(date=date, start=start, end=end, name=name, line=line_no))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find overlapping shifts for the same person.

    Two shifts conflict when a.start_at < b.end_at and b.start_at < a.end_at.
    Returns pairs sorted by (name, a.start_at, a.line, b.start_at, b.line).
    """
    shift_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    # Check all pairs
    for i, a in enumerate(shift_list):
        for b in shift_list[i + 1 :]:
            # Only conflicts within the same person
            if a.name != b.name:
                continue

            # Check overlap condition
            if a.start_at < b.end_at and b.start_at < a.end_at:
                # Ensure first shift has smaller (start_at, line)
                if (a.start_at, a.line) <= (b.start_at, b.line):
                    conflicts.append((a, b))
                else:
                    conflicts.append((b, a))

    # Sort by (name, a.start_at, a.line, b.start_at, b.line)
    conflicts.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))

    return conflicts


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Map each person to their total hours.

    Hours are summed first, then rounded once at the end with round(total, 2).
    Results are sorted by name.
    """
    totals: dict[str, float] = {}

    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        totals[shift.name] = totals.get(shift.name, 0.0) + duration

    # Round each person's total once
    result = {name: round(total, 2) for name, total in totals.items()}

    # Return with keys sorted by name
    return dict(sorted(result.items()))


__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
