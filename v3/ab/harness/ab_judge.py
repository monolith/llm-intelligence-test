#!/usr/bin/env python3
"""Score one A/B run twice with independent headless opus judges (the v3 judge prompt, unchanged).

    python3 v3/ab/harness/ab_judge.py v3/ab/baseline/haiku/noisy-r1 [--which 1 2] [--model opus]

Writes score.json / score.md (judge 1) and score-2.json / score-2.md (judge 2) into the run dir.
The judge session runs in a scratch working directory (no CLAUDE.md), with Read and Write only,
and sees the key and the answers and nothing else.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

REPO = Path("/home/anatoly/llm-intelligence-test")
KEY = REPO / "v3/answer-key/answers-and-scoring.md"
SCRATCH = Path(os.environ.get("AB_SCRATCH", "/tmp/claude-1000/-home-anatoly/24e92440-efc2-4a14-97c2-ee126ebf0ca1/scratchpad/ab")) / "judge"

PROMPT = """You are scoring one run of a synthesis test against a fixed answer key. You are not the system being tested and must not be lenient with it.

Read the answer key at `{key}` and the run's answers at `{answers}` (both may need more than one Read call; read them completely).

Score every item in the answer key against the run's answers. Rules:
- Sections marked exact-match (typically C and E) must match the key's stated answer or tolerance exactly; do not award credit for a plausible-sounding but different number, date, or fraction.
- Checklist sections score each listed item 1 point if satisfied, 0 if not. No partial credit on any single item.
- Where the key marks an item as an abstention item (the correct answer is that something is not determinable from the sources), award the point only if the run's answer abstains accordingly; do not award it for a confident answer that happens to be unfalsifiable, and do not penalize honest hedging as though it were an error.
- Section A is credited wherever the content appears inside the run's eight reconstructions — the run chose its own partition of the stories, so look for each keyed fact anywhere in Section A, not only under the story number the key uses. Never credit Section A from material the run wrote in Sections B–G.
- Apply the key's corruption deductions: subtract for every planted error the run asserts as fact, per the key's list and any general deduction rule it states. A hedged mention of an error ("one source wrongly claims...") is not a deduction.
- Sum each section to its own total, then sum sections minus deductions to the grand total. Floor each section at 0 if the key says to.
- For every item that does NOT earn full marks, classify the loss: "omission" if the run makes no claim on the point (silent, "not stated", "cannot determine" where the key has a value), or "fabrication" if the run makes a specific claim that contradicts the key. Put it in the item's "loss" field; use null for items earning full marks.

Write your scoring to `{score_json}` as strict JSON and nothing else — no prose, no markdown fence. The shape, using the key's own section labels as the keys of "sections":

{{"sections": {{"A": {{"items": [{{"id": "A1.1", "points": 0, "max": 1, "loss": "omission", "note": "why"}}], "total": 0}}, "...": {{"items": [], "total": 0}}}}, "deductions": [{{"reason": "why", "points": -1}}], "total": 0}}

Then write a short human-readable companion to `{score_md}`: the per-section totals, the grand total, and a few lines on what the run got wrong.

Your final reply to me must be one line: the grand total and the per-section totals."""


def judge(run_dir, which, model):
    run_dir = Path(run_dir).resolve()
    suffix = "" if which == 1 else f"-{which}"
    sj, sm = run_dir / f"score{suffix}.json", run_dir / f"score{suffix}.md"
    wd = SCRATCH / f"{run_dir.parent.parent.name}-{run_dir.parent.name}-{run_dir.name}-j{which}"
    wd.mkdir(parents=True, exist_ok=True)
    cmd = ["claude", "-p", "--model", model, "--tools", "Read,Write", "--allowedTools", "Read,Write",
           "--disallowedTools", "Bash", "Grep", "Glob", "Agent", "WebFetch", "WebSearch",
           "--strict-mcp-config", "--setting-sources", "", "--output-format", "json", "--add-dir", str(KEY.parent), "--add-dir", str(run_dir),
           PROMPT.format(key=KEY, answers=run_dir / "answers.md", score_json=sj, score_md=sm)]
    t0 = time.time()
    p = subprocess.run(cmd[:-1], input=cmd[-1], cwd=str(wd), capture_output=True, text=True, timeout=3600)
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"judge {which} failed: {p.stdout[-500:]} {p.stderr[-500:]}")
    total = None
    if sj.exists():
        try:
            total = json.load(open(sj))["total"]
        except Exception as e:
            total = f"unparseable ({e})"
    with open(run_dir / "judge-calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"which": which, "model": model, "session_id": out.get("session_id"), "num_turns": out.get("num_turns"),
                            "total_cost_usd": out.get("total_cost_usd"), "wall_s": round(time.time() - t0, 1),
                            "result": out.get("result"), "total": total}) + "\n")
    print(f"judge {which}: total={total} turns={out.get('num_turns')} cost=${out.get('total_cost_usd', 0):.3f} | {str(out.get('result',''))[:120]!r}")
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--which", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--model", default="opus")
    a = ap.parse_args()
    for w in a.which:
        judge(a.run_dir, w, a.model)


if __name__ == "__main__":
    main()
