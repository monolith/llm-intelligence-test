"""Roster parsing, conflict detection and hour totals (see SPEC-B.md)."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

_DATE_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_RANGE_RE = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})")


class RosterError(ValueError):
    """A malformed roster line."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


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


def _parse_date(text: str) -> dt.date | None:
    m = _DATE_RE.fullmatch(text)
    if m is None:
        return None
    try:
        return dt.date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    m = _RANGE_RE.fullmatch(text)
    if m is None:
        return None
    h1, m1, h2, m2 = (int(g) for g in m.groups())
    if h1 > 23 or h2 > 23 or m1 > 59 or m2 > 59:
        return None
    return dt.time(h1, m1), dt.time(h2, m2)


def parse_roster(text: str) -> list[Shift]:
    shifts: list[Shift] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(lineno, "bad line")
        date = _parse_date(parts[0])
        if date is None:
            raise RosterError(lineno, "bad date")
        times = _parse_range(parts[1])
        if times is None:
            raise RosterError(lineno, "bad time")
        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(lineno, "missing name")
        shifts.append(Shift(date, times[0], times[1], name, lineno))
    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for i, a in enumerate(group):
            for b in group[i + 1 :]:
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    if (b.start_at, b.line) < (a.start_at, a.line):
                        pairs.append((b, a))
                    else:
                        pairs.append((a, b))
    pairs.sort(key=lambda p: (p[0].name, p[0].start_at, p[0].line, p[1].start_at, p[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    seconds: dict[str, int] = {}
    for shift in shifts:
        duration = shift.end_at - shift.start_at
        seconds[shift.name] = seconds.get(shift.name, 0) + int(duration.total_seconds())
    return {name: round(seconds[name] / 3600, 2) for name in sorted(seconds)}
