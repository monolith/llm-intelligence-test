"""Parsing a roster's text into :class:`~roster._shift.Shift` values."""

from __future__ import annotations

import re
from datetime import date, time

from roster._shift import RosterError, Shift

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_TIME_RANGE_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


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
    start_h, start_m, end_h, end_m = (int(part) for part in match.groups())
    try:
        return time(start_h, start_m), time(end_h, end_m)
    except ValueError:
        return None


def parse_roster(text: str) -> list[Shift]:
    """Parse a roster's whole text into an ordered list of shifts.

    Raises :class:`RosterError` on the first malformed line and stops there.
    """
    shifts: list[Shift] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split(None, 2)
        if len(parts) < 2:
            raise RosterError(line_number, "bad line")

        day = _parse_date(parts[0])
        if day is None:
            raise RosterError(line_number, "bad date")

        time_range = _parse_time_range(parts[1])
        if time_range is None:
            raise RosterError(line_number, "bad time")

        if len(parts) < 3 or not parts[2].strip():
            raise RosterError(line_number, "missing name")

        start, end = time_range
        shifts.append(Shift(date=day, start=start, end=end, name=parts[2].strip(), line=line_number))

    return shifts
