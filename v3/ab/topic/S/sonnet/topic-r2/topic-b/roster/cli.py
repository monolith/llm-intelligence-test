"""The ``python -m roster`` command line."""

from __future__ import annotations

import sys
from pathlib import Path

from roster.analysis import find_conflicts
from roster.models import RosterError
from roster.parser import parse_roster

USAGE = "usage: python -m roster check <file>"


def main(argv: list[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    path = args[1]
    try:
        text = Path(path).read_text(encoding="utf-8")
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

    for first, second in conflicts:
        print(
            f"{first.name}: {first.date.isoformat()} "
            f"{first.start:%H:%M}-{first.end:%H:%M} overlaps "
            f"{second.date.isoformat()} {second.start:%H:%M}-{second.end:%H:%M}"
        )
    return 1
