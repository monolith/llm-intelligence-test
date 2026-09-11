"""Command line interface for roster checker."""

from __future__ import annotations

import sys
from pathlib import Path

from roster import RosterError, find_conflicts, parse_roster


def main() -> int:
    """Run the roster checker command line."""
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("usage: python -m roster check <file>", file=sys.stderr)
        return 2

    file_path = sys.argv[2]

    try:
        text = Path(file_path).read_text(encoding="utf-8")
    except OSError:
        print(f"{file_path}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as err:
        print(f"{file_path}: {err}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)

    if not conflicts:
        print("no conflicts")
        return 0

    for shift_a, shift_b in conflicts:
        a_date = shift_a.date.isoformat()
        a_start = shift_a.start.strftime("%H:%M")
        a_end = shift_a.end.strftime("%H:%M")
        b_date = shift_b.date.isoformat()
        b_start = shift_b.start.strftime("%H:%M")
        b_end = shift_b.end.strftime("%H:%M")
        print(
            f"{shift_a.name}: {a_date} {a_start}-{a_end} overlaps {b_date} {b_start}-{b_end}"
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
