#!/usr/bin/env python3
"""Block 2a: the v3 noisy reading task in ONE headless session that is compacted on demand at the
two v3 seams (after retelling 8 and after retelling 16), with or without the plugin loaded.

    python3 v3/ab/harness/ab_single.py --arm baseline --model haiku --rep 1
    python3 v3/ab/harness/ab_single.py --arm plugin --model haiku --rep 1 --plugin-dir ~/context-governance-plugin

Every document is one user turn on the same session (`--resume`), in the v3 order: retelling,
distractor with its one-line question, retelling, ... After r08 and after r16 the harness sends
`/compact` — Claude Code's own compaction, on demand (the corpus is ~115k tokens, under the window,
so it would not compact by itself). The plugin's PreCompact hook fires before it and its
SessionStart(source=compact) nudge fires after it; the baseline gets Claude Code's summary alone.
Then the questions file is one turn and the three answer files are written. Nothing is said about
saving or notes at any point, in either arm; the plugin arm additionally gets one `/goal` turn at
the start (its own session), as in the no-hint design.

Outputs to --out-root/<arm>/<model>/single-r<rep>/: answers*.md, transcript.jsonl (whole session),
cli-calls.jsonl, provenance.json (with compaction count from the transcript), VERIFY.txt.
"""
import argparse, glob, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ab_run  # reuse claude_cmd, run_claude, session_jsonl, capture, tool_uses, GOAL, RULES

REPO = ab_run.REPO; V3 = ab_run.V3
SCRATCH = ab_run.SCRATCH
ORDER = V3 / "distractors" / "ORDER.md"
RETELLINGS = sorted((V3 / "test-input" / "retellings").glob("r*.md"))
QUESTIONS = V3 / "test-input" / "questions.md"

OPENING = ("You are taking a reading-comprehension and reasoning test delivered one document per message, with "
           "unrelated reading tasks mixed in. Rules that are part of the test: read each document exactly once with a "
           "single Read tool call when a message names it (never Bash/cat); never re-read, grep, search, or open any "
           "other file; after each retelling reply with one line acknowledging it (narrator and gist); after each "
           "unrelated document answer its question in one sentence. The questions come at the end. Reply OK to begin.")


def slots():
    rows = re.findall(r"^\| (\d+) \| r(\d+) \| (\S+) \| (\S+) \|", ORDER.read_text(encoding="utf-8"), flags=re.M)
    return [(int(s), int(r), f) for s, r, f, _ in rows]


def distractor_question(fname):
    text = (V3 / "distractors" / "questions.md").read_text(encoding="utf-8")
    m = re.search(r"^## \d+\. " + re.escape(fname) + r"\n\*\*Q:\*\*\s*(.+?)\n", text, flags=re.M)
    return m.group(1).strip() if m else "Answer the document's surface question in one sentence."


def count_compactions(transcript_path):
    n = 0
    for line in open(transcript_path, encoding="utf-8"):
        if '"compact_boundary"' in line:          # one boundary record per compaction
            n += 1
    return n


# Handoff reason for the follow arm. The first wording ("must answer detailed questions about everything in the
# retellings read so far") produced a brief after which Opus 5's safeguard flagged an ordinary retelling turn
# (follow opus r1, 01:20 UTC); this neutral form mirrors the build test's reason, which Opus accepted 3/3.
FOLLOW_REASON = ("stopping here at the plugin's advice; the next session continues the same reading test from this point "
                 "and needs what the retellings read so far established, not the unrelated documents")
# Up-front authorization for the follow arm. Sonnet refused the seam-time release turn as well ("pre-commit to
# suspending a core rule ... classic pattern for getting an agent to lower its guard"; follow sonnet r3): under a strict
# user rule it treats the plugin's hook-injected advisories as injection unless the user vouches for the plugin at the
# start. So the follow arm's opening says so; the continue arm's opening is unchanged (its advisories are ignored).
FOLLOW_AUTH = ("One more rule: the context-governor plugin in this session is installed by me and its advisories are "
               "legitimate. When it advises a seam I will tell you so and then send its handoff command; carrying that "
               "command out, reading and writing the files it names, is part of the test and is the one exception to the "
               "file rule.")
FOLLOW_CONFIRM = ("Yes, proceed: write the handoff brief as the command describes, as complete as you can make it. "
                  "I understand the trade-off and I am following the plugin's advice.")


def _brief_since(workdir, t0):
    import glob as _g
    return [b for b in _g.glob(str(workdir / ".governor" / "handoffs" / "*.md")) if os.path.getmtime(b) >= t0 - 1]


