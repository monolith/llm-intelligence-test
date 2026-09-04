#!/usr/bin/env python3
"""Statistics across repeated runs of the short variant.

Every earlier table in this repository is n = 1 per cell: one run, judged twice. The two judge
numbers measure marking spread, not run-to-run spread, and a single run cannot support a claim
that one model beats another by a few points. This script reads several independent run trees
(runs, runs-r2, runs-r3, ...) and reports what repetition actually licenses:

  * per cell (model x mode): n, mean, SD, min-max, and a t-based 95% interval on the mean;
  * per model, pooled across modes (mode is a blocking factor, so n triples): the same;
  * paired differences between models, paired by (mode, repeat), with a 95% interval and the
    paired t statistic -- the honest test of "is A better than B on this material";
  * cost per point with the run-to-run spread propagated.

The judge-averaged score (mean of the two judgings) is the unit of analysis. Cost, turns and tool
calls come from the captured transcripts, priced from prices.json.
"""
from __future__ import annotations

import argparse, glob, json, math, os, re, statistics as st
from itertools import combinations

MODELS = ["haiku", "sonnet", "opus", "fable"]
MODES = ["single", "sequential", "noisy"]
IDS = {"haiku": "claude-haiku-4-5", "sonnet": "claude-sonnet-5",
       "opus": "claude-opus-5", "fable": "claude-fable-5"}
# two-sided 95% t critical values for small n (df = n-1)
T95 = {1: float("inf"), 2: 12.706, 3: 4.303, 4: 3.182, 5: 2.776, 6: 2.571,
       7: 2.447, 8: 2.365, 9: 2.306, 10: 2.262, 12: 2.201, 15: 2.145, 20: 2.093, 30: 2.045}


def tcrit(n: int) -> float:
    if n <= 1:
        return float("inf")
    keys = sorted(T95)
    for k in keys:
        if k >= n:
            return T95[k]
    return 1.96


def judge_avg(cell_dir: str):
    vals = []
    for name in ("score.json", "score-2.json"):
        p = os.path.join(cell_dir, name)
        if os.path.exists(p):
            try:
                vals.append(json.load(open(p))["total"])
            except Exception:
                pass
    return (sum(vals) / len(vals)) if vals else None


def usage(cell_dir: str):
    paths = sorted(glob.glob(os.path.join(cell_dir, "transcript-seg*.jsonl")),
                   key=lambda p: int(re.search(r"seg(\d+)", p).group(1))) \
        or [os.path.join(cell_dir, "transcript.jsonl")]
    f = cr = cw = o = t = c = 0
    for p in paths:
        if not os.path.exists(p):
            continue
        for line in open(p):
            r = json.loads(line)
            if r.get("role") != "assistant":
                continue
            t += 1
            if "[tool_use " in (r.get("text") or ""):
                c += 1
            u = r.get("usage") or {}
            f += u.get("input_tokens") or 0
            cr += u.get("cache_read_input_tokens") or 0
            cw += u.get("cache_creation_input_tokens") or 0
            o += u.get("output_tokens") or 0
    return f, cr, cw, o, t, c


def cost(prices: dict, model: str, f, cr, cw, o) -> float:
    pr = prices[IDS[model]]
    return (f * pr["input_per_M"] + cr * pr["cached_input_per_M"]
            + cw * pr["cache_write_per_M"] + o * pr["output_per_M"]) / 1e6


def collect(trees: list[str], prices: dict) -> dict:
    """{(model, mode): [ {repeat, score, cost, turns, calls} ... ]} -- only complete cells."""
    out: dict = {}
    for ri, tree in enumerate(trees, 1):
        for m in MODELS:
            for mode in MODES:
                d = os.path.join(tree, m, mode)
                s = judge_avg(d)
                if s is None:
                    continue
                f, cr, cw, o, t, c = usage(d)
                if t == 0:
                    continue
                out.setdefault((m, mode), []).append(
                    {"repeat": ri, "score": s, "cost": cost(prices, m, f, cr, cw, o),
                     "turns": t, "calls": c})
    return out


def summarize(xs: list[float]) -> dict:
    n = len(xs)
    mean = sum(xs) / n
    sd = st.stdev(xs) if n > 1 else float("nan")
    half = tcrit(n) * sd / math.sqrt(n) if n > 1 else float("nan")
    return {"n": n, "mean": mean, "sd": sd, "lo": mean - half, "hi": mean + half,
            "min": min(xs), "max": max(xs)}


def fmt_ci(s: dict, digits=1) -> str:
    if s["n"] == 1:
        return f"{s['mean']:.{digits}f} (n=1)"
    if s["n"] == 2:
        return f"{s['mean']:.{digits}f} ± wide (n=2, range {s['min']:g}–{s['max']:g})"
    return f"{s['mean']:.{digits}f} [{s['lo']:.{digits}f}, {s['hi']:.{digits}f}]"


