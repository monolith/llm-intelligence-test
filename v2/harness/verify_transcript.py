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
    # Benign: tool uses that touch only the run's own output files (e.g. `wc -w` on the notes it just wrote).
    benign = [u for u in uses if u[0] in ("Bash", "Edit") and ("/v2/runs/" in u[1] or "/v3/runs" in u[1]) and "test-input" not in u[1] and "/noise/" not in u[1] and "answer-key" not in u[1] and "originals" not in u[1]]
    uses = [u for u in uses if u not in benign]
    # Continuation reads: the Read tool returns large files in parts; consecutive Reads of the same
    # file with an "offset" are one delivery, not a re-read.
    collapsed = []
    for name, payload in uses:
        try:
            fp = json.loads(payload).get("file_path") if payload.startswith("{") else None
        except json.JSONDecodeError:
            fp = None
        if collapsed and name == "Read" and collapsed[-1][0] == "Read" and fp and fp in collapsed[-1][1] and '"offset"' in payload:
            continue
        collapsed.append((name, payload))
    uses = collapsed
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
    print(f"valid: {len(uses)} prescribed tool use(s), {len(benign)} benign own-output use(s), nothing else")


if __name__ == "__main__":
    main()
