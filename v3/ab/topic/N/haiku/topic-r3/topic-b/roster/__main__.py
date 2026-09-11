"""Command-line interface for roster checker."""

import sys
from pathlib import Path

from roster import RosterError, find_conflicts, parse_roster


def main() -> int:
    """Main entry point for the CLI."""
    if len(sys.argv) != 3 or sys.argv[1] != "check":
        print("usage: python -m roster check <file>", file=sys.stderr)
        return 2

    filepath = sys.argv[2]

    try:
        text = Path(filepath).read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
        print(f"{filepath}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as e:
        print(f"{filepath}: line {e.line}: {e.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)

    if conflicts:
        for shift_a, shift_b in conflicts:
            print(
                f"{shift_a.name}: {shift_a.date} {shift_a.start.strftime('%H:%M')}-{shift_a.end.strftime('%H:%M')} "
                f"overlaps {shift_b.date} {shift_b.start.strftime('%H:%M')}-{shift_b.end.strftime('%H:%M')}"
            )
        return 1
    else:
        print("no conflicts")
        return 0


if __name__ == "__main__":
    sys.exit(main())
