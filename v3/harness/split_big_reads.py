"""Split any prescribed Read whose line span is too large for one Read call.

The Read tool refuses a call whose slice exceeds ~25k tokens; long noise documents
(dense transcript/ledger lines) blow that at 800 lines. Rewrite a rendered segment
instruction file so those reads become consecutive smaller reads of the SAME file
(the transcript verifier already collapses consecutive same-file offset reads into
one delivery, so this does not change what the run is allowed to do).

Usage: split_big_reads.py SEGMENT_FILE --max-lines 300
"""
import argparse, re

ap = argparse.ArgumentParser()
ap.add_argument("segment")
ap.add_argument("--max-lines", type=int, default=300)
a = ap.parse_args()

pat = re.compile(r"^(\d+)\. Read `([^`]+)` lines (\d+)–(\d+) \(offset (\d+), limit (\d+)\)(.*)$")
out, n = [], 0
for line in open(a.segment, encoding="utf-8").read().split("\n"):
    m = pat.match(line)
    if not m:
        if re.match(r"^\d+\. ", line):          # a non-Read numbered step: renumber it
            n += 1
            out.append(re.sub(r"^\d+\.", f"{n}.", line))
        else:
            out.append(line)
        continue
    path, off, lim, tail = m.group(2), int(m.group(5)), int(m.group(6)), m.group(7)
    start = off
    remaining = lim
    while remaining > 0:
        take = min(a.max_lines, remaining)
        n += 1
        out.append(f"{n}. Read `{path}` lines {start}–{start+take-1} (offset {start}, limit {take}){tail}")
        start += take
        remaining -= take
open(a.segment, "w", encoding="utf-8").write("\n".join(out))
print(f"{a.segment}: {n} steps after splitting at {a.max_lines} lines")
