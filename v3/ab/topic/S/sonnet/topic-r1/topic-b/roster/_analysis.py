"""Conflict detection and hour totals over a set of shifts."""

from __future__ import annotations

from collections.abc import Iterable

from roster._model import Shift


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of overlapping same-person shifts, reported once."""
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    if (a.start_at, a.line) <= (b.start_at, b.line):
                        pairs.append((a, b))
                    else:
                        pairs.append((b, a))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Each name's total hours, rounded once at the end."""
    totals: dict[str, float] = {}
    for shift in shifts:
        duration = (shift.end_at - shift.start_at).total_seconds() / 3600
        totals[shift.name] = totals.get(shift.name, 0.0) + duration
    return {name: round(totals[name], 2) for name in sorted(totals)}
