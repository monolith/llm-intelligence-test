"""``python -m roster check <file>``, per ``SPEC-B.md``."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path

from roster import RosterError, find_conflicts, parse_roster

USAGE = "usage: python -m roster check <file>"


def main(argv: Sequence[str] | None = None) -> int:
    """Run the roster CLI and return the process exit code."""
    args = list(argv) if argv is not None else sys.argv[1:]

    if len(args) != 2 or args[0] != "check":
        print(USAGE, file=sys.stderr)
        return 2

    file_arg = args[1]
    try:
        text = Path(file_arg).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"{file_arg}: cannot read file", file=sys.stderr)
        return 2

    try:
        shifts = parse_roster(text)
    except RosterError as exc:
        print(f"{file_arg}: {exc}", file=sys.stderr)
        return 2

    conflicts = find_conflicts(shifts)
    if not conflicts:
        print("no conflicts")
        return 0

    for first, second in conflicts:
        print(
            f"{first.name}: {first.date.isoformat()} {first.start:%H:%M}-{first.end:%H:%M} "
            f"overlaps {second.date.isoformat()} {second.start:%H:%M}-{second.end:%H:%M}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
