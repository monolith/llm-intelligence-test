"""Command line: ``python -m roster check <file>``."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from roster.core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _describe(shift: Shift) -> str:
    return f"{shift.date.isoformat()} {shift.start:%H:%M}-{shift.end:%H:%M}"


def main(argv: Sequence[str]) -> int:
    """Run the command line and return the exit code."""
    if len(argv) != 2 or argv[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2
    path = argv[1]

    try:
        # newline="" hands the text to splitlines() exactly as it is on disk.
        with open(path, encoding="utf-8", newline="") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        print(f"{path}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as err:
        print(f"{path}: line {err.line}: {err.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0
    for first, second in conflicts:
        print(f"{first.name}: {_describe(first)} overlaps {_describe(second)}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
