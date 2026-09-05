"""Build the last ingest segments of a long-notes chain by hand, with more material per segment
than the plan's budget allows, for a chain whose own notes have grown so large that the planner
can only fit a few hundred lines of new material per segment.

Usage:
  tail_segments.py --model fable --after 22 --from-offset 1358 \
      --doc v3/distractors/long/L4-mixed.md --parts 2 [--max-lines 800 --split-lines 300 --split-bytes 40000]

Writes segment-<after+1>.md ... segment-<after+parts>.md into the model's ingest dir, in exactly the
format plan_segments.render_segment uses (so split_big_reads.py and verify_transcript.py treat them
like any other segment): read the previous notes, read this segment's share of the remaining lines
of --doc, answer the document's surface question (from its L{n}-question.txt) after the last chunk,
write notes. Verification uses the segment file itself as the allowed list.
"""
import argparse, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_segments import parse_long_question  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--root", default="v3")
ap.add_argument("--model", required=True)
ap.add_argument("--after", type=int, required=True, help="last completed segment")
ap.add_argument("--from-offset", type=int, required=True, help="first unread 1-based line of --doc")
ap.add_argument("--doc", required=True)
ap.add_argument("--parts", type=int, default=2)
ap.add_argument("--max-lines", type=int, default=800)
ap.add_argument("--split-lines", type=int, default=300)
ap.add_argument("--split-bytes", type=int, default=40000)
a = ap.parse_args()

root = Path(a.root).resolve()
ingest = root / "runs" / a.model / "long-notes" / "ingest"
doc = Path(a.doc).resolve()
qfile = doc.with_name(doc.name.split("-")[0] + "-question.txt")
question = parse_long_question(qfile) if qfile.exists() else None
total = len(doc.read_text(encoding="utf-8").splitlines())
remaining = total - a.from_offset + 1
per = -(-remaining // a.parts)
start = a.from_offset
for p in range(a.parts):
    seg = a.after + 1 + p
    prev = ingest / f"notes-{seg-1}.md"
    end = min(start + per - 1, total)
    lines = [f"Segment {seg} instructions:"]
    n = 1
    nl = len(prev.read_text(encoding="utf-8").splitlines()) if prev.exists() else a.max_lines
    lines.append(f"{n}. Read `{prev}` lines 1–{nl} (offset 1, limit {nl}) — acknowledge.")
    n += 1
    off = start
    while off <= end:
        lim = min(a.max_lines, end - off + 1)
        last = off + lim - 1 >= end
        action = f"answer the question in one sentence: {question}" if (last and question and p == a.parts - 1) else "acknowledge"
        lines.append(f"{n}. Read `{doc}` lines {off}–{off+lim-1} (offset {off}, limit {lim}) — {action}.")
        n += 1
        off += lim
    lines.append(f"{n}. Write your retention notes to `{ingest}/notes-{seg}.md` and stop.")
    out = ingest / f"segment-{seg}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, str(root / "harness" / "split_big_reads.py"), str(out),
                    "--max-lines", str(a.split_lines), "--max-bytes", str(a.split_bytes)], check=True)
    steps = sum(1 for l in out.read_text(encoding="utf-8").splitlines() if l[:1].isdigit())
    print(f"wrote {out}: {doc.name} lines {start}-{end}; {steps} steps")
    start = end + 1
