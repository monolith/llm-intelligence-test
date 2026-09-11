"""Shift-roster checker.

See ``SPEC-B.md`` for the format, the public API (``Shift``, ``RosterError``,
``parse_roster``, ``find_conflicts``, ``hours_by_person``) and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable


class RosterError(ValueError):
    """Raised when roster parsing fails."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")


@dataclass(frozen=True)
class Shift:
    """One shift in a roster."""

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
    """Parse roster text and return shifts in order.

    Raises RosterError on the first malformed line.
    """
    shifts: list[Shift] = []

    for line_num, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        # Split into at most 3 parts: date, time range, name
        parts = stripped.split(None, 2)

        # Check for bad line
        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_str = parts[0], parts[1]

        # Parse date
        try:
            parsed_date = date.fromisoformat(date_str)
        except ValueError:
            raise RosterError(line_num, "bad date")

        # Parse time range
        if "-" not in time_str or time_str.count("-") != 1:
            raise RosterError(line_num, "bad time")

        try:
            start_str, end_str = time_str.split("-", 1)
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
        except ValueError:
            raise RosterError(line_num, "bad time")

        # Extract and validate name
        if len(parts) < 3:
            raise RosterError(line_num, "missing name")

        name = parts[2].strip()
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(
            Shift(
                date=parsed_date,
                start=start_time,
                end=end_time,
                name=name,
                line=line_num,
            )
        )

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find overlapping shifts for the same person.

    Returns pairs sorted by (name, a.start_at, a.line, b.start_at, b.line).
    """
    shifts_list = list(shifts)
    conflicts: list[tuple[Shift, Shift]] = []

    # Check all pairs
    for i, a in enumerate(shifts_list):
        for b in shifts_list[i + 1 :]:
            # Only check same person
            if a.name != b.name:
                continue

            # Check for overlap: a.start_at < b.end_at and b.start_at < a.end_at
            if a.start_at < b.end_at and b.start_at < a.end_at:
                # Ensure first element has smaller (start_at, line)
                if (a.start_at, a.line) <= (b.start_at, b.line):
                    conflicts.append((a, b))
                else:
                    conflicts.append((b, a))

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

    Keys are in ascending name order.
    """
    totals: dict[str, float] = {}

    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600
        if shift.name not in totals:
            totals[shift.name] = 0.0
        totals[shift.name] += duration

    # Round once at the end and sort by name
    result = {name: round(total, 2) for name, total in sorted(totals.items())}
    return result


__all__ = ["Shift", "RosterError", "parse_roster", "find_conflicts", "hours_by_person"]
