#!/usr/bin/env python3
"""Anatoly's test 4: a new topic arrives mid-work. Same session, or a new session as the plugin advises?

    python3 v3/ab/harness/ab_topic.py --arm S|P|N --model haiku --rep 1 [--plugin-dir ...]

Sequence in every arm: ledgerkit phase 1 (the scripted investigation turns), then topic B (the
shift-roster task in a separate directory, with its own hidden tests), then back to ledgerkit for
phase 2 (the five features). Arms:

  S  one session throughout, no plugin.
  P  one session throughout, plugin loaded, goal set (its advisories fire; nothing else done).
  N  plugin loaded; follow its guidance for a topic change: `/<plugin>:conclude` on the ledgerkit
     investigation, a FRESH session for topic B, then a fresh session for ledgerkit phase 2 that
     loads the conclusion with `/<plugin>:merge <slug>`.

Scores: topic B hidden tests (10), ledgerkit hidden tests (30); cost and turns per phase;
re-derived ledgerkit reads in phase 2. Outputs to v3/ab/topic/<arm>/<model>/topic-r<rep>/.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time, xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ab_run, ab_build
from ab_build import run, hidden_tests, reads_in, FIXTURE, HIDDEN, TURNS, PYTEST, GOAL

V3 = ab_run.V3
TOPIC_B = V3 / "build" / "topic-b"
HIDDEN_B = TOPIC_B / "hidden-tests"
SCRATCH = ab_run.SCRATCH / "topic"
ARMS = {"S": "same session, no plugin", "P": "same session, plugin loaded + goal", "N": "plugin: conclude → fresh session for B → fresh session + merge for phase 2"}
B_PROMPT = ("Different job for a bit, unrelated to this repository. In the directory `{bdir}` there is a spec, `SPEC-B.md`, "
            "an empty package `roster/`, and public tests in `tests/`. Implement the package so that the spec is met and "
            "`python -m pytest tests/` passes there. When it is done, stop and say so in one line.")
CONCLUDE_REASON = "generic"
MERGE_NOTE = "That conclusion is the state of the ledgerkit work; continue from it. "


def hidden_b(bdir, out_xml):
    env = dict(os.environ, ROSTER_REPO=str(bdir), PYTHONPATH=str(bdir))
    subprocess.run([str(PYTEST), "-m", "pytest", str(HIDDEN_B), "-q", "--junitxml", str(out_xml), "-p", "no:cacheprovider"],
                   cwd=str(HIDDEN_B), env=env, capture_output=True, text=True, timeout=600)
    root = ET.parse(out_xml).getroot()
    items = [{"name": tc.get("name"), "passed": tc.find("failure") is None and tc.find("error") is None} for tc in root.iter("testcase")]
    return {"passed": sum(i["passed"] for i in items), "total": len(items), "items": items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=list(ARMS), required=True)
    ap.add_argument("--model", required=True); ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--plugin-dir"); ap.add_argument("--plugin-name", default="context-governor")
    ap.add_argument("--goal-cmd", default="goal"); ap.add_argument("--conclude-cmd", default="conclude"); ap.add_argument("--merge-cmd", default="merge")
    ap.add_argument("--out-root", default=str(V3 / "ab" / "topic"))
    a = ap.parse_args()
    if a.arm in ("P", "N") and not a.plugin_dir:
        ap.error(f"arm {a.arm} needs --plugin-dir")
    plugin_dir = Path(a.plugin_dir).resolve() if a.arm in ("P", "N") else None
    run_name = f"topic-r{a.rep}"
    workdir = SCRATCH / a.arm / a.model / run_name
    if workdir.exists():
        raise SystemExit(f"{workdir} exists")
    shutil.copytree(FIXTURE, workdir)
    bdir = workdir.parent / f"{run_name}-topic-b"          # a sibling directory: a separate job, not part of the repo
    shutil.rmtree(bdir, ignore_errors=True); shutil.copytree(TOPIC_B / "task", bdir)
    turns = json.load(open(TURNS)); phase1 = turns["turns"]; phase2_prompt = turns["phase2_prompt"]
    prov = {"arm": a.arm, "arm_desc": ARMS[a.arm], "model_alias": a.model, "rep": a.rep, "condition": "topic",
            "date": time.strftime("%Y-%m-%d"), "workdir": str(workdir), "topic_b_dir": str(bdir),
            "cli_version": subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip(),
            "plugin_dir": str(plugin_dir) if plugin_dir else None,
            "plugin_commit": (subprocess.run(["git", "-C", str(plugin_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() if plugin_dir else None)}
    # the topic-B directory must be reachable: pass it as an extra --add-dir through ab_build.claude_cmd
    orig_cmd = ab_build.claude_cmd
    def cmd_with_b(model, prompt, pd=None, resume=None):
        c = orig_cmd(model, prompt, pd, resume)
        i = c.index("--add-dir"); return c[:i] + ["--add-dir", str(bdir)] + c[i:]
    ab_build.claude_cmd = cmd_with_b
    prov["fixed_flags"] = cmd_with_b(a.model, "<prompt>", plugin_dir)[:-1]

    # ---- ledgerkit phase 1 ----
    if a.arm in ("P", "N"):
        run(workdir, a.model, f"/{a.plugin_name}:{a.goal_cmd} {GOAL}", "goal", plugin_dir)
    sid = None
    for i, t in enumerate(phase1, 1):
        r = run(workdir, a.model, t["text"], f"p1-{i}-{t['kind']}", plugin_dir, resume=sid)
        sid = sid or r["session_id"]
    s1 = sid
    # ---- topic B ----
    slug = None
    if a.arm == "N":
        run(workdir, a.model, f"/{a.plugin_name}:{a.conclude_cmd} {CONCLUDE_REASON}", "conclude", plugin_dir, resume=sid)
        concl = sorted(glob.glob(str(workdir / ".governor" / "conclusions" / "*.md")), key=os.path.getmtime)
        if not concl:
            raise SystemExit("conclude produced no conclusion file")
        slug = Path(concl[-1]).stem
        sid = None
    rb = run(workdir, a.model, B_PROMPT.format(bdir=bdir), "topic-b", plugin_dir, resume=sid, timeout=7200)
    sb = rb["session_id"]
    if a.arm == "N":
        sid = None
    else:
        sid = sb
    # ---- ledgerkit phase 2 ----
    if a.arm == "N":
        rm = run(workdir, a.model, f"/{a.plugin_name}:{a.merge_cmd} {slug}", "merge", plugin_dir)
        sid = rm["session_id"]
        p2 = MERGE_NOTE + phase2_prompt
    else:
        p2 = "Back to this repository. " + phase2_prompt
    r2 = run(workdir, a.model, p2, "phase2", plugin_dir, resume=sid, timeout=7200)
    s2 = r2["session_id"]
    # ---- scores ----
    sa = hidden_tests(workdir, workdir / "hidden-junit.xml")
    score_a = {"passed": sum(i["passed"] for i in sa), "total": len(sa),
               "feature_passed": sum(i["passed"] for i in sa if i["kind"] == "feature"), "feature_total": sum(1 for i in sa if i["kind"] == "feature"),
               "constraint_passed": sum(i["passed"] for i in sa if i["kind"] == "constraint"), "constraint_total": sum(1 for i in sa if i["kind"] == "constraint"), "items": sa}
    score_b = hidden_b(bdir, workdir / "hidden-b-junit.xml")
    json.dump({"ledgerkit": score_a, "topic_b": score_b}, open(workdir / "score.json", "w"), indent=2)
    sessions = list(dict.fromkeys([s1, sb, s2]))
    ab_run.capture(sessions, workdir / "transcript.jsonl")
    ab_run.capture([s1], workdir / "transcript-phase1.jsonl")
    ab_run.capture([s2], workdir / "transcript-phase2.jsonl")
    p1_reads = set(reads_in(workdir / "transcript-phase1.jsonl"))
    rows = [json.loads(l) for l in open(workdir / "transcript-phase2.jsonl")]
    idx = max((i for i, row in enumerate(rows) if row["role"] == "user" and phase2_prompt[:60] in row["text"]), default=0)
    tail = workdir / "transcript-phase2-tail.jsonl"; tail.write_text("".join(json.dumps(row) + "\n" for row in rows[idx:]))
    p2_reads = reads_in(tail)
    rederived = [p for p in p2_reads if p in p1_reads and str(workdir) in p]
    allreads = p1_reads | set(reads_in(workdir / "transcript.jsonl"))
    hidden_access = [p for p in allreads if str(HIDDEN) in p or str(HIDDEN_B) in p or "/reference/" in p]
    verify = ("INVALID: session read hidden tests or the reference: " + str(hidden_access)) if hidden_access else "valid: no access to hidden tests or reference"
    (workdir / "VERIFY.txt").write_text(verify + "\n")
    calls = [json.loads(l) for l in open(workdir / "cli-calls.jsonl")]
    def usage(cs, k): return sum((c.get("usage") or {}).get(k, 0) for c in cs)
    def phase(label): return [c for c in calls if c["_label"] == label]
    prov.update({"sessions": {"phase1": s1, "topic_b": sb, "phase2": s2}, "conclusion_slug": slug,
                 "score": {"ledgerkit": {k: v for k, v in score_a.items() if k != "items"}, "topic_b": {k: v for k, v in score_b.items() if k != "items"}},
                 "turns": sum(c.get("num_turns", 0) for c in calls), "cost_usd": round(sum(c.get("total_cost_usd", 0) for c in calls), 4),
                 "cost_topic_b_usd": round(sum(c.get("total_cost_usd", 0) for c in phase("topic-b")), 4), "turns_topic_b": sum(c.get("num_turns", 0) for c in phase("topic-b")),
                 "cost_phase2_usd": round(sum(c.get("total_cost_usd", 0) for c in phase("phase2")), 4), "turns_phase2": sum(c.get("num_turns", 0) for c in phase("phase2")),
                 "tokens_in_phase2": usage(phase("phase2"), "input_tokens") + usage(phase("phase2"), "cache_read_input_tokens") + usage(phase("phase2"), "cache_creation_input_tokens"),
                 "rederived_reads": len(rederived), "verify": [verify]})
    (workdir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    dest = Path(a.out_root) / a.arm / a.model / run_name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(workdir, dest, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    shutil.copytree(bdir, dest / "topic-b", ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    print(f"arm {a.arm} {a.model} r{a.rep}: ledgerkit {score_a['passed']}/{score_a['total']}, topic B {score_b['passed']}/{score_b['total']}; "
          f"rederived {len(rederived)}; cost ${prov['cost_usd']} (B ${prov['cost_topic_b_usd']}, phase 2 ${prov['cost_phase2_usd']}); {verify}")


if __name__ == "__main__":
    main()
