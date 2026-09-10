"""Hidden test for `hours_by_person`."""

from __future__ import annotations

from pathlib import Path

from conftest import driver_json, write_roster

# Ann: a night shift of 8h15 plus three 20-minute shifts that add to exactly one
# hour -- but only if the rounding happens once, at the end.
# Bo: 50 minutes. Zed: a zero-length shift.
TOTALS = """\
# week 18
2026-05-01 22:00-06:15 Ann Diaz
2026-05-02 07:00-07:20 Ann Diaz
2026-05-02 08:00-08:20 Ann Diaz
2026-05-02 09:00-09:20 Ann Diaz
2026-05-01 12:00-12:00 Zed Marsh
2026-05-01 07:00-07:50 Bo Fell
"""


def test_hours_by_person_rounds_once_and_keys_in_name_order(tmp_path: Path) -> None:
    write_roster(tmp_path, "roster.txt", TOTALS)

    result = driver_json(
        '''
        text = open("roster.txt", encoding="utf-8").read()
        totals = hours_by_person(parse_roster(text))
        emit({"totals": totals, "keys": list(totals), "empty": hours_by_person([])})
        ''',
        cwd=tmp_path,
    )

    assert result["totals"] == {"Ann Diaz": 9.25, "Bo Fell": 0.83, "Zed Marsh": 0.0}
    assert result["keys"] == ["Ann Diaz", "Bo Fell", "Zed Marsh"]
    assert result["empty"] == {}
