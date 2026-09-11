"""Finding overlapping shifts and totalling hours per person."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta
from itertools import combinations

from roster._shift import Shift


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of same-person shifts whose intervals overlap by more than an instant."""
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for left, right in combinations(group, 2):
            if left.start_at < right.end_at and right.start_at < left.end_at:
                if (left.start_at, left.line) <= (right.start_at, right.line):
                    pairs.append((left, right))
                else:
                    pairs.append((right, left))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Each name's total scheduled hours, rounded once at the end."""
    totals: dict[str, timedelta] = {}
    for shift in shifts:
        totals[shift.name] = totals.get(shift.name, timedelta()) + (shift.end_at - shift.start_at)

    return {name: round(totals[name].total_seconds() / 3600, 2) for name in sorted(totals)}
