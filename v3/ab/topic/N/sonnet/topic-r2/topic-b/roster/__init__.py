"""Shift-roster checker.

See ``SPEC-B.md`` for the format, the public API (``Shift``, ``RosterError``,
``parse_roster``, ``find_conflicts``, ``hours_by_person``) and the
``python -m roster check <file>`` command line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable

__all__ = [
    "Shift",
    "RosterError",
    "parse_roster",
    "find_conflicts",
    "hours_by_person",
]

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


@dataclass(frozen=True)
class Shift:
    date: date
    start: time
    end: time
    name: str
    line: int

    @property
    def start_at(self) -> datetime:
        return datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime:
        end_at = datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += timedelta(days=1)
        return end_at


class RosterError(ValueError):
    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


def _parse_date(text: str) -> date | None:
    if not _DATE_RE.match(text):
        return None
    year, month, day = int(text[0:4]), int(text[5:7]), int(text[8:10])
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_time_range(text: str) -> tuple[time, time] | None:
    match = _TIME_RE.match(text)
    if not match:
        return None
    sh, sm, eh, em = (int(part) for part in match.groups())
    try:
        return time(sh, sm), time(eh, em)
    except ValueError:
        return None


def parse_roster(text: str) -> list[Shift]:
    shifts: list[Shift] = []
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(lineno, "bad line")

        parsed_date = _parse_date(parts[0])
        if parsed_date is None:
            raise RosterError(lineno, "bad date")

        parsed_range = _parse_time_range(parts[1])
        if parsed_range is None:
            raise RosterError(lineno, "bad time")

        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(lineno, "missing name")

        start, end = parsed_range
        shifts.append(Shift(date=parsed_date, start=start, end=end, name=name, line=lineno))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    conflicts: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    if (a.start_at, a.line) <= (b.start_at, b.line):
                        conflicts.append((a, b))
                    else:
                        conflicts.append((b, a))

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
    totals: dict[str, float] = {}
    for shift in shifts:
        duration_hours = (shift.end_at - shift.start_at).total_seconds() / 3600.0
        totals[shift.name] = totals.get(shift.name, 0.0) + duration_hours

    return {name: round(totals[name], 2) for name in sorted(totals)}
