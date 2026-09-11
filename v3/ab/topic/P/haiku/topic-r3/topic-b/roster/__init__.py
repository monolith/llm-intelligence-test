"""Shift-roster checker.

Parse rosters in YYYY-MM-DD HH:MM-HH:MM name format, find scheduling conflicts,
and report hours per person.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]


class RosterError(ValueError):
    """A malformed roster line."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


@dataclass(frozen=True)
class Shift:
    """One shift in the roster."""

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
        end_date = self.date
        if self.end < self.start:
            end_date = self.date + dt.timedelta(days=1)
        return dt.datetime.combine(end_date, self.end)


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster text and return shifts in order.

    Raises RosterError on the first malformed line.
    """
    shifts: list[Shift] = []
    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped[0] == "#":
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_str = parts[0], parts[1]
        name = parts[2].strip() if len(parts) > 2 else ""

        try:
            date = dt.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise RosterError(line_num, "bad date")

        if not _is_valid_time_range(time_str):
            raise RosterError(line_num, "bad time")

        if not name:
            raise RosterError(line_num, "missing name")

        start_time, end_time = _parse_time_range(time_str)
        shifts.append(Shift(date=date, start=start_time, end=end_time, name=name, line=line_num))

    return shifts


def _is_valid_time_range(time_str: str) -> bool:
    """Check if time_str is in HH:MM-HH:MM format with valid times."""
    if "-" not in time_str:
        return False
    parts = time_str.split("-")
    if len(parts) != 2:
        return False
    return _is_valid_time(parts[0]) and _is_valid_time(parts[1])


def _is_valid_time(time_str: str) -> bool:
    """Check if time_str is valid HH:MM format."""
    if len(time_str) != 5 or time_str[2] != ":":
        return False
    try:
        hour = int(time_str[0:2])
        minute = int(time_str[3:5])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return False
        return True
    except ValueError:
        return False


def _parse_time_range(time_str: str) -> tuple[dt.time, dt.time]:
    """Parse HH:MM-HH:MM into two time objects."""
    start_str, end_str = time_str.split("-")
    start = dt.time(int(start_str[0:2]), int(start_str[3:5]))
    end = dt.time(int(end_str[0:2]), int(end_str[3:5]))
    return start, end


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find overlapping shifts for the same person.

    Two shifts conflict when they belong to the same person and their intervals
    overlap by more than an instant.
    """
    shifts_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    for i, shift_a in enumerate(shifts_list):
        for shift_b in shifts_list[i + 1 :]:
            if shift_a.name != shift_b.name:
                continue

            if shift_a.start_at < shift_b.end_at and shift_b.start_at < shift_a.end_at:
                if shift_a.start_at < shift_b.start_at or (
                    shift_a.start_at == shift_b.start_at and shift_a.line < shift_b.line
                ):
                    conflicts.append((shift_a, shift_b))
                else:
                    conflicts.append((shift_b, shift_a))

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
    """Total hours per person, rounded once at the end."""
    totals: dict[str, float] = {}

    for shift in shifts:
        duration_seconds = (shift.end_at - shift.start_at).total_seconds()
        duration_hours = duration_seconds / 3600.0
        totals[shift.name] = totals.get(shift.name, 0.0) + duration_hours

    result = {name: round(total, 2) for name, total in totals.items()}
    return dict(sorted(result.items()))
