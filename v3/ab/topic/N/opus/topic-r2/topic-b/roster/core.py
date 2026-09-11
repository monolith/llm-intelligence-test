"""Roster parsing, conflict detection and hour totals."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_RANGE_RE = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})")


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
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


def _parse_date(text: str) -> dt.date | None:
    if not _DATE_RE.fullmatch(text):
        return None
    try:
        return dt.date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return None


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _RANGE_RE.fullmatch(text)
    if not match:
        return None
    sh, sm, eh, em = (int(g) for g in match.groups())
    if sh > 23 or eh > 23 or sm > 59 or em > 59:
        return None
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
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        group.sort(key=lambda s: (s.start_at, s.line))
        for i, a in enumerate(group):
            a_start, a_end = a.start_at, a.end_at
            for b in group[i + 1:]:
                b_start = b.start_at
                if b_start >= a_end:
                    break
                if a_start < b.end_at:
                    pairs.append((a, b))

    pairs.sort(key=lambda p: (p[0].name, p[0].start_at, p[0].line, p[1].start_at, p[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + (shift.end_at - shift.start_at)
    return {name: round(totals[name].total_seconds() / 3600, 2) for name in sorted(totals)}
