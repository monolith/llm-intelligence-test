"""The ``python -m roster`` command line. See ``SPEC-B.md`` section 3."""

from __future__ import annotations

import sys
from pathlib import Path

from roster.conflicts import find_conflicts
from roster.parsing import RosterError, Shift, parse_roster

USAGE = "usage: python -m roster check <file>"


def _format_conflict(first: Shift, second: Shift) -> str:
    return (
        f"{first.name}: {first.date.isoformat()} {first.start:%H:%M}-{first.end:%H:%M} "
        f"overlaps {second.date.isoformat()} {second.start:%H:%M}-{second.end:%H:%M}"
    )


def main(argv: list[str]) -> int:
    """Run the ``roster`` command line and return the process exit code."""
    if len(argv) != 2 or argv[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    file_arg = argv[1]
    try:
        text = Path(file_arg).read_text(encoding="utf-8")
    except OSError:
        print(f"{file_arg}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as exc:
        print(f"{file_arg}: line {exc.line}: {exc.reason}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0

    for first, second in conflicts:
        print(_format_conflict(first, second))
    return 1
