"""The ``Shift`` record and the parse error type."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type
from datetime import datetime, time as time_type, timedelta


@dataclass(frozen=True)
class Shift:
    """One shift, as written on one line of a roster."""

    date: date_type
    start: time_type
    end: time_type
    name: str
    line: int

    @property
    def start_at(self) -> datetime:
        """The shift's start as a naive datetime."""
        return datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime:
        """The shift's end as a naive datetime, a day later when it crosses midnight."""
        end_at = datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += timedelta(days=1)
        return end_at


class RosterError(ValueError):
    """Raised on the first malformed line of a roster."""

    def __init__(self, line: int, reason: str) -> None:
        super().__init__(f"line {line}: {reason}")
        self.line = line
        self.reason = reason

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"
