#!/usr/bin/env python3
"""Block 1: reseed-from-a-brief versus carrying on, on a two-phase build task with hidden tests.

    python3 v3/ab/harness/ab_build.py --arm A --model haiku --rep 1 --plugin-dir ~/context-governance-plugin
    python3 v3/ab/harness/ab_build.py --arm B|C|D|E --model haiku --rep 1

Fixture: v3/build/fixture (copied into the working directory), v3/build/phase1-turns.json (the
scripted phase-1 user turns), v3/build/hidden-tests (never copied, never readable by the session),
v3/build/facts-key.md (for auditing what crossed the seam).

Phase 1 is identical in every arm: the scripted turns on one session (investigation request, noise
questions on unrelated documents, a natural follow-up, the spec update). Then the seam:

  A  plugin: `/<plugin>:handoff <reason>` on the same session; phase 2 starts a FRESH session with
     the plugin loaded (its SessionStart hook offers the brief).            [the plugin's central move]
  B  carry on and compact: `/compact` on the same session; phase 2 continues that session.
  C  carry on, no compaction: phase 2 continues the same session as is.     [cost reference]
  D  nothing crosses: phase 2 is a fresh session with no plugin.            [floor]
  E  naive clear, no plugin: one turn asking for a handover file, then a fresh session told the
     file exists (a user doing by hand what the plugin's hook does).        [separates brief from hook]

Phase 2 prompt is identical in every arm. Tools: Read, Write, Edit, Bash, Grep, Glob (a build task
needs them; both arms alike). Scoring: the hidden tests (pytest, junit xml) → items passed of N;
constraint items separately; plus f̂ = phase-2 reads of files the session already read in phase 1,
tokens at phase-2 start, turns and dollars per phase, and (arms A/E) facts and noise found in the
handover artifact.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time, xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ab_run

REPO = ab_run.REPO; V3 = ab_run.V3
BUILD = V3 / "build"
FIXTURE = BUILD / "fixture"; HIDDEN = BUILD / "hidden-tests"; TURNS = BUILD / "phase1-turns.json"
PYTEST = REPO / "v2/harness/.venv/bin/python"
SCRATCH = ab_run.SCRATCH / "build"
GOAL = "Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md."
HANDOFF_REASON = ("stopping here; the next session will implement the five features in SPEC.md and needs everything "
                  "learned about this repository and every update to the spec")
NAIVE_CLEAR = ("This session is ending. Write a file HANDOVER.md in the repository root with everything the next "
               "session will need to implement the five features in SPEC.md: what you learned about the repository "
               "and every update to the spec. Then stop.")
ARMS = {"A": "plugin handoff + fresh session", "B": "carry on, /compact", "C": "carry on, no compaction",
        "D": "fresh session, nothing crosses", "E": "naive handover file, no plugin, fresh session told it exists"}


def claude_cmd(model, prompt, plugin_dir=None, resume=None):
    cmd = ["claude", "-p", "--model", model, "--tools", "Read,Write,Edit,Bash,Grep,Glob",
           "--allowedTools", "Read,Write,Edit,Bash,Grep,Glob", "--disallowedTools", "Agent", "WebFetch", "WebSearch",
           "--strict-mcp-config", "--setting-sources", "", "--output-format", "json",
           "--add-dir", str(V3 / "distractors")]
    if plugin_dir:
        cmd += ["--plugin-dir", str(plugin_dir)]
    if resume:
        cmd += ["--resume", resume]
    cmd.append(prompt)
    return cmd


def run(workdir, model, prompt, label, plugin_dir=None, resume=None, timeout=5400):
    cmd = claude_cmd(model, prompt, plugin_dir, resume)
    t0 = time.time()
    p = subprocess.run(cmd[:-1], input=cmd[-1], cwd=str(workdir), capture_output=True, text=True, timeout=timeout)
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        out = {"error": "no json", "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:], "rc": p.returncode}
    out.update({"_label": label, "_wall_s": round(time.time() - t0, 1), "_argv": cmd[:-1]})
    with open(workdir / "cli-calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    if "session_id" not in out:
        raise SystemExit(f"{label}: claude -p failed: {out}")
    res = str(out.get("result", ""))
    if "safeguards flagged" in res:
        raise SystemExit(f"{label}: safeguard flagged the prompt; run aborted")
    if out.get("is_error") or "session limit" in res or "rate_limit" in res or res.startswith("API Error"):
        raise SystemExit(f"{label}: API error / rate limit; run aborted: {res[:160]!r}")
    print(f"{label}: turns={out.get('num_turns')} cost=${out.get('total_cost_usd', 0):.3f} wall={out['_wall_s']}s result={res[:90]!r}")
    return out


def hidden_tests(workdir, out_xml):
    env = dict(os.environ, LEDGERKIT_REPO=str(workdir), PYTHONPATH=str(workdir))
    subprocess.run([str(PYTEST), "-m", "pytest", str(HIDDEN), "-q", "--junitxml", str(out_xml), "-p", "no:cacheprovider"],
                   cwd=str(HIDDEN), env=env, capture_output=True, text=True, timeout=600)
    root = ET.parse(out_xml).getroot()
    items = []
    for tc in root.iter("testcase"):
        failed = tc.find("failure") is not None or tc.find("error") is not None
        items.append({"name": tc.get("name"), "file": tc.get("classname"), "passed": not failed,
                      "kind": "constraint" if "constraint" in (tc.get("classname") or "") + (tc.get("name") or "") else "feature"})
    return items


def reads_in(transcript):
    return [inp.get("file_path", "") for name, inp, raw, failed in ab_run.tool_uses(transcript) if name == "Read" and isinstance(inp, dict)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=list(ARMS), required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--plugin-dir"); ap.add_argument("--plugin-name", default="context-governor")
    ap.add_argument("--goal-cmd", default="goal"); ap.add_argument("--handoff-cmd", default="handoff")
    ap.add_argument("--out-root", default=str(V3 / "ab" / "build"))
    a = ap.parse_args()
    if a.arm == "A" and not a.plugin_dir:
        ap.error("arm A needs --plugin-dir")
    plugin_dir = Path(a.plugin_dir).resolve() if a.arm == "A" else None
    run_name = f"build-r{a.rep}"
    workdir = SCRATCH / a.arm / a.model / run_name
    if workdir.exists():
        raise SystemExit(f"{workdir} exists")
    shutil.copytree(FIXTURE, workdir)
    turns = json.load(open(TURNS))
    phase1 = turns["turns"]; phase2_prompt = turns["phase2_prompt"]
    prov = {"arm": a.arm, "arm_desc": ARMS[a.arm], "model_alias": a.model, "rep": a.rep, "condition": "build",
            "date": time.strftime("%Y-%m-%d"), "workdir": str(workdir),
            "cli_version": subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip(),
            "plugin_dir": str(plugin_dir) if plugin_dir else None,
            "plugin_commit": (subprocess.run(["git", "-C", str(plugin_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() if plugin_dir else None),
            "fixed_flags": claude_cmd(a.model, "<prompt>", plugin_dir)[:-1], "goal": GOAL if plugin_dir else None}

    # ---- phase 1 (identical in every arm; plugin arm has the plugin loaded and a goal set) ----
    if a.arm == "A":
        run(workdir, a.model, f"/{a.plugin_name}:{a.goal_cmd} {GOAL}", "goal", plugin_dir)
    sid = None
    for i, t in enumerate(phase1, 1):
        text = t["text"]
        if t.get("noise_file"):
            text = f"Read `{t['noise_file']}` — unrelated task: {text} Answer in one sentence."
        r = run(workdir, a.model, text, f"p1-{i}-{t['kind']}", plugin_dir, resume=sid)
        sid = sid or r["session_id"]
    p1_sid = sid
    p1_calls = [json.loads(l) for l in open(workdir / "cli-calls.jsonl")]
    # ---- seam ----
    handover = None
    if a.arm == "A":
        t0 = time.time()
        run(workdir, a.model, f"/{a.plugin_name}:{a.handoff_cmd} {HANDOFF_REASON}", "handoff", plugin_dir, resume=sid)
        briefs = sorted(glob.glob(str(workdir / ".governor" / "handoffs" / "*.md")), key=os.path.getmtime)
        if not briefs:
            raise SystemExit("handoff produced no brief")
        handover = Path(briefs[-1]); sid = None
    elif a.arm == "B":
        run(workdir, a.model, "/compact", "compact", None, resume=sid)
    elif a.arm == "C":
        pass
    elif a.arm == "D":
        sid = None
    elif a.arm == "E":
        run(workdir, a.model, NAIVE_CLEAR, "naive-handover", None, resume=sid)
        handover = workdir / "HANDOVER.md"
        if not handover.exists():
            raise SystemExit("naive handover produced no HANDOVER.md")
        sid = None
    # ---- phase 2 ----
    p2_prompt = phase2_prompt
    if a.arm == "E":
        p2_prompt = "Your previous session left HANDOVER.md in the repository root. " + phase2_prompt
    r = run(workdir, a.model, p2_prompt, "phase2", plugin_dir, resume=sid, timeout=7200)
    p2_sid = r["session_id"]
    # ---- score ----
    items = hidden_tests(workdir, workdir / "hidden-junit.xml")
    feat = [i for i in items if i["kind"] == "feature"]; cons = [i for i in items if i["kind"] == "constraint"]
    score = {"feature_passed": sum(i["passed"] for i in feat), "feature_total": len(feat),
             "constraint_passed": sum(i["passed"] for i in cons), "constraint_total": len(cons),
             "passed": sum(i["passed"] for i in items), "total": len(items), "items": items}
    json.dump(score, open(workdir / "score.json", "w"), indent=2)
    # transcripts: phase 1 session (+seam) and phase 2 session (same file if the session continued)
    ab_run.capture([p1_sid], workdir / "transcript-phase1.jsonl")
    ab_run.capture([p2_sid], workdir / "transcript-phase2.jsonl")
    p1_reads = set(reads_in(workdir / "transcript-phase1.jsonl"))
    p2_reads = reads_in(workdir / "transcript-phase2.jsonl") if p2_sid != p1_sid else []
    if p2_sid == p1_sid:  # arms B and C: phase 2 is the tail of the same transcript; split at the phase-2 prompt
        rows = [json.loads(l) for l in open(workdir / "transcript-phase2.jsonl")]
        idx = max(i for i, row in enumerate(rows) if row["role"] == "user" and phase2_prompt[:60] in row["text"])
        tail = workdir / "transcript-phase2-tail.jsonl"
        tail.write_text("".join(json.dumps(row) + "\n" for row in rows[idx:]))
        p2_reads = reads_in(tail)
    rederived = [p for p in p2_reads if p in p1_reads]
    hidden_access = [p for p in p1_reads | set(p2_reads) if str(HIDDEN) in p or "/reference/" in p]
    verify = ("INVALID: session read hidden tests or the reference: " + str(hidden_access)) if hidden_access else "valid: no access to hidden tests or reference"
    (workdir / "VERIFY.txt").write_text(verify + "\n")
    calls = [json.loads(l) for l in open(workdir / "cli-calls.jsonl")]
    def usage(cs, k): return sum((c.get("usage") or {}).get(k, 0) for c in cs)
    p2c = [c for c in calls if c["_label"] == "phase2"][0]
    prov.update({"phase1_session": p1_sid, "phase2_session": p2_sid, "handover_file": str(handover) if handover else None,
                 "handover_words": {handover.name: len(handover.read_text().split())} if handover else {},
                 "score": {k: v for k, v in score.items() if k != "items"},
                 "turns": sum(c.get("num_turns", 0) for c in calls), "turns_phase2": p2c.get("num_turns"),
                 "cost_usd": round(sum(c.get("total_cost_usd", 0) for c in calls), 4), "cost_phase2_usd": round(p2c.get("total_cost_usd", 0), 4),
                 "tokens_in_phase2": usage([p2c], "input_tokens") + usage([p2c], "cache_read_input_tokens") + usage([p2c], "cache_creation_input_tokens"),
                 "usage": {k: usage(calls, k) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")},
                 "phase2_reads": len(p2_reads), "rederived_reads": len(rederived), "rederived_files": sorted(set(Path(p).name for p in rederived)),
                 "verify": [verify]})
    (workdir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    dest = Path(a.out_root) / a.arm / a.model / run_name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(workdir, dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    print(f"arm {a.arm} {a.model} r{a.rep}: hidden {score['passed']}/{score['total']} (features {score['feature_passed']}/{score['feature_total']}, "
          f"constraints {score['constraint_passed']}/{score['constraint_total']}); rederived reads {len(rederived)}; cost ${prov['cost_usd']}; {verify}")


if __name__ == "__main__":
    main()
