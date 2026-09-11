"""Finding overlapping shifts and totalling hours worked.

See ``SPEC-B.md`` section 2 for the exact overlap rule and sort order.
"""

from __future__ import annotations

from collections.abc import Iterable

from roster.parsing import Shift


def find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]:
    """Every unordered pair of overlapping same-person shifts, reported once.

    ``a`` and ``b`` conflict when ``a.start_at < b.end_at and b.start_at <
    a.end_at``. The returned pairs are sorted by
    ``(a.name, a.start_at, a.line, b.start_at, b.line)``.
    """
    by_name: dict[str, list[Shift]] = {}
    for shift in shifts:
        by_name.setdefault(shift.name, []).append(shift)

    pairs: list[tuple[Shift, Shift]] = []
    for group in by_name.values():
        ordered = sorted(group, key=lambda shift: (shift.start_at, shift.line))
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                if a.start_at < b.end_at and b.start_at < a.end_at:
                    pairs.append((a, b))

    pairs.sort(key=lambda pair: (pair[0].name, pair[0].start_at, pair[0].line, pair[1].start_at, pair[1].line))
    return pairs


def hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]:
    """Total hours worked per person, rounded once at the end.

    Names are inserted in ascending order, so ``list(result)`` is sorted.
    """
    totals: dict[str, float] = {}
    for shift in shifts:
        duration_hours = (shift.end_at - shift.start_at).total_seconds() / 3600
        totals[shift.name] = totals.get(shift.name, 0.0) + duration_hours

    return {name: round(totals[name], 2) for name in sorted(totals)}
