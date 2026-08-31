#!/usr/bin/env python3
"""One sheet for every cell run: score, and what it cost in tokens, turns, calls and dollars.

Dollars are notional on a subscription plan; turns and tool calls are what a run actually
spends and what a rate limit is denominated in, so all four are reported side by side.
"""
import argparse, glob, json, os, re

AP = argparse.ArgumentParser()
AP.add_argument("--root", default="v3")
AP.add_argument("--prices", default="v2/harness/prices.json")
AP.add_argument("--out")
A = AP.parse_args()

P = json.load(open(A.prices))
IDS = {"haiku": "claude-haiku-4-5", "sonnet": "claude-sonnet-5",
       "opus": "claude-opus-5", "fable": "claude-fable-5"}


def usage(paths):
    fresh = cread = cwrite = out = turns = calls = 0
    for p in paths:
        if not os.path.exists(p):
            continue
        for line in open(p):
            r = json.loads(line)
            if r.get("role") != "assistant":
                continue
            turns += 1
            if "[tool_use " in (r.get("text") or ""):
                calls += 1
            u = r.get("usage") or {}
            fresh += u.get("input_tokens") or 0
            cread += u.get("cache_read_input_tokens") or 0
            cwrite += u.get("cache_creation_input_tokens") or 0
            out += u.get("output_tokens") or 0
    return fresh, cread, cwrite, out, turns, calls


def cost(model, f, cr, cw, o):
    pr = P[IDS[model]]
    return (f * pr["input_per_M"] + cr * pr["cached_input_per_M"]
            + cw * pr["cache_write_per_M"] + o * pr["output_per_M"]) / 1e6


def score(d):
    a = b = None
    for name, slot in (("score.json", "a"), ("score-2.json", "b")):
        p = os.path.join(d, name)
        if os.path.exists(p):
            try:
                v = json.load(open(p))["total"]
            except Exception:
                v = None
            if slot == "a":
                a = v
            else:
                b = v
    return a, b


def fmt(a, b, mx):
    if a is None and b is None:
        return "not run"
    if b is None or a == b:
        return f"{a}/{mx}"
    return f"{a} & {b} /{mx}"


def segs(d):
    return sorted(glob.glob(os.path.join(d, "transcript-seg*.jsonl")),
                  key=lambda p: int(re.search(r"seg(\d+)", p).group(1)))


rows = []
R = A.root

# ---- short variant -------------------------------------------------------
for m in ("haiku", "sonnet", "opus", "fable"):
    for mode in ("single", "sequential", "noisy"):
        d = f"{R}/runs/{m}/{mode}"
        paths = segs(d) or [f"{d}/transcript.jsonl"]
        f, cr, cw, o, t, c = usage(paths)
        if t == 0:
            rows.append((m, "short", mode, "not run", "—", "—", "—", "—")); continue
        a, b = score(d)
        rows.append((m, "short", mode, fmt(a, b, 100),
                     f"{(f+cr+cw)/1e6:.1f}M in / {o/1e3:.0f}k out", str(t), str(c),
                     f"${cost(m, f, cr, cw, o):,.2f}"))

# ---- long: read once, answer from notes ---------------------------------
MAX = {1: 34, 2: 35, 3: 31}
for m in ("haiku", "sonnet", "opus", "fable"):
    ing = f"{R}/runs/{m}/long-notes/ingest"
    f, cr, cw, o, t, c = usage(segs(ing))
    if t:
        rows.append((m, "long / read once", f"ingest ({len(segs(ing))} segments)", "—",
                     f"{(f+cr+cw)/1e6:.1f}M in / {o/1e3:.0f}k out", str(t), str(c),
                     f"${cost(m, f, cr, cw, o):,.2f}"))
    for bn in (1, 2, 3):
        d = f"{R}/runs/{m}/long-notes/batch-{bn}"
        f, cr, cw, o, t, c = usage([f"{d}/transcript.jsonl"])
        a, b = score(d)
        if t == 0:
            rows.append((m, "long / read once", f"batch {bn}", "not run", "—", "—", "—", "—")); continue
        rows.append((m, "long / read once", f"batch {bn}", fmt(a, b, MAX[bn]),
                     f"{(f+cr+cw)/1e6:.1f}M in / {o/1e3:.0f}k out", str(t), str(c),
                     f"${cost(m, f, cr, cw, o):,.2f}"))

# ---- long: re-read per batch --------------------------------------------
for m in ("haiku", "sonnet", "opus", "fable"):
    for bn in (1, 2, 3):
        d = f"{R}/runs/{m}/long-reread/batch-{bn}"
        paths = segs(f"{d}/ingest")
        f, cr, cw, o, t, c = usage(paths)
        a, b = score(d)
        if t == 0:
            rows.append((m, "long / re-read", f"batch {bn}", "not run", "—", "—", "—", "—")); continue
        rows.append((m, "long / re-read", f"batch {bn} ({len(paths)} segments)", fmt(a, b, MAX[bn]),
                     f"{(f+cr+cw)/1e6:.1f}M in / {o/1e3:.0f}k out", str(t), str(c),
                     f"${cost(m, f, cr, cw, o):,.2f}"))

hdr = ["Model", "Variant", "Round", "Score", "Tokens", "Turns", "Tool calls", "Cost (USD)"]
lines = ["| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
for r in rows:
    lines.append("| " + " | ".join(r) + " |")
text = "\n".join(lines)
if A.out:
    open(A.out, "w").write("# Story test v3 — full scoresheet\n\n"
        "Two judges per cell; `a & b` means the judges differed. Dollars are notional on a\n"
        "subscription plan and are shown for API users; turns and tool calls are what a run\n"
        "actually spends. Token counts include cache reads.\n\n" + text + "\n")
    print(f"wrote {A.out}")
print(text)
