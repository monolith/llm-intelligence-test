"""Command line interface for roster."""

from __future__ import annotations

import sys

from roster import RosterError, find_conflicts, parse_roster


def main() -> int:
    """Run the roster checker."""
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("usage: python -m roster check <file>", file=sys.stderr)
        return 2

    file_path = sys.argv[2]

    # Try to read the file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    except (OSError, IOError):
        print(f"{file_path}: cannot read file", file=sys.stderr)
        return 2

    # Try to parse the roster
    try:
        shifts = parse_roster(text)
    except RosterError as e:
        print(f"{file_path}: {e}", file=sys.stderr)
        return 2

    # Find conflicts
    conflicts = find_conflicts(shifts)

    if conflicts:
        for shift_a, shift_b in conflicts:
            a_time = f"{shift_a.start.strftime('%H:%M')}-{shift_a.end.strftime('%H:%M')}"
            b_time = f"{shift_b.start.strftime('%H:%M')}-{shift_b.end.strftime('%H:%M')}"
            print(f"{shift_a.name}: {shift_a.date} {a_time} overlaps {shift_b.date} {b_time}")
        return 1
    else:
        print("no conflicts")
        return 0


if __name__ == "__main__":
    sys.exit(main())
