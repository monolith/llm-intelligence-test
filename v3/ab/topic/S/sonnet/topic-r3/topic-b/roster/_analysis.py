"""Finding conflicts and totalling hours over a set of shifts."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from roster._parse import Shift


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of overlapping same-person shifts, reported once.

    See ``SPEC-B.md`` section 2 for the overlap rule and the ordering of both
    the pair and the returned list.
    """
    by_name: dict[str, list[Shift]] = defaultdict(list)
    for shift in shifts:
        by_name[shift.name].append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                first, second = group[i], group[j]
                if first.start_at < second.end_at and second.start_at < first.end_at:
                    if (second.start_at, second.line) < (first.start_at, first.line):
                        first, second = second, first
                    pairs.append((first, second))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours per person, rounded once at the end.

    Keys are inserted in ascending name order.
    """
    totals: dict[str, float] = {}
    for shift in shifts:
        duration_hours = (shift.end_at - shift.start_at).total_seconds() / 3600
        totals[shift.name] = totals.get(shift.name, 0.0) + duration_hours
    return {name: round(totals[name], 2) for name in sorted(totals)}
