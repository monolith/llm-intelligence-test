#!/usr/bin/env python3
"""Item-level retry driver: which questions are still wrong, and what has been banked.

The unit the model can act on is the QUESTION, not the key's internal item id, so items are
grouped by the question they belong to. A question is banked once every one of its items scores
full marks; banked questions are never re-attempted and their points are kept. Feedback to the
model is the list of question labels still outstanding — never the judge's notes, several of
which state the correct value outright.
"""
import argparse, json, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("score")
a = ap.parse_args()

d = json.load(open(a.score))


def question_of(item_id: str) -> str:
    m = re.match(r"^([ABC])(\d+)", item_id)
    if not m:
        return item_id
    sec, num = m.group(1), m.group(2)
    if sec == "A":
        return f"Section A — story {num}"
    if sec == "B":
        return f"B{num}"
    sub = re.match(r"^C\d+([a-d])", item_id)
    return f"C{num}({sub.group(1)})" if sub else f"C{num}"


groups: dict[str, list] = {}
for sec, v in d["sections"].items():
    for it in v.get("items", []):
        groups.setdefault(question_of(it["id"]), []).append(it)

banked, open_qs = [], []
banked_pts = open_pts = 0
for q, items in groups.items():
    got = sum(i.get("points") or 0 for i in items)
    mx = sum(i.get("max") or 1 for i in items)
    (banked if got == mx else open_qs).append((q, got, mx))
    if got == mx:
        banked_pts += got
    else:
        open_pts += mx - got

ded = sum(x.get("points") or 0 for x in d.get("deductions", []))
print(f"total now: {d['total']}    banked (fully correct) questions: {len(banked)}  = {banked_pts} pts")
print(f"deductions currently applied: {ded}")
print("\nBANKED — do not re-attempt:")
for q, g, m in sorted(banked):
    print(f"  {q}  {g}/{m}")
print("\nSTILL WRONG OR INCOMPLETE — re-attempt these:")
for q, g, m in sorted(open_qs):
    print(f"  {q}  {g}/{m}")
print(f"\nrecoverable if every open question were perfected: +{open_pts} (before deductions)")
