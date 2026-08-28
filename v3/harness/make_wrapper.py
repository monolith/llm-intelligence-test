#!/usr/bin/env python3
"""make_wrapper.py -- embed one scored retelling, byte-identical, as a single
chapter inside a long "wrapper" document built from meaning-free filler text.

Purpose
-------
For the long variant of v3 of the LLM synthesis test, a scored retelling
(``v3/test-input/retellings/rNN-*.md``, roughly 1,400 words) needs to sit
inside a much larger document (50k-100k+ words) so that context handling can
be stress-tested while the actual scored material -- the "needle" -- stays
byte-for-byte auditable. The filler itself carries no information relevant to
scoring; it comes from a separate generator (see ``gen_long_noise.py``) and is
treated here as nothing more than "markdown text with paragraphs" -- this
tool does not parse or rely on any internal structure the filler happens to
have (headings, numbering, etc. inside the filler are just more paragraph
text as far as this tool is concerned).

What this tool does
--------------------
1. Splits the filler into chapters of ~``--chapter-words`` words, cut only at
   paragraph boundaries (paragraphs = blocks separated by a blank line), and
   gives each a generated heading ``## Chapter <n> -- <title>`` drawn from a
   small, seeded, all-common-word title vocabulary (no proper nouns), checked
   against an optional ``--collisions`` file of forbidden names.
2. Inserts the retelling, completely unmodified, as one additional chapter at
   a seeded position that is always strictly inside the document (never the
   first or last chapter), under a heading built from the retelling's own
   title line. The retelling's title line and framing note stay inside the
   chapter exactly as they appear in the source file.
3. Writes an outer ``# <title> -- assembled document (...)`` header and a
   ``*End of document.*`` footer.
4. Prints a small JSON summary to stdout so a verifier can later confirm
   where the needle landed.

A separate ``--verify`` mode re-opens an already-assembled wrapper file and
confirms the retelling text still appears exactly once, byte-identical, and
reports which chapter it is in.

Determinism
-----------
Standard library only. Everything randomized (chapter-insertion position,
generated chapter titles) is drawn from a single ``random.Random(seed)`` in a
fixed order, so the same seed plus the same input files plus the same
``--chapter-words`` always produces byte-identical output.
"""

from __future__ import annotations

import argparse
import bisect
import json
import random
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Title vocabulary -- deliberately plain, common, lower-case English words.
# None of these are proper nouns, so they should never need the --collisions
# check in practice; the check exists as a load-bearing second line of
# defense in case a word here happens to appear in a project's forbidden
# list, and is exercised directly by the tests (a forced collision, not a
# "probably fine" argument).
# ---------------------------------------------------------------------------
TITLE_ADJECTIVES = [
    "quiet", "distant", "narrow", "early", "later", "broken", "steady",
    "plain", "hollow", "patient", "brief", "worn", "closed", "open",
    "common", "private", "modest", "careful", "uncertain", "settled",
    "gradual", "local", "seasonal", "occasional", "ordinary", "familiar",
    "separate", "shared", "final", "idle",
]

TITLE_NOUNS = [
    "ledger", "account", "measure", "season", "harvest", "meeting",
    "letter", "record", "transfer", "balance", "interval", "boundary",
    "routine", "exchange", "interview", "inventory", "schedule",
    "reckoning", "summary", "notice", "proceeding", "allowance",
    "surplus", "register", "survey", "circular", "memorandum",
    "statement", "report", "margin",
]

CHAPTER_HEADING_RE = re.compile(r"^## Chapter (\d+) — ", re.MULTILINE)


