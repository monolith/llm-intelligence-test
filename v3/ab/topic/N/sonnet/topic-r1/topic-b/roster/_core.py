"""Core implementation for the roster package. See SPEC-B.md for the contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Iterable

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_TIME_RANGE_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")
_ONE_DAY = timedelta(days=1)


class RosterError(ValueError):
    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


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
            end_at += _ONE_DAY
        return end_at


def _parse_date(text: str) -> date | None:
    match = _DATE_RE.match(text)
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_time_range(text: str) -> tuple[time, time] | None:
    match = _TIME_RANGE_RE.match(text)
    if match is None:
        return None
    sh, sm, eh, em = (int(part) for part in match.groups())
    try:
        return time(sh, sm), time(eh, em)
    except ValueError:
        return None


def parse_roster(text: str) -> list[Shift]:
    shifts: list[Shift] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        if stripped[0] == "#":
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_no, "bad line")

        parsed_date = _parse_date(parts[0])
        if parsed_date is None:
            raise RosterError(line_no, "bad date")

        parsed_range = _parse_time_range(parts[1])
        if parsed_range is None:
            raise RosterError(line_no, "bad time")

        if len(parts) < 3 or not parts[2].strip():
            raise RosterError(line_no, "missing name")

        start, end = parsed_range
        name = parts[2].strip()
        shifts.append(Shift(date=parsed_date, start=start, end=end, name=name, line=line_no))

    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    key_a = (a.start_at, a.line)
                    key_b = (b.start_at, b.line)
                    pairs.append((a, b) if key_a <= key_b else (b, a))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for shift in shifts:
        hours = (shift.end_at - shift.start_at).total_seconds() / 3600
        totals[shift.name] = totals.get(shift.name, 0.0) + hours

    return {name: round(totals[name], 2) for name in sorted(totals)}
