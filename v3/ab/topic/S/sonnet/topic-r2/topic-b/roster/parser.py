"""Turns roster text into a list of :class:`~roster.models.Shift`."""

from __future__ import annotations

import re
from datetime import date, time

from roster.models import RosterError, Shift

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RANGE_RE = re.compile(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$")


def _parse_date(text: str, line: int) -> date:
    if not _DATE_RE.match(text):
        raise RosterError(line, "bad date")
    year, month, day = text.split("-")
    try:
        return date(int(year), int(month), int(day))
    except ValueError as exc:
        raise RosterError(line, "bad date") from exc


def _parse_time_range(text: str, line: int) -> tuple[time, time]:
    match = _TIME_RANGE_RE.match(text)
    if not match:
        raise RosterError(line, "bad time")
    start_hour, start_minute, end_hour, end_minute = match.groups()
    try:
        start = time(int(start_hour), int(start_minute))
        end = time(int(end_hour), int(end_minute))
    except ValueError as exc:
        raise RosterError(line, "bad time") from exc
    return start, end


def parse_roster(text: str) -> list[Shift]:
    """Parse roster ``text`` into shifts, in the order their lines appear."""
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

        shifts.append(
            Shift(date=shift_date, start=start, end=end, name=parts[2].strip(), line=line_number)
        )
    return shifts