# ---------------------------------------------------------------------------
# Exact-preservation I/O -- newline="" disables any newline translation so
# text read here is reproduced byte-for-byte when written back out.
# ---------------------------------------------------------------------------
def read_exact(path) -> str:
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def write_exact(path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# Filler -> paragraphs -> balanced chapters
# ---------------------------------------------------------------------------
def split_paragraphs(text: str) -> list[str]:
    """Split markdown text into paragraphs at blank-line boundaries.

    Makes no assumption about what is inside a paragraph -- a heading line,
    a list item, ordinary prose, whatever the filler generator produced -- it
    is all just paragraph text here.
    """
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []
    blocks = re.split(r"\n\s*\n+", normalized)
    return [b.strip() for b in blocks if b.strip()]


def balanced_chapter_split(paragraphs: list[str], chapter_words: int, min_chapters: int = 1) -> list[list[str]]:
    """Group paragraphs into chapters of ~chapter_words words each.

    Chooses the number of chapters as round(total_words / chapter_words)
    (never fewer than min_chapters, never more than len(paragraphs)), then
    places each internal boundary at whichever paragraph edge lands closest
    to its ideal cumulative-word target, while guaranteeing every chapter
    gets at least one paragraph.
    """
    if not paragraphs:
        return []

    word_counts = [len(p.split()) for p in paragraphs]
    total = sum(word_counts)
    n = len(paragraphs)

    if chapter_words <= 0:
        chapter_words = max(total, 1)

    ideal = max(1, round(total / chapter_words))
    num_chapters = max(min_chapters, ideal)
    num_chapters = min(num_chapters, n)

    if num_chapters <= 1:
        return [list(paragraphs)]

    cum = []
    running = 0
    for wc in word_counts:
        running += wc
        cum.append(running)

    boundaries: list[int] = []
    last = -1
    for i in range(1, num_chapters):
        remaining_after = num_chapters - i  # chapters still to place after this boundary
        target = total * i / num_chapters
        pos = bisect.bisect_left(cum, target)
        candidates = [j for j in (pos - 1, pos) if 0 <= j < n]
        if not candidates:
            candidates = [n - 1]
        best = min(candidates, key=lambda j: abs(cum[j] - target))
        max_allowed = n - 1 - remaining_after
        best = min(best, max_allowed)
        best = max(best, last + 1)
        boundaries.append(best)
        last = best

    chapters = []
    start = 0
    for b in boundaries:
        end = b + 1
        chapters.append(paragraphs[start:end])
        start = end
    chapters.append(paragraphs[start:])
    return chapters


# ---------------------------------------------------------------------------
# Collision-checked title generation
# ---------------------------------------------------------------------------
def load_collisions(path) -> str:
    """Return the lower-cased text of a forbidden-names file, or "" if none."""
    if not path:
        return ""
    return read_exact(path).lower()


def _word_collides(word: str, forbidden_blob: str) -> bool:
    if not forbidden_blob:
        return False
    return re.search(rf"\b{re.escape(word.lower())}\b", forbidden_blob) is not None


def generate_title(rng: random.Random, forbidden_blob: str, max_tries: int = 500) -> str:
    for _ in range(max_tries):
        adjective = rng.choice(TITLE_ADJECTIVES)
        noun = rng.choice(TITLE_NOUNS)
        if _word_collides(adjective, forbidden_blob) or _word_collides(noun, forbidden_blob):
            continue
        return f"The {adjective.capitalize()} {noun.capitalize()}"
    raise RuntimeError(
        "could not generate a chapter title that avoids the collisions list "
        "after many attempts -- the collisions file may be too broad"
    )


# ---------------------------------------------------------------------------
# Retelling heading extraction
# ---------------------------------------------------------------------------
def extract_retelling_heading_text(retelling_text: str) -> str:
    """The retelling's own title-line text, with the markdown '#' stripped.

    e.g. "# Retelling 01 — Vira Toland, ..." -> "Retelling 01 — Vira Toland, ..."
    """
    first_line = retelling_text.splitlines()[0] if retelling_text.splitlines() else ""
    return first_line.lstrip("#").strip()


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------
def build_wrapper(
    retelling_path,
    filler_path,
    out_path,
    seed: int,
    chapter_words: int = 2000,
    title: str = "Untitled",
    collisions_path=None,
) -> dict:
    retelling_text = read_exact(retelling_path)
    filler_text = read_exact(filler_path)
    forbidden_blob = load_collisions(collisions_path)

    paragraphs = split_paragraphs(filler_text)
    filler_chapters = balanced_chapter_split(paragraphs, chapter_words, min_chapters=2)

    if len(filler_chapters) < 2:
        raise ValueError(
            "filler text has too few paragraphs to place the retelling "
            "strictly inside the document (need at least 2 filler chapters "
            "so the retelling is never first or last)"
        )

    rng = random.Random(seed)
    # 0-indexed slot, strictly between the first and last filler chapter.
    insert_pos = rng.randint(1, len(filler_chapters) - 1)

    heading_text = extract_retelling_heading_text(retelling_text)

    chapter_sections: list[str] = []
    chapter_num = 0
    retelling_chapter_num = None

    for i, para_group in enumerate(filler_chapters):
        if i == insert_pos:
            chapter_num += 1
            chapter_sections.append(f"## Chapter {chapter_num} — {heading_text}\n\n{retelling_text}")
            retelling_chapter_num = chapter_num

        chapter_num += 1
        gen_title = generate_title(rng, forbidden_blob)
        body = "\n\n".join(para_group)
        chapter_sections.append(f"## Chapter {chapter_num} — {gen_title}\n\n{body}")

    body_joined = "\n\n".join(chapter_sections)
    total_words = len(body_joined.split())
    header = f"# {title} — assembled document ({total_words} words; seed {seed})"
    footer = "*End of document.*"
    document = "\n\n".join([header, body_joined, footer])

    idx = document.find(retelling_text)
    start = len(document[:idx].split())
    span_words = len(retelling_text.split())
    end = start + span_words

    write_exact(out_path, document)

    return {
        "out": str(out_path),
        "words": total_words,
        "chapters": len(chapter_sections),
        "retelling_chapter": retelling_chapter_num,
        "retelling_word_span": [start, end],
    }


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
def verify_wrapper(wrapper_path, retelling_path) -> dict:
    wrapper_text = read_exact(wrapper_path)
    retelling_text = read_exact(retelling_path)

    occurrences = wrapper_text.count(retelling_text)
    chapter = None
    if occurrences == 1:
        idx = wrapper_text.find(retelling_text)
        preceding = wrapper_text[:idx]
        matches = list(CHAPTER_HEADING_RE.finditer(preceding))
        if matches:
            chapter = int(matches[-1].group(1))

    return {
        "verified": occurrences == 1 and chapter is not None,
        "occurrences": occurrences,
        "chapter": chapter,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "")
    parser.add_argument("--retelling", help="path to the scored retelling markdown file")
    parser.add_argument("--filler", help="path to the meaning-free filler markdown file")
    parser.add_argument("--out", help="path to write the assembled wrapper document")
    parser.add_argument("--seed", type=int, help="seed for deterministic assembly")
    parser.add_argument("--chapter-words", type=int, default=2000, help="target words per filler chapter (default 2000)")
    parser.add_argument("--title", default="Untitled", help="document title used in the header line")
    parser.add_argument("--collisions", default=None, help="optional file of forbidden names to avoid in generated titles")
    parser.add_argument("--verify", default=None, metavar="FILE", help="verify mode: path to an already-assembled wrapper file")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verify:
        if not args.retelling:
            parser.error("--verify requires --retelling")
        result = verify_wrapper(args.verify, args.retelling)
        print(json.dumps(result))
        return 0 if result["verified"] else 1

    missing = [name for name in ("retelling", "filler", "out", "seed") if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join(f"--{m}" for m in missing))

    result = build_wrapper(
        retelling_path=args.retelling,
        filler_path=args.filler,
        out_path=args.out,
        seed=args.seed,
        chapter_words=args.chapter_words,
        title=args.title,
        collisions_path=args.collisions,
    )
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