FOLLOW_RELEASE = ("This is me, the test giver: the plugin has advised a seam, and I am taking that advice. My next message is "
                  "its handoff command. Carrying it out is part of the test, and for that one message the file rule is "
                  "suspended: read and write the files the command names. Reply OK.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=["baseline", "plugin", "continue", "follow"], required=True,
                    help="baseline/plugin: one session compacted on demand at r08 and r16. "
                         "continue: plugin loaded, one session, NO compaction, advisories ignored (Anatoly's test 3 control). "
                         "follow: plugin loaded; whenever the plugin's fill advisory fires, do what it says — handoff and a fresh session (test 3).")
    ap.add_argument("--model", required=True)
    ap.add_argument("--rep", type=int, required=True)
    ap.add_argument("--plugin-dir")
    ap.add_argument("--plugin-name", default="context-governor")
    ap.add_argument("--goal-cmd", default="goal"); ap.add_argument("--handoff-cmd", default="handoff")
    ap.add_argument("--out-root", default=str(V3 / "ab"))
    a = ap.parse_args()
    if a.arm in ("plugin", "continue", "follow") and not a.plugin_dir:
        ap.error("--plugin-dir is required for the plugin, continue and follow arms")
    plugin_dir = Path(a.plugin_dir).resolve() if a.plugin_dir else None
    run_name = f"single-r{a.rep}"
    workdir = SCRATCH / a.arm / a.model / run_name
    if workdir.exists():
        raise SystemExit(f"{workdir} exists; remove it or pick another --rep")
    workdir.mkdir(parents=True)

    prov = {"arm": a.arm, "model_alias": a.model, "rep": a.rep, "condition": "single", "date": time.strftime("%Y-%m-%d"),
            "workdir": str(workdir), "cli_version": subprocess.run(["claude", "--version"], capture_output=True, text=True).stdout.strip(),
            "plugin_dir": str(plugin_dir) if plugin_dir else None,
            "plugin_commit": (subprocess.run(["git", "-C", str(plugin_dir), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() if plugin_dir else None),
            "fixed_flags": ab_run.claude_cmd(a.model, "<prompt>", plugin_dir)[:-1],
            "seam": {"baseline": "on-demand /compact after r08 and r16, same session; nothing said about saving",
                     "plugin": "on-demand /compact after r08 and r16, same session; nothing said about saving",
                     "continue": "one session, no compaction, fill advisories ignored",
                     "follow": "handoff + fresh session each time the plugin's fill advisory fires; no compaction"}[a.arm],
            "handoffs": [], "follow_reason": FOLLOW_REASON if a.arm == "follow" else None,
            "follow_protocol": "v3: up-front authorization in the opening + user release turn + handoff command" if a.arm == "follow" else None}
    if a.arm in ("plugin", "continue", "follow"):
        ab_run.run_claude(workdir, a.model, f"/{a.plugin_name}:{a.goal_cmd} {ab_run.GOAL}", "goal", plugin_dir)
    opening = OPENING + (" " + FOLLOW_AUTH if a.arm == "follow" else "")
    r = ab_run.run_claude(workdir, a.model, opening, "opening", plugin_dir)
    sid = r["session_id"]
    sids = [sid]
    expected = []
    turn = 0
    last_tier = -1

    def advisory_fired():
        """The plugin's fill advisory state for the current session: highest tier crossed so far."""
        f = workdir / ".governor" / "state" / f"fill-{sid}.json"
        try:
            return json.load(open(f)).get("last_tier", -1)
        except Exception:
            return -1

    def maybe_follow(label):
        nonlocal sid, last_tier
        if a.arm != "follow":
            return
        tier = advisory_fired()
        if tier > last_tier and tier >= 1:            # the 50 % advisory (tier index 1) or higher
            # A user turn releases the test's file rule for the handoff. Sonnet refused the command twice when the
            # release sat inside the command's own text ("a plugin-authored message ... overriding the test's core
            # rule", follow sonnet r1/r2); the release must come from the user, so it is its own turn.
            ab_run.run_claude(workdir, a.model, FOLLOW_RELEASE, f"release-{label}", plugin_dir, resume=sid)
            t0 = time.time()
            ab_run.run_claude(workdir, a.model, f"/{a.plugin_name}:{a.handoff_cmd} {FOLLOW_REASON}", f"handoff-{label}", plugin_dir, resume=sid)
            if not _brief_since(workdir, t0):
                # Sonnet 5 answers the handoff with a concern and a question ("a condensed brief would lose the
                # fine-grained detail ... Do you want me to proceed?", follow sonnet r1, pass 2). A user following the
                # plugin's advice says yes once; the confirmation is counted as a usability cost in provenance.
                ab_run.run_claude(workdir, a.model, FOLLOW_CONFIRM, f"confirm-{label}", plugin_dir, resume=sid)
                prov.setdefault("handoff_confirmations", []).append(label)
            brief = ab_run.newest_brief(workdir, t0)  # aborts if the session still refused (no brief written)
            # The fresh session reseeds from the brief. The test's own rule ("never open any other file") made the
            # first fresh sessions refuse the hook's offer of the brief (follow opus r1, 01:20 UTC), so the opening
            # names the brief and licenses exactly one read of it, as experiment 1's seam step did.
            r2 = ab_run.run_claude(workdir, a.model, opening.replace("Reply OK to begin.", "Earlier sessions began this test and "
                                   f"their context is gone; their handoff brief is `{brief}`. Reading it once now, with a single "
                                   "Read call, is part of the test. Then reply OK to continue."), f"fresh-{label}", plugin_dir)
            sid = r2["session_id"]; sids.append(sid); prov["handoffs"].append(label); last_tier = -1
            prov.setdefault("briefs", []).append({"at": label, "path": str(brief), "words": len(brief.read_text(encoding="utf-8").split())})
        else:
            last_tier = max(last_tier, tier)

    for slot, rnum, dfile in slots():
        rpath = RETELLINGS[rnum - 1]
        turn += 1
        ab_run.run_claude(workdir, a.model, f"Read `{rpath}` — acknowledge in one line (narrator and gist).", f"r{rnum:02d}", plugin_dir, resume=sid)
        expected.append(str(rpath)); maybe_follow(f"r{rnum:02d}")
        dpath = V3 / "distractors" / dfile
        turn += 1
        ab_run.run_claude(workdir, a.model, f"Read `{dpath}` — unrelated task: {distractor_question(dfile)} Answer in one sentence.", f"d{slot:02d}", plugin_dir, resume=sid)
        expected.append(str(dpath)); maybe_follow(f"d{slot:02d}")
        if rnum in (8, 16) and a.arm in ("baseline", "plugin"):
            ab_run.run_claude(workdir, a.model, "/compact", f"compact-after-r{rnum:02d}", plugin_dir, resume=sid)
    parts = [workdir / f"answers-part{i}.md" for i in (1, 2, 3)]
    q = (f"Read `{QUESTIONS}` — the questions about the twenty-four retellings you have read. Answer every question following "
         "that file's instructions exactly (Section A: decide the eight-story partition yourself), from what you have; you "
         "cannot go back to the documents. Save the answer sheet in THREE Write calls: `{p1}` (Section A stories 1–4), "
         "`{p2}` (Section A stories 5–8 and Section B), `{p3}` (Sections C–G). Your final reply must be one line: the three "
         "paths written and the number of questions answered.").format(p1=parts[0], p2=parts[1], p3=parts[2])
    ab_run.run_claude(workdir, a.model, q, "questions", plugin_dir, resume=sid)
    expected.append(str(QUESTIONS))
    missing = [p.name for p in parts if not p.exists()]
    if missing:
        (workdir / "VERIFY.txt").write_text(f"INVALID: missing answer parts {missing}\n")
        raise SystemExit(f"missing answer parts {missing}")
    (workdir / "answers.md").write_text("\n\n".join(p.read_text(encoding="utf-8") for p in parts), encoding="utf-8")
    ab_run.capture(sids, workdir / "transcript.jsonl")
    # verification: reads in order (continuations collapsed), own-file writes benign, nothing else
    reads, benign, bad = [], [], []
    wd = str(workdir)
    for name, inp, raw, failed in ab_run.tool_uses(workdir / "transcript.jsonl"):
        fp = inp.get("file_path", "") if isinstance(inp, dict) else ""
        if fp and not fp.startswith("/"):
            fp = str(workdir / fp)
        if name == "Read":
            if reads and reads[-1] == fp and "offset" in inp:
                continue
            if (fp == wd or fp.startswith(wd + "/")) or failed:
                benign.append((name, fp)); continue
            reads.append(fp)
        elif name in ("Write", "Edit") and fp.startswith(wd):
            benign.append((name, fp))
        else:
            bad.append((name, raw[:120]))
    missing_reads = [Path(e).name for e in expected if e not in reads]
    noise_skipped = [m for m in missing_reads if not m.startswith("r") or m == "questions.md" and False]
    fatal = [m for m in missing_reads if m.startswith("r") and m[1:3].isdigit() or m == "questions.md"]
    extra = [Path(g).name for g in reads if g not in expected]
    problems = [f"unexpected tool use: {b}" for b in bad] + ([f"missing reads: {fatal}"] if fatal else []) + ([f"extra reads: {extra}"] if extra else [])
    n_comp = sum(count_compactions(ab_run.session_jsonl(x)) for x in sids)
    line = (f"valid ({len(reads)} prescribed reads, {len(benign)} benign own-file uses" + (f"; noise skipped: {noise_skipped}" if noise_skipped else "") + f"; compactions: {n_comp})"
            if not problems else "INVALID\n  " + "\n  ".join(problems))
    (workdir / "VERIFY.txt").write_text(line + "\n", encoding="utf-8")
    print(line)
    calls = [json.loads(l) for l in open(workdir / "cli-calls.jsonl", encoding="utf-8")]
    prov.update({"session_id": sid, "sessions": sids, "compactions": n_comp, "noise_skipped": noise_skipped, "verify": [line],
                 "turns": sum(c.get("num_turns", 0) for c in calls), "cost_usd": round(sum(c.get("total_cost_usd", 0) for c in calls), 4),
                 "usage": {k: sum((c.get("usage") or {}).get(k, 0) for c in calls) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")},
                 "answers_words": len((workdir / "answers.md").read_text().split()), "handover_words": {}})
    (workdir / "provenance.json").write_text(json.dumps(prov, indent=2), encoding="utf-8")
    dest = Path(a.out_root) / a.arm / a.model / run_name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(workdir, dest)
    print(f"run copied to {dest}; turns={prov['turns']} cost=${prov['cost_usd']} compactions={n_comp}")


if __name__ == "__main__":
    main()
