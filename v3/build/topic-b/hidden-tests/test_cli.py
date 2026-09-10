"""Hidden tests for `python -m roster check`."""

from __future__ import annotations

from pathlib import Path

from conftest import run_cli, write_roster

WEEK = """\
# week 18
2026-05-01 08:00-16:00 Ann Diaz
2026-05-01 15:00-20:00 Ann Diaz

2026-05-01 16:00-22:00 Bo Fell
2026-05-01 22:00-06:00 Ann Diaz
2026-05-02 05:30-09:00 Ann Diaz
"""

CLEAN = """\
# week 19
2026-05-08 08:00-16:00 Ann Diaz
2026-05-08 16:00-22:00 Ann Diaz
2026-05-08 09:00-17:00 Bo Fell
"""

BROKEN = """\
# week 20
2026-05-15 08:00-16:00 Ann Diaz
2026-05-15 25:00-26:00 Bo Fell
2026-05-15 09:00-17:00 Ann Diaz
"""


def test_check_prints_the_conflicts_it_found_and_exits_1_only_when_there_are_any(tmp_path: Path) -> None:
    write_roster(tmp_path, "week.txt", WEEK)
    write_roster(tmp_path, "clean.txt", CLEAN)

    dirty = run_cli(["check", "week.txt"], cwd=tmp_path)
    assert dirty.returncode == 1, dirty.stdout + dirty.stderr
    assert dirty.stdout.splitlines() == [
        "Ann Diaz: 2026-05-01 08:00-16:00 overlaps 2026-05-01 15:00-20:00",
        "Ann Diaz: 2026-05-01 22:00-06:00 overlaps 2026-05-02 05:30-09:00",
    ]

    clean = run_cli(["check", "clean.txt"], cwd=tmp_path)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert clean.stdout.splitlines() == ["no conflicts"]


def test_check_exits_2_and_names_the_bad_line_on_stderr(tmp_path: Path) -> None:
    write_roster(tmp_path, "broken.txt", BROKEN)

    proc = run_cli(["check", "broken.txt"], cwd=tmp_path)

    assert proc.returncode == 2, proc.stdout + proc.stderr
    assert proc.stdout == ""
    assert proc.stderr.splitlines() == ["broken.txt: line 3: bad time"]
