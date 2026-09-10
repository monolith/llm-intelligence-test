#!/usr/bin/env python3
"""Handover-content metric: how many facts did a handover carry, and how many of them belong?

    python3 v3/ab/harness/ab_handover.py v3/ab/plugin/haiku/noisy-r1 [--model opus] [--force]

For each handover a run wrote (baseline: notes-after-r08.md, notes-after-r16.md; plugin: the two
briefs under .governor/handoffs/, in time order) it records:

- story_facts: canon facts (F001–F112 in v3/answer-key/canon.md) whose substance is present in the
  handover, judged by one headless opus session that sees the canon and the handover and nothing
  else. Count out of 112. This is a judge call, so it carries the usual judge noise; it is a
  diagnostic, not the score.
- noise_facts: distractor answers (v3/distractors/questions.md) present in the handover, checked
  deterministically by token. Only the distractors delivered before that seam count (slots 1–8 at
  seam 1, 1–16 at seam 2). Count out of 8 or 16.
- context_appropriate_share: story_facts / (story_facts + noise_facts).

Writes handover-metrics.json into the run dir; ab_report.py picks it up.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

REPO = Path("/home/anatoly/llm-intelligence-test")
CANON = REPO / "v3/answer-key/canon.md"
QUESTIONS = REPO / "v3/distractors/questions.md"
SCRATCH = Path(os.environ.get("AB_SCRATCH", "/tmp/claude-1000/-home-anatoly/24e92440-efc2-4a14-97c2-ee126ebf0ca1/scratchpad/ab")) / "handover"
STOP = {"the", "a", "an", "of", "on", "in", "at", "to", "for", "and", "or", "by", "with", "from", "mrs", "mr", "dr",
        "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "weeks", "week", "less", "than",
        "levy", "mills", "dollar", "hotel", "lemma", "norm", "route", "message", "words", "level", "error", "code"}


OVERRIDE = {1: ["six mills", "mills on the dollar"], 7: ["Krell", "four weeks", "4 weeks"],
            12: ["Dunmore", "No. 219", "219"], 16: ["dryer", "Phyl", "Armando"]}   # slots whose answer has no distinctive token


def noise_probes():
    """slot -> list of probe strings taken from the distractor's answer (numbers, codes, proper names)."""
    text = QUESTIONS.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^## (\d+)\. (\S+)\n\*\*Q:\*\*.*?\n\*\*A:\*\*\s*(.+?)\s*$", text, flags=re.M | re.S):
        slot, fname, ans = int(m.group(1)), m.group(2), m.group(3).split("\n")[0]
        ans = ans.replace("*", "")
        probes = re.findall(r"\$?\d[\d,\.\-]*[A-Za-z\-]*\d*", ans)                      # $59.65, 4471-K, SKF-2201, 1,480
        probes += [w for w in re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", ans) if w.lower() not in STOP]  # Sparrow, Interleaving, Buckley
        probes = [p.strip(".,") for p in probes if len(p.strip(".,")) >= 3]
        if slot in OVERRIDE:
            probes = OVERRIDE[slot]
        elif not probes:
            probes = [w for w in re.findall(r"\b[a-zA-Z]{5,}\b", ans) if w.lower() not in STOP][:2]
        out[slot] = {"file": fname, "answer": ans, "probes": sorted(set(probes))}
    return out


def noise_hits(handover_text, probes, slots):
    low = handover_text.lower()
    hits = []
    for s in slots:
        p = probes.get(s)
        if p and any(x.lower() in low for x in p["probes"]):
            hits.append(p["file"])
    return hits


def handovers_in(run_dir):
    prov = json.load(open(run_dir / "provenance.json"))
    if str(prov.get("seam", "")).startswith("none"):
        # nothing was written at the cut; the plugin's automatic state (ledger, facts log) is the only carrier
        f = run_dir / ".governor" / "ledger.md"
        return [f] if f.exists() else []
    if prov["arm"] == "baseline" or prov.get("seam") == "v3 notes step":
        files = [run_dir / "notes-after-r08.md", run_dir / "notes-after-r16.md"]
    else:
        files = sorted((run_dir / ".governor" / "handoffs").glob("*.md"), key=lambda p: p.stat().st_mtime)
    return [f for f in files if f.exists()][:2]


PROMPT = """You are auditing a handover document written by a reader partway through a reading task. You must be exact and not generous.

Read `{canon}` completely (it may take more than one Read). Its section "People and relationships" through "Abstention facts" contains a table of canon facts with ids F001 to F112. Then read `{handover}` completely.

For each canon fact, decide whether its substance is present in the handover: the specific person, relationship, date, quantity, place, object, document, or mechanism is stated in the handover accurately enough that someone holding only the handover could answer a question about it. A vague gesture ("there was a dispute about testing") does not count; a wrong value does not count; a fact merely implied does not count.

Write to `{out}` strict JSON and nothing else, no prose, no markdown fence:
{{"present": ["F001", "F003"], "notes": "one line on what kind of content dominates the handover"}}

Your final reply to me must be one line: the number of facts present out of 112."""


def judge_story_facts(run_dir, handover, idx, model):
    out = run_dir / f"handover-{idx}-facts.json"
    wd = SCRATCH / f"{run_dir.parent.parent.name}-{run_dir.parent.name}-{run_dir.name}-h{idx}"
    wd.mkdir(parents=True, exist_ok=True)
    cmd = ["claude", "-p", "--model", model, "--tools", "Read,Write", "--allowedTools", "Read,Write",
           "--disallowedTools", "Bash", "Grep", "Glob", "Agent", "WebFetch", "WebSearch",
           "--strict-mcp-config", "--setting-sources", "", "--output-format", "json",
           "--add-dir", str(CANON.parent), "--add-dir", str(run_dir),
           PROMPT.format(canon=CANON, handover=handover, out=out)]
    p = subprocess.run(cmd[:-1], input=cmd[-1], cwd=str(wd), capture_output=True, text=True, timeout=2400)
    try:
        o = json.loads(p.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"handover judge failed: {p.stdout[-300:]} {p.stderr[-300:]}")
    present = []
    if out.exists():
        try:
            present = sorted(set(json.load(open(out)).get("present", [])))
        except Exception:
            pass
    return present, {"session_id": o.get("session_id"), "num_turns": o.get("num_turns"), "total_cost_usd": o.get("total_cost_usd")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    run_dir = Path(a.run_dir).resolve()
    outp = run_dir / "handover-metrics.json"
    if outp.exists() and not a.force:
        print(f"exists: {outp}"); return
    probes = noise_probes()
    rows = []
    for idx, h in enumerate(handovers_in(run_dir), 1):
        text = h.read_text(encoding="utf-8")
        slots = range(1, 8 * idx + 1)
        nh = noise_hits(text, probes, slots)
        present, call = judge_story_facts(run_dir, h, idx, a.model)
        sf, nf = len(present), len(nh)
        rows.append({"seam": idx, "file": h.name, "words": len(text.split()), "story_facts": sf, "story_facts_of": 112,
                     "noise_facts": nf, "noise_facts_of": len(slots), "noise_hits": nh,
                     "context_appropriate_share": round(sf / (sf + nf), 3) if sf + nf else None, "judge": call})
        print(f"seam {idx} {h.name}: {len(text.split())} words, story facts {sf}/112, noise facts {nf}/{len(slots)}, share {rows[-1]['context_appropriate_share']}")
    json.dump({"handovers": rows, "noise_probes": {str(k): v for k, v in probes.items()}, "model": a.model,
               "date": time.strftime("%Y-%m-%d")}, open(outp, "w"), indent=2)
    print(f"wrote {outp}")


if __name__ == "__main__":
    main()
