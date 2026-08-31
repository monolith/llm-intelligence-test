#!/usr/bin/env python3
"""Cumulative banking across rounds: an item counts once, the first time it is earned.

Round N presents only the questions that still hold unearned items. Anything already earned is
banked and never re-asked, so the running total cannot fall — which is the point of this variant:
it removes the "rewrote a good answer and broke it" failure mode entirely and measures only whether
the model can accumulate to a target given repeated attempts at what it has not yet got.
"""
import argparse, json, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("scores", nargs="+", help="score.json files, in round order")
ap.add_argument("--target", type=int, default=18)
a = ap.parse_args()


def question_of(i):
    m = re.match(r"^([ABC])(\d+)", i)
    if not m:
        return i
    s, n = m.groups()
    if s == "A":
        return f"Section A — story {n}"
    if s == "B":
        return f"B{n}"
    sub = re.match(r"^C\d+([a-d])", i)
    return f"C{n}({sub.group(1)})" if sub else f"C{n}"


best, mx, first_earned = {}, {}, {}
for rnd, path in enumerate(a.scores):
    d = json.load(open(path))
    for sec, v in d["sections"].items():
        for it in v.get("items", []):
            i = it["id"]
            p = it.get("points") or 0
            mx[i] = it.get("max") or 1
            if p > best.get(i, 0):
                best[i] = p
                first_earned.setdefault(i, rnd) if p == mx[i] else None
    print(f"round {rnd}: sheet total {d['total']}, deductions {sum(x.get('points') or 0 for x in d.get('deductions', []))}")

earned = sum(best.values())
total_max = sum(mx.values())
open_q = sorted({question_of(i) for i in mx if best.get(i, 0) < mx[i]})
print(f"\nBANKED ITEMS: {sum(1 for i in mx if best.get(i,0)==mx[i])} of {len(mx)}   "
      f"points earned {earned}/{total_max}")
print(f"target (opus): {a.target} net / 22 raw items")
print(f"\nSTILL OPEN — {len(open_q)} questions:")
for q in open_q:
    items = [i for i in mx if question_of(i) == q]
    print(f"  {q}  {sum(best.get(i,0) for i in items)}/{sum(mx[i] for i in items)}")
