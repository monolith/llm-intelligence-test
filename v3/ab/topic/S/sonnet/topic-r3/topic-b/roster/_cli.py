"""The ``python -m roster`` command line."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from roster._analysis import find_conflicts
from roster._parse import RosterError, parse_roster

USAGE = "usage: python -m roster check <file>"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the ``roster`` command line and return the process exit code."""
    args = list(argv) if argv is not None else sys.argv[1:]

    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    file = args[1]
    try:
        text = Path(file).read_text(encoding="utf-8")
    except OSError:
        print(f"{file}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as exc:
        print(f"{file}: line {exc.line}: {exc.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0

    for first, second in conflicts:
        print(
            f"{first.name}: {first.date.isoformat()} "
            f"{first.start.strftime('%H:%M')}-{first.end.strftime('%H:%M')} overlaps "
            f"{second.date.isoformat()} {second.start.strftime('%H:%M')}-{second.end.strftime('%H:%M')}"
        )
    return 1
