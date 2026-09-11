"""Roster line format: the ``Shift`` type, ``RosterError`` and ``parse_roster``.

See ``SPEC-B.md`` section 1 and 2 for the format this reads and the exact
validation order errors are raised in.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_TIME_RANGE_RE = re.compile(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})")


@dataclass(frozen=True)
class Shift:
    """One line of a roster, already validated."""

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


class RosterError(ValueError):
    """Raised on the first malformed line a roster parse encounters."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"


def _parse_date(text: str) -> date | None:
    if not _DATE_RE.fullmatch(text):
        return None
    try:
        return date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except ValueError:
        return None


def _parse_time_range(text: str) -> tuple[time, time] | None:
    match = _TIME_RANGE_RE.fullmatch(text)
    if not match:
        return None
    start_hour, start_minute, end_hour, end_minute = (int(part) for part in match.groups())
    try:
        return time(start_hour, start_minute), time(end_hour, end_minute)
    except ValueError:
        return None


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster's text into ``Shift`` objects, in line order.

    Raises ``RosterError`` on the first malformed line and parses no further.
    """
    shifts: list[Shift] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped[0] == "#":
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_number, "bad line")

        parsed_date = _parse_date(parts[0])
        if parsed_date is None:
            raise RosterError(line_number, "bad date")

        time_range = _parse_time_range(parts[1])
        if time_range is None:
            raise RosterError(line_number, "bad time")

        name = parts[2].strip() if len(parts) == 3 else ""
        if not name:
            raise RosterError(line_number, "missing name")

        start, end = time_range
        shifts.append(Shift(date=parsed_date, start=start, end=end, name=name, line=line_number))

    return shifts
