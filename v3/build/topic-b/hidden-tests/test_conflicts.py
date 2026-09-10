"""Hidden tests for `find_conflicts`."""

from __future__ import annotations

from pathlib import Path

from conftest import driver_json, write_roster

PAIRS_DRIVER = '''
text = open("roster.txt", encoding="utf-8").read()
pairs = find_conflicts(parse_roster(text))
emit([[a.line, b.line, a.name, b.name] for a, b in pairs])
'''

# Ann Diaz double-books herself; Bo Fell and the lower-case "ann diaz" overlap
# her in wall-clock time but are other people.
SAME_PERSON = """\
2026-05-01 08:00-16:00 Ann Diaz
2026-05-01 15:00-20:00 Ann Diaz
2026-05-01 09:00-18:00 Bo Fell
2026-05-01 10:00-11:00 ann diaz
"""

# A chain of shifts that only touch, once across midnight.
TOUCHING = """\
2026-05-01 08:00-16:00 Ann Diaz
2026-05-01 16:00-22:00 Ann Diaz
2026-05-01 22:00-06:00 Ann Diaz
2026-05-02 06:00-10:00 Ann Diaz
"""

# Ann's night shift runs into the next morning's; Bo works the same clock hours
# on two different days.
ACROSS_MIDNIGHT = """\
2026-05-01 22:00-06:00 Ann Diaz
2026-05-02 05:30-09:00 Ann Diaz
2026-05-03 22:00-23:00 Bo Fell
2026-05-04 22:00-23:00 Bo Fell
"""

# Three of Ann's shifts overlap each other, out of order in the file; Zed has
# one pair, and sorts after Ann.
ORDERING = """\
2026-05-01 12:00-20:00 Zed Marsh
2026-05-01 10:00-14:00 Ann Diaz
2026-05-01 09:00-13:00 Ann Diaz
2026-05-01 11:00-12:30 Ann Diaz
2026-05-01 13:00-21:00 Zed Marsh
"""


def test_find_conflicts_pairs_overlaps_for_the_same_person_only(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", SAME_PERSON)

    pairs = driver_json(PAIRS_DRIVER, cwd=tmp_path)

    assert [(row[0], row[1]) for row in pairs] == [(1, 2)]
    assert pairs[0][2] == pairs[0][3] == "Ann Diaz"


def test_find_conflicts_ignores_shifts_that_only_touch(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", TOUCHING)

    assert driver_json(PAIRS_DRIVER, cwd=tmp_path) == []


def test_find_conflicts_sees_an_overlap_that_runs_past_midnight(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", ACROSS_MIDNIGHT)

    pairs = driver_json(PAIRS_DRIVER, cwd=tmp_path)

    assert [(row[0], row[1]) for row in pairs] == [(1, 2)]


def test_find_conflicts_sorts_by_name_then_start_with_the_earlier_shift_first(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", ORDERING)

    pairs = driver_json(PAIRS_DRIVER, cwd=tmp_path)

    assert [(row[0], row[1]) for row in pairs] == [(3, 2), (3, 4), (2, 4), (1, 5)]
