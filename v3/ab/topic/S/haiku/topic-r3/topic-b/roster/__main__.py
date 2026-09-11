"""Command line interface for the roster checker."""

from __future__ import annotations

import sys
from pathlib import Path

from roster import RosterError, find_conflicts, parse_roster


def main(argv: list[str] | None = None) -> int:
    """Run the roster checker command line."""
    if argv is None:
        argv = sys.argv[1:]

    # Check for correct command line arguments
    if len(argv) != 2 or argv[0] != "check":
        sys.stderr.write("usage: python -m roster check <file>\n")
        return 2

    filepath = argv[1]

    # Try to read the file
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except (OSError, IOError):
        sys.stderr.write(f"{filepath}: cannot read file\n")
        return 2

    # Try to parse the roster
    try:
        shifts = parse_roster(text)
    except RosterError as err:
        sys.stderr.write(f"{filepath}: line {err.line}: {err.reason}\n")
        return 2

    # Find conflicts
    conflicts = find_conflicts(shifts)

    if not conflicts:
        sys.stdout.write("no conflicts\n")
        return 0

    # Print conflicts
    for shift_a, shift_b in conflicts:
        date_a = shift_a.date.isoformat()
        start_a = shift_a.start.isoformat(timespec="minutes")
        end_a = shift_a.end.isoformat(timespec="minutes")
        date_b = shift_b.date.isoformat()
        start_b = shift_b.start.isoformat(timespec="minutes")
        end_b = shift_b.end.isoformat(timespec="minutes")

        sys.stdout.write(
            f"{shift_a.name}: {date_a} {start_a}-{end_a} overlaps {date_b} {start_b}-{end_b}\n"
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
