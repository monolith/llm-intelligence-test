"""Command line interface for roster."""

from __future__ import annotations

import sys
from pathlib import Path

from roster import RosterError, find_conflicts, parse_roster


def main() -> int:
    """Main entry point."""
    # Parse arguments
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("usage: python -m roster check <file>", file=sys.stderr)
        return 2

    filepath = sys.argv[2]

    # Read file
    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except (OSError, ValueError):
        print(f"{filepath}: cannot read file", file=sys.stderr)
        return 2

    # Parse roster
    try:
        shifts = parse_roster(text)
    except RosterError as exc:
        print(f"{filepath}: line {exc.line}: {exc.reason}", file=sys.stderr)
        return 2

    # Find conflicts
    conflicts = find_conflicts(shifts)

    if conflicts:
        for first, second in conflicts:
            print(
                f"{first.name}: {first.date} {first.start.strftime('%H:%M')}-"
                f"{first.end.strftime('%H:%M')} overlaps {second.date} "
                f"{second.start.strftime('%H:%M')}-{second.end.strftime('%H:%M')}"
            )
        return 1

    print("no conflicts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
