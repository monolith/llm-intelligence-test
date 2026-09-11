"""The ``python -m roster`` command line."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from roster._analysis import find_conflicts
from roster._model import RosterError
from roster._parsing import parse_roster

USAGE = "usage: python -m roster check <file>"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    args = list(argv) if argv is not None else sys.argv[1:]

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
    except RosterError as exc:
        print(f"{path}: line {exc.line}: {exc.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0

    for a, b in conflicts:
        a_start, a_end = a.start.strftime("%H:%M"), a.end.strftime("%H:%M")
        b_start, b_end = b.start.strftime("%H:%M"), b.end.strftime("%H:%M")
        print(
            f"{a.name}: {a.date.isoformat()} {a_start}-{a_end} "
            f"overlaps {b.date.isoformat()} {b_start}-{b_end}"
        )
    return 1
