"""Segment planner for the v3 long-variant ingest ("long-notes" / "long-reread" administration).

The fixed four-segment schedule in PROTOCOL-LONG.md ("Segment 1: r01-r06 ... then
L1 -> notes-1", etc.) is too coarse for a fresh-reader-per-segment protocol: the
wrapped retellings run ~62k words and the long-noise documents run ~220k words
each, so a single one of those documents alone can blow past a reader's context
budget. This planner replaces the fixed schedule with one driven by an actual
token budget: it walks the fixed ingest ORDER (retellings + their noise slots,
long noise after r06/r12/r18/r24) and cuts a new segment ("fresh reader") every
time the running token estimate would exceed --budget, splitting documents by
LINE RANGE wherever a cut falls mid-document. Every prescribed Read also obeys
--max-lines (the Read tool returns large files in parts).

Token estimate: words * 1.35 (see PROTOCOL-LONG.md / the task brief). Each
segment after the first starts by reading the previous segment's notes file;
that read is costed at the notes file's actual word count when the file
already exists on disk, else at an assumed 6,000 words.

Usage:
    python plan_segments.py --root v3 --model sonnet --budget 110000 \\
        --max-lines 800 --out v3/runs/sonnet/long-notes/ingest/plan.json
    python plan_segments.py --root v3 --model sonnet --out ... --render 3
    python plan_segments.py --root v3 --model sonnet --out ... --verify-allowed 3
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
from pathlib import Path
from typing import Optional

WORDS_TO_TOKENS = 1.35
ASSUMED_NOTES_WORDS = 6000

WRAPPED_INDICES = {3, 6, 9, 12, 15, 18, 21, 24}
LONG_AFTER = {6: 1, 12: 2, 18: 3, 24: 4}


# ---------------------------------------------------------------------------
# small text-file parsers
# ---------------------------------------------------------------------------


def parse_order(root: Path) -> dict[int, dict[str, str]]:
    """Parse v3/distractors/ORDER.md's pipe table -> {slot: {"after":..., "file":..., "kind":...}}."""
    text = (root / "distractors" / "ORDER.md").read_text(encoding="utf-8")
    rows: dict[int, dict[str, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 4 or not cells[0].isdigit():
            continue
        slot = int(cells[0])
        rows[slot] = {"after": cells[1], "file": cells[2], "kind": cells[3]}
    return rows


def parse_short_questions(root: Path) -> dict[int, str]:
    """Parse v3/distractors/questions.md -> {slot: question text} (Q only, never the A)."""
    text = (root / "distractors" / "questions.md").read_text(encoding="utf-8")
    out: dict[int, str] = {}
    for m in re.finditer(r"^## (\d+)\.[^\n]*\n\*\*Q:\*\*\s*(.+?)\s*\n\*\*A:\*\*", text, flags=re.M):
        out[int(m.group(1))] = m.group(2).strip()
    return out


def parse_long_question(path: Path) -> Optional[str]:
    """Parse an L{n}-question.txt file -> the question text only (never the answer line)."""
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^Q:\s*(.+)$", text, flags=re.M)
    return m.group(1).strip() if m else None


def glob_one(root: Path, pattern: str) -> Path:
    matches = sorted(root.glob(pattern))
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly one match for {pattern!r} under {root}, found {len(matches)}")
    return matches[0]


# ---------------------------------------------------------------------------
# document model
# ---------------------------------------------------------------------------


def line_word_counts(path: Path) -> list[int]:
    return [len(line.split()) for line in path.read_text(encoding="utf-8").splitlines()]


def file_word_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def build_docs(root: Path) -> list[dict]:
    """Build the fixed ingest-order document list: for i in 1..24, retelling i, then
    noise slot i, then (after i in {6,12,18,24}) the corresponding long-noise document.
    """
    root = Path(root)
    order = parse_order(root)
    short_q = parse_short_questions(root)
    docs: list[dict] = []

    for i in range(1, 25):
        ii = f"{i:02d}"

        if i in WRAPPED_INDICES:
            rfile = root / "test-input" / "long" / f"r{ii}-long.md"
            if not rfile.exists():
                raise FileNotFoundError(f"expected wrapped retelling at {rfile}")
            kind = "wrapped"
        else:
            rfile = glob_one(root, f"test-input/retellings/r{ii}-*.md")
            kind = "retelling"
        docs.append({"doc_id": f"r{ii}", "kind": kind, "file": rfile, "label_base": f"r{ii}", "question": None})

        slot = order[i]
        nfile = root / "distractors" / slot["file"]
        docs.append(
            {
                "doc_id": f"slot{i}",
                "kind": "noise",
                "file": nfile,
                "label_base": f"slot {i}",
                "question": short_q.get(i),
            }
        )

        if i in LONG_AFTER:
            n = LONG_AFTER[i]
            lfile = glob_one(root, f"distractors/long/L{n}-*.md")
            qfile = root / "distractors" / "long" / f"L{n}-question.txt"
            docs.append(
                {
                    "doc_id": f"L{n}",
                    "kind": "long-noise",
                    "file": lfile,
                    "label_base": f"L{n}",
                    "question": parse_long_question(qfile),
                }
            )

    return docs


# ---------------------------------------------------------------------------
# chunking
# ---------------------------------------------------------------------------


def _max_lines_within_budget(prefix: list[int], start0: int, cap: int, target_words: float) -> int:
    """Largest L in [0, cap] such that sum(word_counts[start0:start0+L]) <= target_words."""
    if target_words < 0 or cap <= 0:
        return 0
    hi = start0 + cap
    threshold = prefix[start0] + target_words
    j = bisect.bisect_right(prefix, threshold, start0, hi + 1) - 1
    return max(j - start0, 0)


def notes_read_word_count(notes_path: Path) -> int:
    """Actual word count of a previous segment's notes file, or the 6,000-word assumption
    if it does not (yet) exist on disk."""
    if notes_path.exists():
        return file_word_count(notes_path)
    return ASSUMED_NOTES_WORDS


def build_plan(root: str | Path, model: str, budget: int, max_lines: int) -> list[dict]:
    root = Path(root)
    notes_dir = root / "runs" / model / "long-notes" / "ingest"
    docs = build_docs(root)

    segments: list[dict] = []
    seg_index = 1
    cur_reads: list[dict] = []
    cur_tokens = 0.0

    def start_segment(first: bool) -> None:
        nonlocal cur_reads, cur_tokens
        cur_reads = []
        cur_tokens = 0.0
        if not first:
            prev_k = seg_index - 1
            notes_path = notes_dir / f"notes-{prev_k}.md"
            if notes_path.exists():
                total_lines = len(notes_path.read_text(encoding="utf-8").splitlines())
                limit = min(max(total_lines, 1), max_lines)
                words = file_word_count(notes_path)
            else:
                limit = max_lines
                words = ASSUMED_NOTES_WORDS
            cur_reads.append(
                {
                    "file": str(notes_path),
                    "offset": 1,
                    "limit": limit,
                    "kind": "notes",
                    "label": f"notes {prev_k}",
                    "question": None,
                    "acknowledge": True,
                }
            )
            cur_tokens += words * WORDS_TO_TOKENS

    def finalize_segment() -> None:
        segments.append(
            {
                "index": seg_index,
                "reads": cur_reads,
                "est_tokens": round(cur_tokens, 2),
                "notes_out": f"notes-{seg_index}.md",
            }
        )

    start_segment(first=True)

    for doc in docs:
        path: Path = doc["file"]
        word_counts = line_word_counts(path)
        total = len(word_counts)
        prefix = [0] * (total + 1)
        for idx, w in enumerate(word_counts):
            prefix[idx + 1] = prefix[idx] + w

        offset = 1  # 1-based line offset, matching the Read tool
        doc_reads: list[dict] = []
        while offset <= total:
            remaining_budget = budget - cur_tokens
            target_words = remaining_budget / WORDS_TO_TOKENS
            cap = min(max_lines, total - offset + 1)
            length = _max_lines_within_budget(prefix, offset - 1, cap, target_words)

            if length == 0:
                made_progress_this_segment = len(cur_reads) > (1 if seg_index > 1 else 0)
                if not made_progress_this_segment:
                    # Nothing but the mandatory notes-read (or nothing at all) is in this
                    # fresh segment yet: force at least one line so the plan always makes
                    # forward progress, even if that overshoots the budget.
                    length = 1
                else:
                    finalize_segment()
                    seg_index += 1
                    start_segment(first=False)
                    continue

            chunk_words = prefix[offset - 1 + length] - prefix[offset - 1]
            read = {
                "file": str(path),
                "offset": offset,
                "limit": length,
                "kind": doc["kind"],
                "label": None,  # filled in once the doc's total part count is known
                "question": None,
                "acknowledge": True,
            }
            cur_reads.append(read)
            doc_reads.append(read)
            cur_tokens += chunk_words * WORDS_TO_TOKENS
            offset += length

        n_parts = len(doc_reads)
        for j, read in enumerate(doc_reads, start=1):
            read["label"] = doc["label_base"] if n_parts == 1 else f"{doc['label_base']} part {j}/{n_parts}"
            if j == n_parts and doc["question"]:
                read["question"] = doc["question"]
                read["acknowledge"] = False

    finalize_segment()
    return segments


# ---------------------------------------------------------------------------
# rendering / verification helpers
# ---------------------------------------------------------------------------


def notes_dir_for(root: str | Path, model: str) -> str:
    return str(Path(root) / "runs" / model / "long-notes" / "ingest")


def render_segment(segment: dict, notes_dir: str) -> str:
    lines = [f"Segment {segment['index']} instructions:"]
    for i, r in enumerate(segment["reads"], start=1):
        a = r["offset"]
        b = a + r["limit"] - 1
        if r["question"]:
            action = f"answer the question in one sentence: {r['question']}"
        else:
            action = "acknowledge"
        lines.append(f"{i}. Read `{r['file']}` lines {a}\u2013{b} (offset {a}, limit {r['limit']}) \u2014 {action}.")
    n = len(segment["reads"]) + 1
    notes_path = f"{notes_dir}/{segment['notes_out']}"
    lines.append(f"{n}. Write your retention notes to `{notes_path}` and stop.")
    return "\n".join(lines)


def verify_allowed_basenames(segment: dict) -> list[str]:
    """One basename per distinct file in the segment's reads, in order (consecutive reads
    of the same file collapse to one delivery, matching verify_transcript.py), plus the
    notes file the segment writes at the end.
    """
    basenames: list[str] = []
    prev = None
    for r in segment["reads"]:
        bn = os.path.basename(r["file"])
        if bn != prev:
            basenames.append(bn)
            prev = bn
    basenames.append(segment["notes_out"])
    return basenames


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--budget", type=int, default=110000)
    ap.add_argument("--max-lines", type=int, default=800, dest="max_lines")
    ap.add_argument("--out", required=True)
    ap.add_argument("--render", type=int, default=None)
    ap.add_argument("--verify-allowed", type=int, default=None, dest="verify_allowed")
    args = ap.parse_args()

    segments = build_plan(args.root, args.model, args.budget, args.max_lines)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(segments, indent=2), encoding="utf-8")

    printed = False
    if args.render is not None:
        seg = next((s for s in segments if s["index"] == args.render), None)
        if seg is None:
            raise SystemExit(f"no segment with index {args.render} (plan has {len(segments)} segments)")
        print(render_segment(seg, notes_dir_for(args.root, args.model)))
        printed = True
    if args.verify_allowed is not None:
        seg = next((s for s in segments if s["index"] == args.verify_allowed), None)
        if seg is None:
            raise SystemExit(f"no segment with index {args.verify_allowed} (plan has {len(segments)} segments)")
        print(" ".join(f'--allowed "{b}"' for b in verify_allowed_basenames(seg)))
        printed = True
    if not printed:
        print(f"{len(segments)} segment(s) written to {out_path}")


if __name__ == "__main__":
    main()
