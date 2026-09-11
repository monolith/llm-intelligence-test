"""CLI entry point for roster."""

from __future__ import annotations

import sys

from roster import RosterError, find_conflicts, parse_roster


def main() -> int:
    """Run the roster checker."""
    # Check command line arguments
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("usage: python -m roster check <file>", file=sys.stderr)
        return 2

    filepath = sys.argv[2]

    # Try to read the file
    try:
        with open(filepath, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        print(f"{filepath}: cannot read file", file=sys.stderr)
        return 2

    # Try to parse the roster
    try:
        shifts = parse_roster(text)
    except RosterError as e:
        print(f"{filepath}: line {e.line}: {e.reason}", file=sys.stderr)
        return 2

    # Find conflicts
    conflicts = find_conflicts(shifts)

    # Output results
    if conflicts:
        for a, b in conflicts:
            a_start = f"{a.start.hour:02d}:{a.start.minute:02d}"
            a_end = f"{a.end.hour:02d}:{a.end.minute:02d}"
            b_start = f"{b.start.hour:02d}:{b.start.minute:02d}"
            b_end = f"{b.end.hour:02d}:{b.end.minute:02d}"
            print(
                f"{a.name}: {a.date} {a_start}-{a_end} overlaps {b.date} {b_start}-{b_end}"
            )
        return 1
    else:
        print("no conflicts")
        return 0


if __name__ == "__main__":
    sys.exit(main())
