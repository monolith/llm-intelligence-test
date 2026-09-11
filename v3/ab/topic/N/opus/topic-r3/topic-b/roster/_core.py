"""Parsing, conflict detection and hour totals for shift rosters."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

_DATE_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_CLOCK = r"([01][0-9]|2[0-3]):([0-5][0-9])"
_RANGE_RE = re.compile(_CLOCK + "-" + _CLOCK)


@dataclass(frozen=True)
class Shift:
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
        end = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end += dt.timedelta(days=1)
        return end


class RosterError(ValueError):
    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(line, reason)

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


def _parse_date(text: str) -> dt.date | None:
    match = _DATE_RE.fullmatch(text)
    if match is None:
        return None
    try:
        return dt.date(*(int(part) for part in match.groups()))
    except ValueError:
        return None


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _RANGE_RE.fullmatch(text)
    if match is None:
        return None
    sh, sm, eh, em = (int(part) for part in match.groups())
    return dt.time(sh, sm), dt.time(eh, em)


def parse_roster(text: str) -> list[Shift]:
    shifts: list[Shift] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(number, "bad line")
        date = _parse_date(parts[0])
        if date is None:
            raise RosterError(number, "bad date")
        times = _parse_range(parts[1])
        if times is None:
            raise RosterError(number, "bad time")
        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(number, "missing name")
        shifts.append(Shift(date, times[0], times[1], name, number))
    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    by_person: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_person.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_person.values():
        group.sort(key=lambda s: (s.start_at, s.line))
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    pairs.append((a, b))

    pairs.sort(key=lambda p: (p[0].name, p[0].start_at, p[0].line, p[1].start_at, p[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    seconds: dict[str, int] = {}
    for shift in shifts:
        length = shift.end_at - shift.start_at
        seconds[shift.name] = seconds.get(shift.name, 0) + int(length.total_seconds())
    return {name: round(seconds[name] / 3600, 2) for name in sorted(seconds)}
