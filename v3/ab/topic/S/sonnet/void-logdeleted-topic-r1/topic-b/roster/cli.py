"""The ``python -m roster`` command line."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from roster._conflicts import find_conflicts
from roster._parse import parse_roster
from roster._shift import RosterError

USAGE = "usage: python -m roster check <file>"


def main(argv: Sequence[str]) -> int:
    """Run ``python -m roster`` with ``argv`` (excluding the program name) and return the exit code."""
    if len(argv) != 2 or argv[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    file_arg = argv[1]
    try:
        text = Path(file_arg).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"{file_arg}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as exc:
        print(f"{file_arg}: line {exc.line}: {exc.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if conflicts:
        for first, second in conflicts:
            print(
                f"{first.name}: {first.date.isoformat()} {first.start:%H:%M}-{first.end:%H:%M} "
                f"overlaps {second.date.isoformat()} {second.start:%H:%M}-{second.end:%H:%M}"
            )
        return 1

    print("no conflicts")
    return 0
