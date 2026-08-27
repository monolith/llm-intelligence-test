"""Item-level agreement between the two judgings of each cell: raw agreement and Cohen's kappa.

Usage: python judge_kappa.py --runs v2/runs --out v2/runs/kappa.json
Items are matched by section + id; a point value is binarised as full credit vs not (checklist items are 0/1 anyway).
"""
import argparse
import glob
import json
import os


def _items(score):
    out = {}
    for sec, body in score.get("sections", {}).items():
        for it in body.get("items", []):
            key = f"{sec}:{it.get('id')}"
            mx = it.get("max", 1) or 1
            out[key] = 1 if it.get("points", 0) >= mx else 0
    return out


def kappa(a, b):
    keys = sorted(set(a) & set(b))
    if not keys:
        return None, None, 0
    n = len(keys)
    agree = sum(1 for k in keys if a[k] == b[k])
    po = agree / n
    pa1 = sum(a[k] for k in keys) / n
    pb1 = sum(b[k] for k in keys) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    k = None if pe == 1 else (po - pe) / (1 - pe)
    return po, k, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="v2/runs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    result = {}
    for s1 in sorted(glob.glob(os.path.join(a.runs, "*", "*", "score.json"))):
        s2 = s1.replace("score.json", "score-2.json")
        if not os.path.exists(s2):
            continue
        cell = "/".join(s1.split(os.sep)[-3:-1])
        j1, j2 = json.load(open(s1)), json.load(open(s2))
        po, k, n = kappa(_items(j1), _items(j2))
        result[cell] = {"items_matched": n, "agreement": po, "kappa": k,
                        "total_1": j1.get("total"), "total_2": j2.get("total")}
        print(f"{cell}: n={n} agreement={po if po is None else round(po,3)} kappa={k if k is None else round(k,3)} totals={j1.get('total')}/{j2.get('total')}")
    json.dump(result, open(a.out, "w"), indent=1)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
