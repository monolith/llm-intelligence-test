"""``Shift`` and ``RosterError``, the two data types the rest of the package builds on."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta


@dataclass(frozen=True)
class Shift:
    """One line of a roster, parsed."""

    date: date
    start: time
    end: time
    name: str
    line: int

    @property
    def start_at(self) -> datetime:
        """The moment this shift starts."""
        return datetime.combine(self.date, self.start)

    @property
    def end_at(self) -> datetime:
        """The moment this shift ends, one day later than ``date`` when it crosses midnight."""
        end_at = datetime.combine(self.date, self.end)
        if self.end < self.start:
            end_at += timedelta(days=1)
        return end_at


class RosterError(ValueError):
    """Raised when a roster line cannot be parsed."""

    def __init__(self, line: int, reason: str) -> None:
        self.line = line
        self.reason = reason
        super().__init__(f"line {line}: {reason}")

    def __str__(self) -> str:
        return f"line {self.line}: {self.reason}"
