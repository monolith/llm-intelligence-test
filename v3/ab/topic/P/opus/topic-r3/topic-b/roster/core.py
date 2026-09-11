"""The roster format, the shift type, and the two things worth asking about a roster.

One shift per line, ``YYYY-MM-DD HH:MM-HH:MM name``.  A shift whose end time is
less than its start time crosses midnight and finishes the next day; one whose
end equals its start is zero-length.  See ``SPEC-B.md``.
"""

from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass

COMMENT_PREFIX = "#"
DATE_PATTERN = re.compile(r"([0-9]{4})-([0-9]{2})-([0-9]{2})\Z")
RANGE_PATTERN = re.compile(r"([0-9]{2}):([0-9]{2})-([0-9]{2}):([0-9]{2})\Z")
SECONDS_PER_HOUR = 3600


class RosterError(ValueError):
    """A line that does not hold a shift.  ``str()`` reads ``line N: reason``."""

    line: int
    reason: str

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


@dataclass(frozen=True)
class Shift:
    """One person's shift, as one line of a roster wrote it."""

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
        """When the shift ends, the next day when it crosses midnight."""
        ends = dt.datetime.combine(self.date, self.end)
        if self.end < self.start:
            ends += dt.timedelta(days=1)
        return ends


def _parse_date(text: str, line: int) -> dt.date:
    match = DATE_PATTERN.fullmatch(text)
    if match is None:
        raise RosterError(line, "bad date")
    year, month, day = (int(part) for part in match.groups())
    try:
        return dt.date(year, month, day)
    except ValueError as exc:
        raise RosterError(line, "bad date") from exc


def _parse_range(text: str, line: int) -> tuple[dt.time, dt.time]:
    match = RANGE_PATTERN.fullmatch(text)
    if match is None:
        raise RosterError(line, "bad time")
    start_hour, start_minute, end_hour, end_minute = (int(part) for part in match.groups())
    try:
        return dt.time(start_hour, start_minute), dt.time(end_hour, end_minute)
    except ValueError as exc:
        raise RosterError(line, "bad time") from exc


def _parse_line(stripped: str, line: int) -> Shift:
    parts = stripped.split(None, 2)
    if len(parts) < 2:
        raise RosterError(line, "bad line")
    date = _parse_date(parts[0], line)
    start, end = _parse_range(parts[1], line)
    name = parts[2].strip() if len(parts) > 2 else ""
    if not name:
        raise RosterError(line, "missing name")
    return Shift(date=date, start=start, end=end, name=name, line=line)


def parse_roster(text: str) -> list[Shift]:
    """Read a roster into shifts, in line order, each carrying its 1-based line number.

    Blank lines and lines starting with ``#`` are skipped.  The first malformed
    line raises :class:`RosterError` and nothing after it is parsed.
    """
    shifts: list[Shift] = []
    for line, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith(COMMENT_PREFIX):
            continue
        shifts.append(_parse_line(stripped, line))
    return shifts


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every pair of shifts of one person whose intervals overlap by more than an instant.

    Shifts that merely touch do not conflict, and neither do two people's shifts
    however much they overlap.  Each unordered pair comes back once, smaller
    ``(start_at, line)`` first, sorted by name, then by each shift in turn.
    """
    items = list(shifts)
    pairs: list[tuple[Shift, Shift]] = []
    for index, one in enumerate(items):
        for other in items[index + 1 :]:
            if one.name != other.name:
                continue
            if one.start_at < other.end_at and other.start_at < one.end_at:
                first, second = sorted((one, other), key=lambda shift: (shift.start_at, shift.line))
                pairs.append((first, second))
    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, keyed in ascending name order.

    Durations are added up exactly and rounded once, at the end, so three
    twenty minute shifts come to ``1.0`` rather than ``0.99``.
    """
    totals: dict[str, dt.timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, dt.timedelta()) + (shift.end_at - shift.start_at)
    return {
        name: round(totals[name].total_seconds() / SECONDS_PER_HOUR, 2) for name in sorted(totals)
    }
