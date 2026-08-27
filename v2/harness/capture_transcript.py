"""Reduce a Claude Code subagent transcript (task-output JSONL) to evidence: role, text, model, usage, timestamp.

Usage: python capture_transcript.py <task-output.jsonl> [<more.jsonl> ...] --out <dir>/transcript.jsonl
Multiple inputs are concatenated in order (used for the noisy mode, where compaction starts a fresh subagent).
"""
import argparse
import json


def _text_of(content):
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            parts.append(block.get("text", ""))
        elif t == "tool_use":
            parts.append(f"[tool_use {block.get('name')}: {json.dumps(block.get('input'), ensure_ascii=False)[:2000]}]")
        elif t == "tool_result":
            c = block.get("content")
            if isinstance(c, list):
                c = " ".join(b.get("text", "") for b in c if isinstance(b, dict))
            parts.append(f"[tool_result: {str(c)[:4000]}]")
    return "\n".join(parts)


def reduce_file(path, segment):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") not in ("user", "assistant"):
                continue
            m = d.get("message") or {}
            rows.append({
                "segment": segment,
                "role": m.get("role", d["type"]),
                "text": _text_of(m.get("content")),
                "model": m.get("model"),
                "usage": m.get("usage"),
                "timestamp": d.get("timestamp"),
            })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows = []
    for i, p in enumerate(a.inputs, 1):
        rows.extend(reduce_file(p, i))
    with open(a.out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    usage_in = sum((r["usage"] or {}).get("input_tokens", 0) for r in rows if r["role"] == "assistant")
    usage_out = sum((r["usage"] or {}).get("output_tokens", 0) for r in rows if r["role"] == "assistant")
    print(f"wrote {a.out}: {len(rows)} messages across {len(a.inputs)} segment(s); assistant usage in={usage_in} out={usage_out}")


if __name__ == "__main__":
    main()
