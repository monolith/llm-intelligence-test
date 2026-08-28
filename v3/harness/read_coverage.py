"""Compare what a segment PRESCRIBED against what the reader actually read.

The transcript verifier only checks which files were opened. A Read whose slice
exceeds the tool's ~25k-token cap fails, and a reader that does not retry it
silently loses that span — including, in the worst case, the carried notes.
This walks every captured transcript and reports, per segment, the prescribed
line span of each file against the union of spans actually returned.

Usage: read_coverage.py [--model M ...] [--only-gaps]
"""
import argparse, glob, json, os, re

AP = argparse.ArgumentParser()
AP.add_argument("--root", default="/home/anatoly/llm-intelligence-test/v3")
AP.add_argument("--model", action="append")
AP.add_argument("--only-gaps", action="store_true")
A = AP.parse_args()

STEP = re.compile(r"^\d+\. Read `([^`]+)` lines (\d+)–(\d+) ")
CALL = re.compile(r"\[tool_use Read: (\{.*?\})\]", re.S)


def merge(spans):
    out = []
    for s, e in sorted(spans):
        if out and s <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def gaps(want, have):
    ws, we = want
    missing, cur = [], ws
    for s, e in have:
        if e < cur:
            continue
        if s > cur:
            missing.append((cur, min(s - 1, we)))
        cur = max(cur, e + 1)
        if cur > we:
            break
    if cur <= we:
        missing.append((cur, we))
    return [(s, e) for s, e in missing if s <= e]


for model in (A.model or ["haiku", "sonnet", "opus", "fable"]):
    d = f"{A.root}/runs/{model}/long-notes/ingest"
    segs = sorted(glob.glob(f"{d}/transcript-seg*.jsonl"),
                  key=lambda p: int(re.search(r"seg(\d+)", p).group(1)))
    for tp in segs:
        n = int(re.search(r"seg(\d+)", tp).group(1))
        sp = f"{d}/segment-{n}.md"
        if not os.path.exists(sp):
            print(f"{model} seg{n}: no segment file"); continue
        want = {}
        for line in open(sp, encoding="utf-8"):
            m = STEP.match(line)
            if m:
                f, s, e = m.group(1), int(m.group(2)), int(m.group(3))
                b = os.path.basename(f)
                want[b] = (min(want.get(b, (s, e))[0], s), max(want.get(b, (s, e))[1], e))
        rows = [json.loads(l) for l in open(tp)]
        have, pending = {}, None
        for r in rows:
            t = r.get("text") or ""
            m = CALL.search(t)
            if m:
                c = json.loads(m.group(1))
                pending = c
                continue
            if pending and t.startswith("[tool_result"):
                ok = "exceeds maximum allowed tokens" not in t
                if ok:
                    b = os.path.basename(pending["file_path"])
                    off = pending.get("offset") or 1
                    lim = pending.get("limit")
                    end = off + lim - 1 if lim else 10 ** 9
                    have.setdefault(b, []).append([off, end])
                pending = None
        bad = []
        for b, span in want.items():
            g = gaps(span, merge(have.get(b, [])))
            if g:
                lost = sum(e - s + 1 for s, e in g)
                kind = "NOTES" if b.startswith("notes-") else "file"
                bad.append(f"{kind} {b} missing {lost} lines {g[:3]}")
        if bad:
            print(f"{model} seg{n}: " + "; ".join(bad))
        elif not A.only_gaps:
            print(f"{model} seg{n}: complete")
