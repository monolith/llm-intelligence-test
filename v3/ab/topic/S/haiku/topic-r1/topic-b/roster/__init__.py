"""Shift-roster checker."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable


class RosterError(ValueError):
    """Exception raised when parsing a roster line fails."""

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

    Returns shifts in order, with 1-based line numbers. Raises RosterError on
    the first malformed line.
    """
    shifts: list[Shift] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_str = parts[0], parts[1]

        # Validate and parse date
        try:
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise RosterError(line_num, "bad date")

        # Validate and parse time range
        if not _is_valid_time_range(time_str):
            raise RosterError(line_num, "bad time")

        start_str, end_str = time_str.split("-", 1)
        start = dt.datetime.strptime(start_str, "%H:%M").time()
        end = dt.datetime.strptime(end_str, "%H:%M").time()

        # Extract and validate name
        name = parts[2].strip() if len(parts) > 2 else ""
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(Shift(date=date, start=start, end=end, name=name, line=line_num))

    return shifts


def _is_valid_time_range(time_str: str) -> bool:
    """Check if a time range string is valid HH:MM-HH:MM format (zero-padded)."""
    parts = time_str.split("-")
    if len(parts) != 2:
        return False
    for part in parts:
        if not _is_valid_time(part):
            return False
    return True


def _is_valid_time(time_str: str) -> bool:
    """Check if a time string is valid HH:MM format (zero-padded)."""
    if len(time_str) != 5 or time_str[2] != ":":
        return False
    try:
        dt.datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find all conflicting shift pairs for the same person.

    Two shifts conflict if they belong to the same person and overlap by more
    than an instant: a.start_at < b.end_at and b.start_at < a.end_at.
    """
    shifts_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    for i, shift_a in enumerate(shifts_list):
        for shift_b in shifts_list[i + 1 :]:
            if shift_a.name == shift_b.name:
                if shift_a.start_at < shift_b.end_at and shift_b.start_at < shift_a.end_at:
                    # Order by (start_at, line)
                    if (shift_a.start_at, shift_a.line) <= (shift_b.start_at, shift_b.line):
                        conflicts.append((shift_a, shift_b))
                    else:
                        conflicts.append((shift_b, shift_a))

    # Sort by (name, a.start_at, a.line, b.start_at, b.line)
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
    """Calculate total hours per person.

    Sums all shift durations, then rounds once at the end with round(total, 2).
    Returns a dict with names in ascending order.
    """
    totals: dict[str, float] = {}

    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        if shift.name not in totals:
            totals[shift.name] = 0.0
        totals[shift.name] += duration

    # Round once at the end and sort by name
    result = {name: round(total, 2) for name, total in sorted(totals.items())}
    return result


__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
