"""Build the single-mode bundle: all twelve retellings followed by the questions, in order.
Usage: python make_bundle.py --root v2 --out v2/test-input/bundle-single.md
"""
import argparse
import glob
import os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="v2")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(a.root, "test-input", "retellings", "r[0-9][0-9]-*.md")))
    assert files, "no retellings found"
    parts = ["# Test input — the retellings in order, then the questions\n"]
    for f in files:
        parts.append(open(f, encoding="utf-8").read().rstrip() + "\n\n---\n")
    parts.append(open(os.path.join(a.root, "test-input", "questions.md"), encoding="utf-8").read())
    text = "\n".join(parts)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {a.out}: {len(text.split())} words, {len(files)} retellings")


if __name__ == "__main__":
    main()
