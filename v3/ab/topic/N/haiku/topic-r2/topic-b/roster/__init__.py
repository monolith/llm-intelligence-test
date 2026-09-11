"""Shift-roster checker.

Nothing is implemented yet. See ``SPEC-B.md`` for the format, the public API
(``Shift``, ``RosterError``, ``parse_roster``, ``find_conflicts``,
``hours_by_person``) and the ``python -m roster check <file>`` command line.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Shift:
    date: datetime.date
    start: datetime.time
    end: datetime.time
    name: str
    line: int

    @property
    def start_at(self) -> datetime.datetime:
        return datetime.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime.datetime:
        end_date = self.date if self.end >= self.start else self.date + datetime.timedelta(days=1)
        return datetime.datetime.combine(end_date, self.end)


class RosterError(ValueError):
    def __init__(self, line: int, reason: str):
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text and return list of Shift objects."""
    shifts = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        if not stripped or stripped[0] == '#':
            continue

        parts = stripped.split(None, 2)

        if len(parts) < 2:
            raise RosterError(line_num, "bad line")

        date_str, time_str = parts[0], parts[1]

        try:
            date = datetime.date.fromisoformat(date_str)
        except (ValueError, TypeError):
            raise RosterError(line_num, "bad date")

        try:
            start_str, end_str = time_str.split('-')
            start = datetime.time.fromisoformat(start_str)
            end = datetime.time.fromisoformat(end_str)
        except (ValueError, TypeError):
            raise RosterError(line_num, "bad time")

        if len(parts) < 3:
            raise RosterError(line_num, "missing name")

        name = parts[2].strip()
        if not name:
            raise RosterError(line_num, "missing name")

        shifts.append(Shift(date=date, start=start, end=end, name=name, line=line_num))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Find overlapping shifts for the same person."""
    shifts_list = list(shifts)
    conflicts = []

    for i, shift_a in enumerate(shifts_list):
        for shift_b in shifts_list[i + 1:]:
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
        key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line)
    )

    return conflicts


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Calculate total hours per person."""
    hours_dict = {}

    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        if shift.name not in hours_dict:
            hours_dict[shift.name] = 0.0
        hours_dict[shift.name] += duration

    for name in hours_dict:
        hours_dict[name] = round(hours_dict[name], 2)

    return dict(sorted(hours_dict.items()))
