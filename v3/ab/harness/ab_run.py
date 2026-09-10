#!/usr/bin/env python3
"""A/B driver: one run of the v3 story test's noisy condition as a headless Claude Code session,
with (plugin arm) or without (baseline arm) a plugin loaded. The plugin is the single switch.

    python3 v3/ab/harness/ab_run.py --arm baseline --model haiku --rep 1
    python3 v3/ab/harness/ab_run.py --arm plugin --model haiku --rep 1 \
        --plugin-dir ~/context-governance-plugin --plugin-name context-governor

Fixed for both arms: `claude -p --model <m> --allowedTools Read,Write --setting-sources ""
--output-format json --add-dir <material dirs>`, working directory outside /home/anatoly (so no
CLAUDE.md loads), the v3 reading order, the v3 segment prompts, one fresh session per segment.

The only difference: the plugin arm adds `--plugin-dir`, opens with `/<plugin>:goal <goal>`, ends
segments 1 and 2 with "reply READY FOR HANDOFF" followed by a `/<plugin>:handoff <reason>` turn,
and the next segment's first step reads the newest brief under `.governor/handoffs/` instead of a
notes file. The baseline arm ends segments 1 and 2 with the v3 "write your retention notes" step.

Outputs (copied into --out-root/<arm>/<model>/noisy-r<rep>/): segment-1..3.md, notes or briefs,
answers-part1..3.md, answers.md, transcript-seg1..3.jsonl, cli-calls.jsonl, provenance.json,
VERIFY.txt, and the whole .governor/ tree in the plugin arm.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

REPO = Path("/home/anatoly/llm-intelligence-test")
V3 = REPO / "v3"
TEMPLATE_DIR = V3 / "runs" / "sonnet" / "noisy"           # v3 segment files; only paths are model-specific
TEMPLATE_PREFIX = "/home/anatoly/llm-intelligence-test/v3/runs/sonnet/noisy/"
MATERIAL_DIRS = [str(V3 / "test-input"), str(V3 / "distractors")]
SCRATCH = Path(os.environ.get("AB_SCRATCH", "/tmp/claude-1000/-home-anatoly/24e92440-efc2-4a14-97c2-ee126ebf0ca1/scratchpad/ab"))

GOAL = ("Read the delivered documents in order and answer detailed questions later about everything "
        "in the retellings, not the unrelated documents.")
HANDOFF_REASON = ("your context will be discarded; the next session must answer detailed questions about "
                  "everything in the retellings read so far, not the unrelated documents")

RULES = ("You are taking a reading-comprehension and reasoning test delivered in parts, with unrelated reading "
         "tasks mixed in. Rules that are part of the test: read each document exactly once with a single Read "
         "tool call (never Bash/cat), in the prescribed order, completing every numbered step — skipping one "
         "invalidates the run; never re-read, grep, search, open any other file, or use any other tool; after "
         "each retelling write one line acknowledging it; after each unrelated document answer its question in "
         "one sentence. ")

def prompt_seg12(seg_path, arm):
    tail = {
        "baseline": ("its last step has you write retention notes with ONE Write call before your context is "
                     "discarded — be exhaustive about everything in the retellings (not the unrelated documents). "
                     "Your final reply to me must be one line: the notes path and an approximate word count (no tools for that)."),
        # wording chosen after probing Opus 5's safeguard: "reply exactly: READY FOR HANDOFF" was flagged as
        # reasoning_extraction 2/2 with the plugin's anchor live; this form passed 2/2 (see README)
        "plugin": ("its last step has you stop before your context is discarded; do not write notes, the handover "
                   "is done for you afterwards. Your final reply to me must be one line: the number of steps you completed."),
    }[arm]
    return RULES + f"Start by reading your instruction file `{seg_path}` (one Read call), then follow it exactly; " + tail

def prompt_seg3(seg_path):
    return ("You are finishing a reading-comprehension and reasoning test delivered in parts, with unrelated reading "
            "tasks mixed in. Previous readers read the first sixteen documents and left you notes; their context is "
            "gone. " + RULES[RULES.index("Rules"):] +
            f"Start by reading your instruction file `{seg_path}` (one Read call), then follow it exactly (its first "
            "step is the previous readers' notes; its later steps include the questions file and then the answers). "
            "Answer every question following the questions file's instructions exactly — Section A: decide the "
            "eight-story partition yourself — from the notes and what you read; you cannot go back. Save the answer "
            "sheet in THREE Write calls exactly as the instruction file names them. Your final reply to me must be one "
            "line: the three paths written and the number of questions answered.")

HANDOFF_STEP = ("17. Your context will now be discarded and a fresh reader will continue from a handover. Do not write "
                "notes; stop here and reply with the number of steps you completed.")


def build_segment(n, arm, workdir, handover_in=None):
    """Segment file n for this run: v3 template with paths rewritten; plugin arm swaps the seam steps."""
    text = (TEMPLATE_DIR / f"segment-{n}.md").read_text(encoding="utf-8")
    text = text.replace(TEMPLATE_PREFIX, str(workdir) + "/")
    lines = text.splitlines()
    if arm == "plugin":
        if n in (1, 2):
            i = next(k for k, l in enumerate(lines) if "Your context will now be discarded" in l)
            num = lines[i].split(".")[0]
            lines[i] = f"{num}. " + HANDOFF_STEP.split(". ", 1)[1]
        if n in (2, 3):
            i = next(k for k, l in enumerate(lines) if l.startswith("1. Read "))
            lines[i] = (f"1. Read `{handover_in}` — the previous reader's handover brief (all you have of documents "
                        f"read before you); acknowledge in one line.")
    out = workdir / f"segment-{n}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def claude_cmd(model, prompt, plugin_dir=None, resume=None):
    # --tools limits the tool set itself (Bash/Grep/Glob gone, not merely un-allowed: headless mode
    # auto-approves read-only shell commands otherwise); --strict-mcp-config drops the user's MCP servers.
    cmd = ["claude", "-p", "--model", model, "--tools", "Read,Write", "--allowedTools", "Read,Write",
           "--disallowedTools", "Bash", "Grep", "Glob", "Agent", "WebFetch", "WebSearch",
           "--strict-mcp-config", "--setting-sources", "", "--output-format", "json"]
    for d in MATERIAL_DIRS:
        cmd += ["--add-dir", d]
    if plugin_dir:
        cmd += ["--plugin-dir", str(plugin_dir)]
    if resume:
        cmd += ["--resume", resume]
    cmd.append(prompt)
    return cmd


def run_claude(workdir, model, prompt, label, plugin_dir=None, resume=None, timeout=5400, dry=False):
    cmd = claude_cmd(model, prompt, plugin_dir, resume)
    if dry:
        print(f"[dry] {label}: cwd={workdir}\n      " + " ".join(repr(c) if " " in c else c for c in cmd[:-1]) + f"\n      prompt={prompt[:160]!r}...")
        return {"session_id": "DRY", "num_turns": 0, "total_cost_usd": 0, "usage": {}, "result": ""}
    t0 = time.time()
    # prompt on stdin: --add-dir is variadic and swallows a trailing positional prompt
    p = subprocess.run(cmd[:-1], input=cmd[-1], cwd=str(workdir), capture_output=True, text=True, timeout=timeout)
    try:
        out = json.loads(p.stdout)
    except json.JSONDecodeError:
        out = {"error": "no json", "stdout": p.stdout[-2000:], "stderr": p.stderr[-2000:], "rc": p.returncode}
    out["_label"] = label
    out["_wall_s"] = round(time.time() - t0, 1)
    out["_argv"] = cmd[:-1]
    with open(workdir / "cli-calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    if "error" in out and "session_id" not in out:
        raise SystemExit(f"{label}: claude -p failed: {out}")
    if "safeguards flagged" in str(out.get("result", "")):
        raise SystemExit(f"{label}: the model's safeguard flagged the prompt; run aborted (see cli-calls.jsonl)")
    print(f"{label}: turns={out.get('num_turns')} cost=${out.get('total_cost_usd', 0):.3f} wall={out['_wall_s']}s "
          f"result={str(out.get('result', ''))[:100]!r}")
    return out


def newest_brief(workdir, after_ts):
    briefs = [Path(p) for p in glob.glob(str(workdir / ".governor" / "handoffs" / "*.md"))]
    briefs = [b for b in briefs if b.stat().st_mtime >= after_ts - 1]
    if not briefs:
        raise SystemExit("handoff produced no brief under .governor/handoffs/")
    return max(briefs, key=lambda b: b.stat().st_mtime)


def session_jsonl(session_id):
    hits = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{session_id}.jsonl"))
    return hits[0] if hits else None


def capture(session_ids, out_path):
    files = [session_jsonl(s) for s in session_ids]
    if any(f is None for f in files):
        raise SystemExit(f"session transcript missing for {session_ids}")
    subprocess.run([str(REPO / "v2/harness/.venv/bin/python"), str(REPO / "v2/harness/capture_transcript.py"),
                    *files, "--out", str(out_path)], check=True)


def tool_uses(transcript):
    uses = []
    for line in open(transcript, encoding="utf-8"):
        r = json.loads(line)
        if r.get("role") != "assistant":
            continue
        for m in re.finditer(r"\[tool_use (\w+): (.*?)\]", r["text"], flags=re.S):
            name, payload = m.group(1), m.group(2)
            try:
                inp = json.loads(payload) if payload.startswith("{") else {}
            except json.JSONDecodeError:
                # capture_transcript truncates long tool inputs (Write content); recover the path by regex
                inp = {}
                fm = re.search(r'"file_path":\s*"([^"]+)"', payload)
                if fm:
                    inp["file_path"] = fm.group(1)
                if '"offset"' in payload:
                    inp["offset"] = True
            uses.append((name, inp, payload[:200]))
    return uses


def verify_segment(seg_file, transcript, workdir):
    """Prescribed reads in order; own-output writes and plugin bookkeeping benign; anything else invalid."""
    expected = re.findall(r"^\d+\. Read `([^`]+)`", seg_file.read_text(encoding="utf-8"), flags=re.M)
    expected = [str(Path(workdir) / seg_file.name)] + expected   # the reader saw the workdir copy
    wd = str(workdir)
    prescribed, benign, bad = [], [], []
    for name, inp, raw in tool_uses(transcript):
        fp = inp.get("file_path", "") if isinstance(inp, dict) else ""
        if fp and not fp.startswith("/"):
            fp = str(Path(workdir) / fp)                    # the plugin's commands use paths relative to the cwd
        if name == "Read":
            if prescribed and prescribed[-1] == fp and "offset" in inp:
                continue                                   # continuation of a long file
            if fp.startswith(wd + "/.governor/") and fp not in expected:
                benign.append((name, fp)); continue       # ledger / facts log / brief re-read by plugin turns
            prescribed.append(fp)
        elif name in ("Write", "Edit") and fp.startswith(wd):
            benign.append((name, fp))
        elif name == "Bash" and not any(d in raw for d in MATERIAL_DIRS):
            benign.append((name, raw[:80]))               # plugin's git/test checks; blocked anyway
        else:
            bad.append((name, raw[:120]))
    # collapse an immediate duplicate read of the same file (brief offered by hook, then read as step 1)
    dedup = []
    for fp in prescribed:
        if dedup and dedup[-1] == fp:
            continue
        dedup.append(fp)
    problems = [f"unexpected tool use: {b}" for b in bad]
    # A skipped *unrelated* document (distractor) is recorded, not fatal: it carries no scored material,
    # both arms are subject to the same rule, and re-running until a reader complies would select for
    # compliant runs. A missing retelling, notes/brief, or questions read stays fatal.
    missing = [e for e in expected if e not in dedup]
    noise_skipped = [Path(e).name for e in missing if "/distractors/" in e]
    if missing and len(noise_skipped) == len(missing) and not bad:
        kept = [e for e in expected if e not in missing]
        if dedup == kept:
            return [], len(dedup), len(benign), noise_skipped
    if dedup != expected:
        problems.append(f"read sequence differs: expected {len(expected)} reads, got {len(dedup)}; "
                        f"missing {[Path(e).name for e in expected if e not in dedup]}; "
                        f"extra {[Path(g).name for g in dedup if g not in expected]}; "
                        f"out of order: {[Path(e).name for e in expected if e in dedup] != [Path(g).name for g in dedup if g in expected]}")
    return problems, len(dedup), len(benign), []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["baseline", "plugin"], required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--plugin-dir")
    ap.add_argument("--plugin-name", default="context-governor")
    ap.add_argument("--goal-cmd", default="goal")
    ap.add_argument("--handoff-cmd", default="handoff")
    ap.add_argument("--out-root", default=str(V3 / "ab"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reverify", help="re-run verification on an existing run dir and exit")
    a = ap.parse_args()
    if a.reverify:
        d = Path(a.reverify).resolve()
        wd = Path(json.load(open(d / "provenance.json")).get("workdir", d))
        report = []; all_skipped = []
        for n in (1, 2, 3):
            problems, npres, nben, skipped = verify_segment(d / f"segment-{n}.md", d / f"transcript-seg{n}.jsonl", wd)
            line = (f"segment {n}: valid ({npres} prescribed reads, {nben} benign own-output/plugin uses"
                    + (f"; noise skipped: {skipped}" if skipped else "") + ")" if not problems
                    else f"segment {n}: INVALID\n  " + "\n  ".join(problems))
            print(line); report.append(line); all_skipped.extend(skipped)
        (d / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        prov = json.load(open(d / "provenance.json")); prov["verify"] = report; prov["noise_skipped"] = all_skipped
        (d / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
        return
    if a.arm == "plugin" and not a.plugin_dir:
        ap.error("--plugin-dir is required for the plugin arm")
    plugin_dir = Path(a.plugin_dir).resolve() if a.plugin_dir else None

    run_name = f"noisy-r{a.rep}"
    workdir = SCRATCH / a.arm / a.model / run_name
    if workdir.exists() and not a.dry_run:
        raise SystemExit(f"{workdir} exists; remove it or pick another --rep")
    workdir.mkdir(parents=True, exist_ok=True)
    dry = a.dry_run
    sessions = {}

    prov = {"arm": a.arm, "model_alias": a.model, "rep": a.rep, "date": time.strftime("%Y-%m-%d"), "workdir": str(workdir),
            "cli_version": subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip(),
            "plugin_dir": str(plugin_dir) if plugin_dir else None, "plugin_name": a.plugin_name if plugin_dir else None,
            "plugin_commit": (subprocess.run(["git", "-C", str(plugin_dir), "rev-parse", "HEAD"], capture_output=True,
                                             text=True).stdout.strip() if plugin_dir else None),
            "fixed_flags": claude_cmd(a.model, "<prompt>", plugin_dir)[:-1], "goal": GOAL if (plugin_dir and a.goal_cmd) else None,
            "handoff_reason": HANDOFF_REASON if (plugin_dir and a.handoff_cmd) else None,
            "seam": "plugin handoff command" if (plugin_dir and a.handoff_cmd) else "v3 notes step",
            "goal_session": "separate session; segment 1 starts fresh with the anchor live" if (plugin_dir and a.goal_cmd) else None}

    # ---- segment 1 ----
    seam_arm = a.arm if (a.arm == "baseline" or a.handoff_cmd) else "baseline"   # no handoff command: notes step, plugin loaded
    seg1 = build_segment(1, seam_arm, workdir)
    resume = None
    if a.arm == "plugin" and a.goal_cmd:
        # The goal is set in its own short session; segment 1 then starts fresh with the anchor live
        # (the plugin keeps the goal on disk). Resuming the goal session instead trips Opus 5's
        # safeguard on the very next message ("reasoning_extraction"); a fresh session does not.
        g = run_claude(workdir, a.model, f"/{a.plugin_name}:{a.goal_cmd} {GOAL}", "goal", plugin_dir, dry=dry)
        resume = None
    r = run_claude(workdir, a.model, prompt_seg12(seg1, seam_arm), "segment-1", plugin_dir, resume=resume, dry=dry)
    sessions[1] = [r["session_id"]]
    handover = None
    for n in (1, 2):
        if seam_arm == "plugin":
            t0 = time.time()
            h = run_claude(workdir, a.model, f"/{a.plugin_name}:{a.handoff_cmd} {HANDOFF_REASON}",
                           f"handoff-{n}", plugin_dir, resume=sessions[n][-1], dry=dry)
            handover = workdir / ".governor" / "handoffs" / "DRY.md" if dry else newest_brief(workdir, t0)
        else:
            handover = workdir / ("notes-after-r08.md" if n == 1 else "notes-after-r16.md")
            if not dry and not handover.exists():
                raise SystemExit(f"segment {n} wrote no notes at {handover}")
        seg = build_segment(n + 1, seam_arm, workdir, handover_in=handover)
        prompt = prompt_seg12(seg, seam_arm) if n == 1 else prompt_seg3(seg)
        r = run_claude(workdir, a.model, prompt, f"segment-{n+1}", plugin_dir, dry=dry)
        sessions[n + 1] = [r["session_id"]]
    if dry:
        for n in (1, 2, 3):
            print(f"--- segment-{n}.md ---"); print((workdir / f"segment-{n}.md").read_text()[:1500])
        return

    # ---- assemble, capture, verify ----
    parts = [workdir / f"answers-part{i}.md" for i in (1, 2, 3)]
    missing = [p.name for p in parts if not p.exists()]
    (workdir / "answers.md").write_text("\n\n".join(p.read_text(encoding="utf-8") for p in parts if p.exists()), encoding="utf-8")
    report = []; all_skipped = []
    if missing:
        report.append(f"MISSING answer parts: {missing}")
    for n in (1, 2, 3):
        ids = sessions[n]
        # the plugin arm's goal turn and handoff turns live in the same session as segments 1/2
        capture(ids, workdir / f"transcript-seg{n}.jsonl")
        problems, npres, nben, skipped = verify_segment(workdir / f"segment-{n}.md", workdir / f"transcript-seg{n}.jsonl", workdir)
        line = (f"segment {n}: valid ({npres} prescribed reads, {nben} benign own-output/plugin uses"
                + (f"; noise skipped: {skipped}" if skipped else "") + ")" if not problems
                else f"segment {n}: INVALID\n  " + "\n  ".join(problems))
        print(line); report.append(line); all_skipped.extend(skipped)
    handovers = {}
    if seam_arm == "plugin":
        for b in sorted(glob.glob(str(workdir / ".governor" / "handoffs" / "*.md"))):
            handovers[Path(b).name] = len(Path(b).read_text(encoding="utf-8").split())
    else:
        for nm in ("notes-after-r08.md", "notes-after-r16.md"):
            if (workdir / nm).exists():
                handovers[nm] = len((workdir / nm).read_text(encoding="utf-8").split())
    calls = [json.loads(l) for l in open(workdir / "cli-calls.jsonl", encoding="utf-8")]
    prov.update({"sessions": sessions, "handover_words": handovers, "answers_words": len((workdir / "answers.md").read_text().split()),
                 "turns": sum(c.get("num_turns", 0) for c in calls), "cost_usd": round(sum(c.get("total_cost_usd", 0) for c in calls), 4),
                 "usage": {k: sum((c.get("usage") or {}).get(k, 0) for c in calls) for k in
                           ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")},
                 "model_usage": [c.get("modelUsage") for c in calls if c.get("modelUsage")][:1],
                 "verify": report, "noise_skipped": all_skipped})
    (workdir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    (workdir / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    dest = Path(a.out_root) / a.arm / a.model / run_name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(workdir, dest)
    print(f"run copied to {dest}; turns={prov['turns']} cost=${prov['cost_usd']} handovers={handovers}")


if __name__ == "__main__":
    main()
