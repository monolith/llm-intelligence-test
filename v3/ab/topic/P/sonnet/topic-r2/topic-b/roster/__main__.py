"""``python -m roster check <file>`` -- print scheduling conflicts."""

from __future__ import annotations

import sys
from pathlib import Path

from roster import RosterError, Shift, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def _format_shift(shift: Shift) -> str:
    return f"{shift.date.isoformat()} {shift.start.strftime('%H:%M')}-{shift.end.strftime('%H:%M')}"


def main(argv: list[str] | None = None) -> int:
    """Run the command line and return the process exit code."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    file = args[1]
    try:
        text = Path(file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
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
        print(f"{first.name}: {_format_shift(first)} overlaps {_format_shift(second)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
