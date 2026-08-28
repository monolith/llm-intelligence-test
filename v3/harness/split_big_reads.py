"""Split any prescribed Read that one Read call cannot return.

The Read tool refuses a slice over ~25k tokens. Two things blow that: many lines
(dense noise documents at 800 lines) and few but very long lines (a reader's own
retention notes, where 276 lines were 30,086 tokens). Splitting on line count
alone missed the second case, and a reader whose notes read fails loses its whole
carried memory in silence. So split on BOTH: line count and measured bytes.

Rewrite a rendered segment instruction file so oversized reads become consecutive
smaller reads of the SAME file (the transcript verifier collapses consecutive
same-file offset reads into one delivery, so this does not change what the run is
allowed to read).

Usage: split_big_reads.py SEGMENT_FILE [--max-lines 300] [--max-bytes 40000]
"""
import argparse, os, re

ap = argparse.ArgumentParser()
ap.add_argument("segment")
ap.add_argument("--max-lines", type=int, default=300)
ap.add_argument("--max-bytes", type=int, default=40000)
a = ap.parse_args()

pat = re.compile(r"^(\d+)\. Read `([^`]+)` lines (\d+)–(\d+) \(offset (\d+), limit (\d+)\)(.*)$")

_sizes: dict[str, list[int]] = {}


def line_bytes(path: str) -> list[int]:
    """Byte length of each line, 1-indexed (index 0 unused)."""
    if path not in _sizes:
        if not os.path.exists(path):
            _sizes[path] = []
        else:
            with open(path, "rb") as fh:
                _sizes[path] = [0] + [len(l) for l in fh]
    return _sizes[path]


def chunks(path: str, off: int, lim: int) -> list[tuple[int, int]]:
    """Split [off, off+lim) into pieces under both the line and the byte cap."""
    sizes = line_bytes(path)
    out, start, taken, acc = [], off, 0, 0
    for ln in range(off, off + lim):
        b = sizes[ln] if ln < len(sizes) else 0
        # close the current piece before it would break either cap
        if taken and (taken >= a.max_lines or acc + b > a.max_bytes):
            out.append((start, taken))
            start, taken, acc = ln, 0, 0
        taken += 1
        acc += b
    if taken:
        out.append((start, taken))
    return out


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
    for start, take in chunks(path, off, lim):
        n += 1
        out.append(f"{n}. Read `{path}` lines {start}–{start+take-1} (offset {start}, limit {take}){tail}")
open(a.segment, "w", encoding="utf-8").write("\n".join(out))
print(f"{a.segment}: {n} steps after splitting at {a.max_lines} lines / {a.max_bytes} bytes")
