"""Parsing a roster's plain text into :class:`Shift` values.

See ``SPEC-B.md`` section 1 for the exact line format and section 2 for the
error semantics of :class:`RosterError`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_TIME_RANGE_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


class RosterError(ValueError):
    """Raised by :func:`parse_roster` on the first malformed line."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason


@dataclass(frozen=True)
class Shift:
    """One shift, as parsed from one line of a roster."""

    date: date
    start: time
    end: time
    name: str
    line: int

    @property
    def start_at(self) -> datetime:
        """The shift's start as a naive datetime."""
        return datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime:
        """The shift's end as a naive datetime, one day later when it crosses midnight."""
        end_at = datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += timedelta(days=1)
        return end_at


def _parse_date(text: str, line: int) -> date:
    match = _DATE_RE.match(text)
    if not match:
        raise RosterError(line, "bad date")
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise RosterError(line, "bad date") from exc


def _parse_time_range(text: str, line: int) -> tuple[time, time]:
    match = _TIME_RANGE_RE.match(text)
    if not match:
        raise RosterError(line, "bad time")
    start_hour, start_minute, end_hour, end_minute = (int(part) for part in match.groups())
    if not (0 <= start_hour <= 23 and 0 <= start_minute <= 59 and 0 <= end_hour <= 23 and 0 <= end_minute <= 59):
        raise RosterError(line, "bad time")
    return time(start_hour, start_minute), time(end_hour, end_minute)


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text into :class:`Shift` values, in line order.

    Raises :class:`RosterError` on the first malformed line and parses no
    further.
    """
    shifts: list[Shift] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped[0] == "#":
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_number, "bad line")

        shift_date = _parse_date(parts[0], line_number)
        start, end = _parse_time_range(parts[1], line_number)

        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(line_number, "missing name")

        shifts.append(Shift(date=shift_date, start=start, end=end, name=name, line=line_number))
    return shifts
