"""Command line: ``python -m roster check <file>``."""

from __future__ import annotations

import sys

from roster._core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _describe(shift: Shift) -> str:
    return f"{shift.date:%Y-%m-%d} {shift.start:%H:%M}-{shift.end:%H:%M}"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2
    path = args[1]

    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except (OSError, ValueError):
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
    for a, b in conflicts:
        print(f"{a.name}: {_describe(a)} overlaps {_describe(b)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