def paired(cells: dict, a: str, b: str) -> dict | None:
    """Paired by (mode, repeat). Returns summary of (a - b) differences, plus a paired t."""
    diffs = []
    for mode in MODES:
        ra = {r["repeat"]: r["score"] for r in cells.get((a, mode), [])}
        rb = {r["repeat"]: r["score"] for r in cells.get((b, mode), [])}
        for rep in sorted(set(ra) & set(rb)):
            diffs.append(ra[rep] - rb[rep])
    if not diffs:
        return None
    s = summarize(diffs)
    if s["n"] > 1 and s["sd"] > 0:
        s["t"] = s["mean"] / (s["sd"] / math.sqrt(s["n"]))
    else:
        s["t"] = float("nan")
    s["wins"] = sum(1 for d in diffs if d > 0)
    s["ties"] = sum(1 for d in diffs if d == 0)
    return s


def render(cells: dict) -> str:
    L = ["# Short variant — statistics across repeats", ""]
    L += ["Unit of analysis: the judge-averaged score of one run. Intervals are two-sided 95%",
          "t-intervals on the mean; with n = 3 they are wide by construction, and that width is the",
          "finding, not a defect. n = 1 cells report the single value and no interval.", ""]

    L += ["## Per cell", "", "| Model | Mode | n | mean [95% CI] | SD | min–max | $/run (mean) | turns/run (mean) |",
          "|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        for mode in MODES:
            rs = cells.get((m, mode))
            if not rs:
                L.append(f"| {m} | {mode} | 0 | not run | | | | |"); continue
            s = summarize([r["score"] for r in rs])
            sd = "—" if math.isnan(s["sd"]) else f"{s['sd']:.1f}"
            L.append(f"| {m} | {mode} | {s['n']} | {fmt_ci(s)} | {sd} | {s['min']:g}–{s['max']:g} | "
                     f"${sum(r['cost'] for r in rs)/len(rs):.2f} | {sum(r['turns'] for r in rs)/len(rs):.0f} |")

    L += ["", "## Per model, pooled across the three modes", "",
          "Mode is a blocking factor here — each model saw the same three administrations — so pooling",
          "triples n for the model-level question without mixing in material differences.", "",
          "| Model | n | mean [95% CI] | SD | $/point (mean) |", "|---|---|---|---|---|"]
    pooled = {}
    for m in MODELS:
        rs = [r for mode in MODES for r in cells.get((m, mode), [])]
        if not rs:
            L.append(f"| {m} | 0 | not run | | |"); continue
        s = summarize([r["score"] for r in rs]); pooled[m] = s
        sd = "—" if math.isnan(s["sd"]) else f"{s['sd']:.1f}"
        cpp = st.mean([r["cost"] / r["score"] for r in rs if r["score"] > 0])
        L.append(f"| {m} | {s['n']} | {fmt_ci(s)} | {sd} | ${cpp:.4f} |")

    L += ["", "## Paired comparisons (A − B), paired by mode and repeat", "",
          "A positive mean favours A. `wins` counts pairs where A scored higher. The paired t is",
          "reported for readers who want it; with n ≤ 9 treat |t| > 2.3 as the conventional bar.", "",
          "| A | B | n pairs | mean diff [95% CI] | wins–ties–losses | paired t |", "|---|---|---|---|---|---|"]
    order = [m for m in MODELS if any((m, mode) in cells for mode in MODES)]
    for a, b in combinations(reversed(order), 2):
        s = paired(cells, a, b)
        if not s:
            continue
        losses = s["n"] - s["wins"] - s["ties"]
        t = "—" if math.isnan(s["t"]) else f"{s['t']:.2f}"
        L.append(f"| {a} | {b} | {s['n']} | {fmt_ci(s)} | {s['wins']}–{s['ties']}–{losses} | {t} |")

    L += ["", "## Reading the intervals", "",
          "If two models' intervals do not overlap, the ranking between them is supported by these",
          "runs. If they overlap, the runs cannot tell them apart at this n — which is a statement about",
          "the experiment, not about the models. The paired table is the stronger test, because it",
          "removes the material's own difficulty from the comparison.", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trees", nargs="+", default=["v3/runs", "v3/runs-r2", "v3/runs-r3"])
    ap.add_argument("--prices", default="v2/harness/prices.json")
    ap.add_argument("--out")
    a = ap.parse_args()
    prices = json.load(open(a.prices))
    cells = collect(a.trees, prices)
    text = render(cells)
    if a.out:
        open(a.out, "w").write(text + "\n")
        print(f"wrote {a.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
