"""The ``python -m roster check <file>`` command line."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from roster.core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _describe(shift: Shift) -> str:
    return f"{shift.date.isoformat()} {shift.start:%H:%M}-{shift.end:%H:%M}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    name = args[1]
    try:
        text = Path(name).read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"{name}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as err:
        print(f"{name}: line {err.line}: {err.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0
    for first, second in conflicts:
        print(f"{first.name}: {_describe(first)} overlaps {_describe(second)}")
    return 1
