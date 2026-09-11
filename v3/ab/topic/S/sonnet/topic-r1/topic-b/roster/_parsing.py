"""Turning roster text into :class:`~roster._model.Shift` objects."""

from __future__ import annotations

import re
from datetime import date, time

from roster._model import RosterError, Shift

_DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_TIME_RANGE_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


def _parse_date(text: str, line: int) -> date:
    match = _DATE_RE.match(text)
    if match is None:
        raise RosterError(line, "bad date")
    year, month, day = (int(group) for group in match.groups())
    try:
        return date(year, month, day)
    except ValueError as exc:
        raise RosterError(line, "bad date") from exc


def _parse_time_range(text: str, line: int) -> tuple[time, time]:
    match = _TIME_RANGE_RE.match(text)
    if match is None:
        raise RosterError(line, "bad time")
    start_hour, start_minute, end_hour, end_minute = (int(group) for group in match.groups())
    try:
        start = time(start_hour, start_minute)
        end = time(end_hour, end_minute)
    except ValueError as exc:
        raise RosterError(line, "bad time") from exc
    return start, end


def parse_roster(text: str) -> list[Shift]:
    """Parse roster text into shifts, in line order.

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

        if len(parts) < 3 or not parts[2].strip():
            raise RosterError(line_number, "missing name")
        name = parts[2].strip()

        shifts.append(Shift(date=shift_date, start=start, end=end, name=name, line=line_number))

    return shifts
