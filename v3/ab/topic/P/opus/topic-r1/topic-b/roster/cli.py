"""The ``python -m roster check <file>`` command line."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from roster.core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _describe(shift: Shift) -> str:
    return f"{shift.date.isoformat()} {shift.start:%H:%M}-{shift.end:%H:%M}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2
    path = args[1]

    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, UnicodeDecodeError):
        print(f"{path}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as err:
        print(f"{path}: {err}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0
    for first, second in conflicts:
        print(f"{first.name}: {_describe(first)} overlaps {_describe(second)}")
    return 1
