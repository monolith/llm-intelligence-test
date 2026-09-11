"""Conflict finding and hour totals over a list of shifts."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations

from roster.models import Shift


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of the same person's shifts whose intervals overlap."""
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    conflicts: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for a, b in combinations(group, 2):
            if a.start_at < b.end_at and b.start_at < a.end_at:
                first, second = sorted((a, b), key=lambda s: (s.start_at, s.line))
                conflicts.append((first, second))

    conflicts.sort(
        key=lambda pair: (
            pair[0].name,
            pair[0].start_at,
            pair[0].line,
            pair[1].start_at,
            pair[1].line,
        )
    )
    return conflicts


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Each name's total hours, rounded once at the end."""
    totals: dict[str, float] = {}
    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600
        totals[shift.name] = totals.get(shift.name, 0.0) + duration

    return {name: round(totals[name], 2) for name in sorted(totals)}
