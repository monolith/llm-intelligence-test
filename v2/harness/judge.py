#!/usr/bin/env python3
"""Judge one run's answers.md against the answer key, N times at temperature 0.

Writes DIR/score.json (every judging, the first as canonical, and the max absolute difference in
total score between judgings) and DIR/score.md (a per-section table, one column per judging).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from common import (
    REQUEST_TIMEOUT_S,
    call_with_retries,
    extract_json,
    extract_text,
    load_dotenv,
    repo_root_from,
)
from prompts import judge_prompt

DEFAULT_JUDGE_MODEL = "claude-opus-5"


def judge_once(client, model: str, answer_key_text: str, answers_text: str, max_tokens: int, sleep=time.sleep) -> dict:
    """One judging call. Returns the parsed JSON verdict; raises ValueError if it cannot be parsed."""
    prompt = judge_prompt(answer_key_text, answers_text)
    response, _latency_s = call_with_retries(
        client,
        model=model,
        system=None,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        sleep=sleep,
    )
    text = extract_text(response)
    return extract_json(text)


def section_totals(verdict: dict) -> dict[str, float]:
    """{"A": total, ..., "deductions": sum, "total": total} pulled out of one judging's JSON."""
    totals: dict[str, float] = {}
    for section, body in verdict.get("sections", {}).items():
        totals[section] = body.get("total", 0)
    totals["deductions"] = sum(d.get("points", 0) for d in verdict.get("deductions", []))
    totals["total"] = verdict.get("total", 0)
    return totals


def max_abs_diff(judgings: list[dict]) -> float:
    """Largest absolute difference in grand total between any two judgings; 0.0 if fewer than two."""
    totals = [j.get("total", 0) for j in judgings]
    if len(totals) < 2:
        return 0.0
    return max(abs(a - b) for i, a in enumerate(totals) for b in totals[i + 1 :])


def render_score_md(judgings: list[dict]) -> str:
    if not judgings:
        return "# Score\n\nNo judgings.\n"

    all_totals = [section_totals(j) for j in judgings]
    sections = sorted({s for j in judgings for s in j.get("sections", {})})
    headers = ["Section"] + [f"Judging {i + 1}" + (" (canonical)" if i == 0 else "") for i in range(len(judgings))]
    lines = ["# Score", "", "| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]

    for section in sections:
        row = [section] + [str(t.get(section, "-")) for t in all_totals]
        lines.append("| " + " | ".join(row) + " |")

    ded_row = ["Deductions"] + [str(t["deductions"]) for t in all_totals]
    lines.append("| " + " | ".join(ded_row) + " |")

    total_row = ["**Total**"] + [f"**{t['total']}**" for t in all_totals]
    lines.append("| " + " | ".join(total_row) + " |")

    lines.append("")
    lines.append(f"Max absolute difference in total across judgings: {max_abs_diff(judgings)}")

    for i, j in enumerate(judgings):
        if j.get("deductions"):
            lines.append("")
            lines.append(f"## Judging {i + 1} deductions")
            for d in j["deductions"]:
                lines.append(f"- {d.get('points', '?')}: {d.get('reason', '')}")

    return "\n".join(lines) + "\n"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Judge a run's answers.md against an answer key.")
    parser.add_argument("--run", required=True, help="Run directory (must contain answers.md); score files are written here.")
    parser.add_argument("--key", required=True, help="Path to the answer key file.")
    parser.add_argument("--model", default=DEFAULT_JUDGE_MODEL, help="Judge model id.")
    parser.add_argument("--times", type=int, default=2, help="Number of independent judgings at temperature 0.")
    parser.add_argument("--max-tokens", type=int, default=8000)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    load_dotenv(repo_root_from(__file__) / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    run_dir = Path(args.run)
    answers_path = run_dir / "answers.md"
    key_path = Path(args.key)

    if not answers_path.is_file():
        print(f"no answers.md in {run_dir}", file=sys.stderr)
        return 2
    if not key_path.is_file():
        print(f"answer key not found: {key_path}", file=sys.stderr)
        return 2
    if not api_key:
        print("No credentials found: set ANTHROPIC_API_KEY to run the judge.", file=sys.stderr)
        return 2

    import anthropic

    client = anthropic.Anthropic(api_key=api_key, max_retries=0, timeout=REQUEST_TIMEOUT_S)

    answers_text = answers_path.read_text(encoding="utf-8")
    key_text = key_path.read_text(encoding="utf-8")

    judgings = []
    for _ in range(max(1, args.times)):
        judgings.append(judge_once(client, args.model, key_text, answers_text, args.max_tokens))

    score = {
        "judgings": judgings,
        "canonical": judgings[0],
        "max_abs_diff": max_abs_diff(judgings),
    }
    (run_dir / "score.json").write_text(json.dumps(score, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (run_dir / "score.md").write_text(render_score_md(judgings), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
