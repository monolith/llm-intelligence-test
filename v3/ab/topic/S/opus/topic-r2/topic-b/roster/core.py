"""The roster format, the Shift type, and the conflict and hours calculations."""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

# ASCII digits only: ``\d`` would also accept other scripts' digits.
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_TIME_RANGE_PATTERN = re.compile(r"([01][0-9]|2[0-3]):([0-5][0-9])-([01][0-9]|2[0-3]):([0-5][0-9])")


class RosterError(ValueError):
    """A malformed roster line."""

    line: int
    reason: str

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


@dataclass(frozen=True)
class Shift:
    """One shift, as written on one roster line."""

    date: dt.date
    start: dt.time
    end: dt.time
    name: str
    line: int

    @property
    def start_at(self) -> dt.datetime:
        """When the shift starts."""
        return dt.datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> dt.datetime:
        """When the shift ends; the following day when it crosses midnight."""
        end = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            end += dt.timedelta(days=1)
        return end


def _parse_date(text: str) -> dt.date | None:
    if not _DATE_PATTERN.fullmatch(text):
        return None
    try:
        return dt.date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return None


def _parse_time_range(text: str) -> tuple[dt.time, dt.time] | None:
    match = _TIME_RANGE_PATTERN.fullmatch(text)
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
    times = _parse_time_range(parts[1])
    if times is None:
        raise RosterError(number, "bad time")
    name = parts[2].strip() if len(parts) == 3 else ""
    if not name:
        raise RosterError(number, "missing name")
    start, end = times
    return Shift(date=date, start=start, end=end, name=name, line=number)


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text into shifts, in line order.

    Raises :class:`RosterError` on the first malformed line.
    """
    shifts: list[Shift] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        shifts.append(_parse_line(stripped, number))
    return shifts


def _order_key(shift: Shift) -> tuple[dt.datetime, int]:
    return (shift.start_at, shift.line)


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every pair of one person's shifts that overlap by more than an instant."""
    by_person: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_person.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for own in by_person.values():
        own.sort(key=_order_key)
        for index, first in enumerate(own):
            first_start = first.start_at
            first_end = first.end_at
            for second in own[index + 1 :]:
                # Later shifts start no earlier than this one, so once one
                # starts at or after this one's end, none of the rest overlap.
                if second.start_at >= first_end:
                    break
                if first_start < second.end_at:
                    pairs.append((first, second))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded once to two places, keyed in name order."""
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + (shift.end_at - shift.start_at)
    return {name: round(totals[name] / dt.timedelta(hours=1), 2) for name in sorted(totals)}
