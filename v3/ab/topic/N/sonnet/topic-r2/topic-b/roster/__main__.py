"""Command line entry point: ``python -m roster check <file>``."""

from __future__ import annotations

import sys

from roster import RosterError, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    file = args[1]
    try:
        with open(file, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError:
        print(f"{file}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as err:
        print(f"{file}: line {err.line}: {err.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0

    for a, b in conflicts:
        print(
            f"{a.name}: {a.date.isoformat()} "
            f"{a.start.strftime('%H:%M')}-{a.end.strftime('%H:%M')} overlaps "
            f"{b.date.isoformat()} {b.start.strftime('%H:%M')}-{b.end.strftime('%H:%M')}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
