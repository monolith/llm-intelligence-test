#!/usr/bin/env python3
"""apply_triage_b.py — apply the six (b) prose-overlap paraphrases.

Source: `audit-triage.md` section "## (b) Real material defects" — six
near-verbatim (12+ word) copies of an original story's own narration into a
retelling that covers the same ground. This script applies the exact
old -> new paraphrase given for each, one replacement per file.

Matching is whitespace-normalised: any run of whitespace in the `old`
string matches any run of whitespace in the target file (so a stray double
space or a line-wrapped copy still counts as a match), but every other
character must match exactly. If an `old` string is not found exactly once
in its target file, the script fails loudly (prints the file and an old-
string snippet) and, in apply mode, exits non-zero without writing anything.

Usage:
    python3 apply_triage_b.py            # apply all six edits
    python3 apply_triage_b.py --check    # report presence only; no writes

Exit codes:
    0  success (--check: all six present exactly once;
                apply: all edits applied and all six word counts in range)
    1  failure (--check: one or more missing/not-unique;
                apply: an edit could not be applied, or a resulting word
                count falls outside 1,200-1,800)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent  # v2/

WORD_COUNT_MIN = 1200
WORD_COUNT_MAX = 1800

EDITS = [
    {
        "file": REPO_ROOT / "test-input/retellings/r02-a-clerks-son-remembers.md",
        "old": (
            "On the morning of 6 March 1898 a work train came down off the "
            "quarry grade without brakes enough to hold her."
        ),
        "new": (
            "On the morning of 6 March 1898 a work train started down the "
            "quarry grade with nothing left to hold her."
        ),
    },
    {
        "file": REPO_ROOT / "test-input/retellings/r04-what-the-creek-gave-back.md",
        "old": (
            "The state's flood-control cut took Sallow Creek out of its bed "
            "for eleven weeks and the gorge was dry to the gravel."
        ),
        "new": (
            "A state flood-control project had pulled Sallow Creek out of "
            "its bed for eleven weeks, leaving the gorge dry down to the "
            "gravel."
        ),
    },
    {
        "file": REPO_ROOT / "test-input/retellings/r05-the-engines-my-grandfather-bought.md",
        "old": (
            "kept the company's books from the age of eighteen, which is "
            "to say for thirty-nine years, because she was better at it than "
            "anybody her father could hire."
        ),
        "new": (
            "kept the company's books from the age of eighteen, which is "
            "to say for thirty-nine years, because nobody her father ever "
            "hired did the work as well as she did."
        ),
    },
    {
        "file": REPO_ROOT / "test-input/retellings/r11-sentinel-ghost-lies-down.md",
        "old": (
            "kept a ruled book of every night the sound came — the date, "
            "the day's high, the night's low, whether she spoke, and the "
            "hour."
        ),
        "new": (
            "kept a ruled book of every night the sound came: the date, how "
            "warm the day had been, how cold the night ran, whether she "
            "spoke, and at what hour."
        ),
    },
    {
        "file": REPO_ROOT / "test-input/retellings/r12-our-valley-school-history.md",
        "old": (
            "The last night the bridge was heard was the ninth of February, "
            "1954. In March of that year the railroad rebuilt the bridge to "
            "carry the new diesel engines, and put new bearings under the "
            "long span, and from that month to this the valley has not "
            "heard a sound."
        ),
        "new": (
            "The last night the bridge was heard was the ninth of February, "
            "1954. The following month the railroad rebuilt the bridge to "
            "carry the new diesel engines, and put new bearings under the "
            "long span, and from that time to this the valley has not heard "
            "a sound."
        ),
    },
    {
        "file": REPO_ROOT / "test-input/retellings/r03-the-night-book.md",
        "old": (
            "Five columns. The date. The day's high. The night's low. "
            "Whether she spoke. And the hour."
        ),
        "new": (
            "Five columns. The date, how warm the day ran, how cold the "
            "night got, whether she spoke, and the hour of it."
        ),
    },
]


def build_ws_pattern(s: str) -> re.Pattern:
    """Compile `s` into a regex where every run of whitespace becomes \\s+
    (matches any run of whitespace) and everything else is matched
    literally."""
    parts = re.split(r"\s+", s.strip())
    return re.compile(r"\s+".join(re.escape(p) for p in parts))


def snippet(s: str, n: int = 90) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n] + "..."


# Mirrors audit.py's word_count_after_framing(): strips leading blank/
# heading/blockquote/italic framing lines before counting, so counts here
# agree with the audit's own 1,200-1,800 check. Duplicated (not imported)
# to keep this script standalone.
def strip_framing(text: str) -> str:
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if (
            line == ""
            or line.startswith("#")
            or line.startswith(">")
            or (line.startswith("*") and line.endswith("*") and not line.startswith("**"))
            or (line.startswith("_") and line.endswith("_"))
        ):
            i += 1
            continue
        break
    return "\n".join(lines[i:])


def word_count_after_framing(text: str) -> int:
    return len(strip_framing(text).split())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report whether each old string is present exactly once; make no changes",
    )
    args = parser.parse_args()

    # Phase 1: verify every old string is present exactly once, in every
    # target file, before writing anything.
    problems: list[str] = []
    matches_by_index: dict[int, re.Match] = {}
    texts_by_path: dict[Path, str] = {}

    for i, edit in enumerate(EDITS, 1):
        path: Path = edit["file"]
        old: str = edit["old"]

        if not path.exists():
            problems.append(f"[{i}] MISSING FILE: {path}")
            continue

        if path not in texts_by_path:
            texts_by_path[path] = path.read_text(encoding="utf-8")
        text = texts_by_path[path]

        pattern = build_ws_pattern(old)
        found = list(pattern.finditer(text))

        if len(found) == 0:
            problems.append(f"[{i}] NOT FOUND in {path}\n      old: {snippet(old)}")
        elif len(found) > 1:
            problems.append(
                f"[{i}] FOUND {len(found)} TIMES (expected exactly 1) in {path}\n      old: {snippet(old)}"
            )
        else:
            matches_by_index[i] = found[0]
            if args.check:
                print(f"[{i}] present (1x): {path}")

    if args.check:
        if problems:
            print()
            for p in problems:
                print(p, file=sys.stderr)
            print(f"\nCHECK: {len(problems)} of {len(EDITS)} old string(s) missing or not unique.")
            return 1
        print(f"\nCHECK: all {len(EDITS)} old strings present exactly once. No files modified.")
        return 0

    # Apply mode: fail loudly and write nothing if any old string could not
    # be matched exactly once.
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        print(
            f"\nFAILED: {len(problems)} of {len(EDITS)} edit(s) could not be applied "
            "as written. No files were modified.",
            file=sys.stderr,
        )
        return 1

    # All edits verified unique — apply them.
    edited_paths: list[Path] = []
    for i, edit in enumerate(EDITS, 1):
        path = edit["file"]
        new = edit["new"]
        text = texts_by_path[path]
        m = matches_by_index[i]
        text = text[: m.start()] + new + text[m.end() :]
        texts_by_path[path] = text
        if path not in edited_paths:
            edited_paths.append(path)
        print(f"[{i}] applied edit to {path}")

    for path in edited_paths:
        path.write_text(texts_by_path[path], encoding="utf-8")

    # Report word counts, fail if any is out of range.
    print()
    out_of_range = False
    for path in edited_paths:
        wc = word_count_after_framing(path.read_text(encoding="utf-8"))
        in_range = WORD_COUNT_MIN <= wc <= WORD_COUNT_MAX
        status = "OK" if in_range else "OUT OF RANGE"
        print(f"{path}: {wc} words [{status}]")
        if not in_range:
            out_of_range = True

    if out_of_range:
        print(
            f"\nFAILED: one or more edited retellings fall outside "
            f"{WORD_COUNT_MIN}-{WORD_COUNT_MAX} words after editing.",
            file=sys.stderr,
        )
        return 1

    print(f"\nOK: all {len(edited_paths)} edited retellings within {WORD_COUNT_MIN}-{WORD_COUNT_MAX} words.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
