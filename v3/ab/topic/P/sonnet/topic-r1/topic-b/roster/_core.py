"""Parsing, conflict detection and hour totals for the shift roster.

See ``SPEC-B.md`` for the exact contract; this module implements it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


@dataclass(frozen=True)
class Shift:
    """One shift, as written on one line of a roster."""

    date: date
    start: time
    end: time
    name: str
    line: int

    @property
    def start_at(self) -> datetime:
        """When the shift starts, as a naive datetime."""
        return datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime:
        """When the shift ends, as a naive datetime, one day later if it crosses midnight."""
        end_at = datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += timedelta(days=1)
        return end_at


class RosterError(ValueError):
    """A roster line could not be parsed."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text into shifts, in line order.

    Raises :class:`RosterError` on the first malformed line.
    """
    shifts: list[Shift] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_number, "bad line")

        date_part, time_part = parts[0], parts[1]

        if not _DATE_RE.match(date_part):
            raise RosterError(line_number, "bad date")
        try:
            shift_date = date(int(date_part[0:4]), int(date_part[5:7]), int(date_part[8:10]))
        except ValueError:
            raise RosterError(line_number, "bad date") from None

        time_match = _TIME_RE.match(time_part)
        if not time_match:
            raise RosterError(line_number, "bad time")
        try:
            start_hour, start_minute, end_hour, end_minute = (int(g) for g in time_match.groups())
            start_time = time(start_hour, start_minute)
            end_time = time(end_hour, end_minute)
        except ValueError:
            raise RosterError(line_number, "bad time") from None

        if len(parts) < 3 or not parts[2].strip():
            raise RosterError(line_number, "missing name")
        name = parts[2].strip()

        shifts.append(Shift(date=shift_date, start=start_time, end=end_time, name=name, line=line_number))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of overlapping same-person shifts, reported once each."""
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    if (a.start_at, a.line) <= (b.start_at, b.line):
                        pairs.append((a, b))
                    else:
                        pairs.append((b, a))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded once at the end."""
    totals: dict[str, float] = {}
    for shift in shifts:
        duration_hours = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        totals[shift.name] = totals.get(shift.name, 0.0) + duration_hours
    return {name: round(totals[name], 2) for name in sorted(totals)}
