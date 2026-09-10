"""Hidden tests for `parse_roster`."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import driver_json, write_roster

MIXED = """\
# week 18
2026-05-01 08:00-16:00 Ann Diaz

   2026-05-02 09:15-17:45   Bo Fell   
# a second comment
2026-05-03 06:00-14:00 C. Okafor #2 late
"""

MIDNIGHT = """\
2026-05-01 22:00-06:00 Ann Diaz
2026-05-01 09:00-17:00 Ann Diaz
2026-05-01 12:00-12:00 Ann Diaz
"""

BAD = {
    "e1.txt": "\n\n2026-05-01\n",
    "e2.txt": "# lead\nnotadate 08:00-16:00 Ann Diaz\n",
    "e3.txt": "2026-02-30 08:00-16:00 Ann Diaz\n",
    "e4.txt": "2026-05-01 8:00-16:00 Ann Diaz\n",
    "e5.txt": "2026-05-01 08:00-16:00\n",
    "e6.txt": "2026-13-01 nonsense Ann Diaz\n",
    "e7.txt": "2026-05-01 08:00-16:00 Ann Diaz\nbroken\n2026-05-01 xx Ann Diaz\n",
}


def test_parse_roster_skips_comments_and_blanks_and_records_the_source_line(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", MIXED)

    shifts = driver_json(
        '''
        text = open("roster.txt", encoding="utf-8").read()
        emit([shape(s) for s in parse_roster(text)])
        ''',
        cwd=tmp_path,
    )

    assert [s["line"] for s in shifts] == [2, 4, 6]
    assert [s["name"] for s in shifts] == ["Ann Diaz", "Bo Fell", "C. Okafor #2 late"]
    assert [s["date"] for s in shifts] == ["2026-05-01", "2026-05-02", "2026-05-03"]
    assert [s["start"] for s in shifts] == ["08:00", "09:15", "06:00"]
    assert [s["end"] for s in shifts] == ["16:00", "17:45", "14:00"]


def test_parse_roster_ends_a_midnight_crossing_shift_on_the_next_day(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", MIDNIGHT)

    shifts = driver_json(
        '''
        text = open("roster.txt", encoding="utf-8").read()
        emit([shape(s) for s in parse_roster(text)])
        ''',
        cwd=tmp_path,
    )

    crossing, same_day, empty = shifts
    assert (crossing["start_at"], crossing["end_at"]) == ("2026-05-01T22:00:00", "2026-05-02T06:00:00")
    assert (same_day["start_at"], same_day["end_at"]) == ("2026-05-01T09:00:00", "2026-05-01T17:00:00")
    assert (empty["start_at"], empty["end_at"]) == ("2026-05-01T12:00:00", "2026-05-01T12:00:00")


def test_parse_roster_raises_roster_error_with_the_line_number_and_reason(tmp_path: Path) -> None:
    for name, text in BAD.items():
        write_roster(tmp_path, name, text)
    write_roster(tmp_path, "names.json", json.dumps(sorted(BAD)))

    reported = driver_json(
        '''
        import json
        names = json.loads(open("names.json", encoding="utf-8").read())
        out = []
        for name in names:
            text = open(name, encoding="utf-8").read()
            try:
                parse_roster(text)
            except RosterError as err:
                out.append([name, err.line, err.reason, str(err), isinstance(err, ValueError)])
            else:
                out.append([name, None, None, None, None])
        emit(out)
        ''',
        cwd=tmp_path,
    )

    assert [(row[0], row[1], row[2]) for row in reported] == [
        ("e1.txt", 3, "bad line"),
        ("e2.txt", 2, "bad date"),
        ("e3.txt", 1, "bad date"),
        ("e4.txt", 1, "bad time"),
        ("e5.txt", 1, "missing name"),
        ("e6.txt", 1, "bad date"),
        ("e7.txt", 2, "bad line"),
    ]
    assert [row[3] for row in reported] == [f"line {row[1]}: {row[2]}" for row in reported]
    assert all(row[4] is True for row in reported)
