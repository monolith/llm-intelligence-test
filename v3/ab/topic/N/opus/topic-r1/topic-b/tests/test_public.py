"""Three smoke tests over the public API. Run them with `python -m pytest tests/`.

They are a small sample of what SPEC-B.md requires, not the whole contract.
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


SAMPLE = """\
# week 18
2026-05-01 08:00-16:00 Ann Diaz

2026-05-01 15:00-20:00 Ann Diaz
2026-05-01 16:00-22:00 Bo Fell
"""


def test_parse_roster_reads_the_lines_that_are_not_blank_or_comments() -> None:
    from roster import parse_roster

    shifts = parse_roster(SAMPLE)

    assert [s.name for s in shifts] == ["Ann Diaz", "Ann Diaz", "Bo Fell"]
    assert shifts[0].date == dt.date(2026, 5, 1)
    assert shifts[0].start == dt.time(8, 0)
    assert shifts[0].end == dt.time(16, 0)
    assert shifts[0].line == 2


def test_find_conflicts_pairs_one_persons_overlapping_shifts() -> None:
    from roster import find_conflicts, parse_roster

    conflicts = find_conflicts(parse_roster(SAMPLE))

    assert len(conflicts) == 1
    first, second = conflicts[0]
    assert first.name == second.name == "Ann Diaz"
    assert first.start == dt.time(8, 0)
    assert second.start == dt.time(15, 0)


def test_hours_by_person_counts_a_shift_that_crosses_midnight() -> None:
    from roster import hours_by_person, parse_roster

    totals = hours_by_person(parse_roster("2026-05-01 22:00-06:00 Ann Diaz\n"))

    assert totals == {"Ann Diaz": 8.0}
