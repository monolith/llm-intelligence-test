"""``python -m roster check <file>``.

Exit code 0 when the roster holds no conflicts, 1 when it holds some, and 2 when
the file cannot be read, cannot be parsed, or the command line is not understood.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from roster.core import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"
COMMAND = "check"

NO_CONFLICTS = 0
CONFLICTS_FOUND = 1
FAILED = 2


def _shown(shift: Shift) -> str:
    """A shift as ``YYYY-MM-DD HH:MM-HH:MM``, with the end time as it was written."""
    return f"{shift.date.isoformat()} {shift.start:%H:%M}-{shift.end:%H:%M}"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2 or args[0] != COMMAND:
        print(USAGE, file=sys.stderr)
        return FAILED

    name = args[1]
    try:
        text = Path(name).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"{name}: cannot read file", file=sys.stderr)
        return FAILED

    try:
        shifts = parse_roster(text)
    except RosterError as exc:
        print(f"{name}: {exc}", file=sys.stderr)
        return FAILED

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return NO_CONFLICTS
    for first, second in conflicts:
        print(f"{first.name}: {_shown(first)} overlaps {_shown(second)}")
    return CONFLICTS_FOUND
