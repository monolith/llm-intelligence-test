"""The `python -m roster` command line."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from .core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _format(shift: Shift) -> str:
    return f"{shift.date.isoformat()} {shift.start:%H:%M}-{shift.end:%H:%M}"


def main(argv: Sequence[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    path = args[1]
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
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
        print(f"{first.name}: {_format(first)} overlaps {_format(second)}")
    return 1
