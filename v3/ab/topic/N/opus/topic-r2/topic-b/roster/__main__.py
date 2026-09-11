"""Command line: ``python -m roster check <file>``."""

from __future__ import annotations

import sys

from roster.core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _fmt(shift: Shift) -> str:
    return f"{shift.date.isoformat()} {shift.start.strftime('%H:%M')}-{shift.end.strftime('%H:%M')}"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, "rb") as handle:
            text = handle.read().decode("utf-8")
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
    for a, b in conflicts:
        print(f"{a.name}: {_fmt(a)} overlaps {_fmt(b)}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
