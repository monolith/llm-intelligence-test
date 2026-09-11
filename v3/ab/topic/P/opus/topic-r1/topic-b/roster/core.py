"""Reading a roster, finding conflicting shifts, and totalling hours."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

_DATE_RE = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})")
_TIME = r"([01][0-9]|2[0-3]):([0-5][0-9])"
_RANGE_RE = re.compile(_TIME + "-" + _TIME)
_ONE_DAY = dt.timedelta(days=1)
_SECONDS_PER_HOUR = 3600


@dataclass(frozen=True)
class Shift:
    """One roster line: ``name`` works from ``start`` to ``end`` on ``date``."""

    date: dt.date
    start: dt.time
    end: dt.time
    name: str
    line: int

    @property
    def start_at(self) -> dt.datetime:
        """The instant the shift starts."""
        return dt.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> dt.datetime:
        """The instant the shift ends, on the next day when it crosses midnight."""
        end_at = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += _ONE_DAY
        return end_at


class RosterError(ValueError):
    """A roster line that cannot be read, with its line number and the reason."""

    line: int
    reason: str

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(line, reason)
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


def _parse_date(text: str) -> dt.date | None:
    match = _DATE_RE.fullmatch(text)
    if match is None:
        return None
    year, month, day = (int(group) for group in match.groups())
    try:
        return dt.date(year, month, day)
    except ValueError:
        return None


def _parse_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _RANGE_RE.fullmatch(text)
    if match is None:
        return None
    start_hour, start_minute, end_hour, end_minute = (int(group) for group in match.groups())
    return dt.time(start_hour, start_minute), dt.time(end_hour, end_minute)


def _parse_line(stripped: str, number: int) -> Shift:
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
    start, end = times
    return Shift(date=date, start=start, end=end, name=name, line=number)


def parse_roster(text: str) -> list[Shift]:
    """Read every shift in ``text``, stopping at the first malformed line."""
    shifts: list[Shift] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        shifts.append(_parse_line(stripped, number))
    return shifts


def _pair_key(pair: tuple[Shift, Shift]) -> tuple[str, dt.datetime, int, dt.datetime, int]:
    first, second = pair
    return (first.name, first.start_at, first.line, second.start_at, second.line)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every pair of one person's shifts that overlap by more than an instant."""
    by_name: dict[str, list[tuple[dt.datetime, int, dt.datetime, Shift]]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append((shift.start_at, shift.line, shift.end_at, shift))

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        group.sort(key=lambda entry: (entry[0], entry[1]))
        for index, (a_start, _, a_end, a) in enumerate(group):
            for position in range(index + 1, len(group)):
                b_start, _, b_end, b = group[position]
                # Later shifts start no earlier than this one, so none of them
                # can overlap ``a`` either.
                if b_start >= a_end:
                    break
                if a_start < b_end:
                    pairs.append((a, b))

    pairs.sort(key=_pair_key)
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours worked by each person, keyed in ascending name order."""
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + (shift.end_at - shift.start_at)
    return {
        name: round(totals[name].total_seconds() / _SECONDS_PER_HOUR, 2) for name in sorted(totals)
    }
