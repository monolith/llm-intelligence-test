"""Check that a reduced transcript (from capture_transcript.py) used only the prescribed tool calls.

Usage: python verify_transcript.py --transcript DIR/transcript.jsonl --allowed "cat v2/test-input/bundle-single.md"
Multiple --allowed values are matched in order against the tool_use blocks' command text (substring match).
Exit 0 = valid; exit 1 = the run used tools beyond the prescribed sequence (details printed).
"""
import argparse
import json
import re
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--allowed", action="append", default=[])
    a = ap.parse_args()
    uses = []
    with open(a.transcript, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r["role"] != "assistant":
                continue
            for m in re.finditer(r"\[tool_use (\w+): (.*?)\]", r["text"], flags=re.S):
                uses.append((m.group(1), m.group(2)[:300]))
    problems = []
    if len(uses) != len(a.allowed):
        problems.append(f"expected {len(a.allowed)} tool uses, found {len(uses)}")
    for i, (name, payload) in enumerate(uses):
        want = a.allowed[i] if i < len(a.allowed) else None
        if want is None or want not in payload:
            problems.append(f"tool use #{i+1} {name}: {payload[:160]!r} (allowed: {want!r})")
    if problems:
        print("INVALID RUN:\n  " + "\n  ".join(problems))
        sys.exit(1)
    print(f"valid: {len(uses)} prescribed tool use(s), nothing else")


if __name__ == "__main__":
    main()
