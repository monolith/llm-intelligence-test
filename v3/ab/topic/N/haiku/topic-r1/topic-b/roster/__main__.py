"""Command-line interface for roster checker."""

import sys
from pathlib import Path

from roster import RosterError, find_conflicts, parse_roster


def main() -> int:
    """Main entry point for the roster check command."""
    # Check arguments
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("usage: python -m roster check <file>", file=sys.stderr)
        return 2

    filepath = sys.argv[2]

    # Try to read the file
    try:
        content = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        print(f"{filepath}: cannot read file", file=sys.stderr)
        return 2

    # Try to parse the roster
    try:
        shifts = parse_roster(content)
    except RosterError as e:
        print(f"{filepath}: line {e.line}: {e.reason}", file=sys.stderr)
        return 2

    # Find conflicts
    conflicts = find_conflicts(shifts)

    # If no conflicts, print "no conflicts" and exit 0
    if not conflicts:
        print("no conflicts")
        return 0

    # Print conflicts and exit 1
    for shift_a, shift_b in conflicts:
        print(
            f"{shift_a.name}: {shift_a.date} {shift_a.start.strftime('%H:%M')}-{shift_a.end.strftime('%H:%M')} "
            f"overlaps {shift_b.date} {shift_b.start.strftime('%H:%M')}-{shift_b.end.strftime('%H:%M')}"
        )

    return 1


if __name__ == "__main__":
    sys.exit(main())
