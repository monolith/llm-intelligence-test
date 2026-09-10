# Plugin A/B test: does a context plugin change what a Claude Code session retains across a handover?

This directory holds a controlled experiment on top of the v3 story test. The question: when a
Claude Code session has to hand its work to a fresh session (the "seam", which is what compaction
is), does loading a context-management plugin change the score, and what does it cost?

The plugin tested here is the original `context-governor`
(github.com/monolith/context-governor, commit recorded in every run's `provenance.json`). It is a
stand-in: the experiment is written so that a session holding a different plugin can rerun it by
changing three parameters. See "Adapting to another plugin" below.

Results, when present, are in `REPORT.md` (generated) and summarized at the end of this file.

## Design in one paragraph

Hold everything fixed and flip one switch. The system under test is a real Claude Code session
run headless (`claude -p`), one fresh session per reading segment, driven from outside by
`harness/ab_run.py`. Both arms get the same model, the same material in the same order, the same
prompts, the same two tools (Read, Write), no user settings, no CLAUDE.md, and the same two
independent judges. The plugin arm adds `--plugin-dir`, sets the plugin's goal once, and at each
seam runs the plugin's handoff command instead of the baseline's "write your retention notes"
step; the next session reads the plugin's brief instead of the notes. That is the whole
difference.

## Why headless sessions and not subagents

The plugin works through session hooks (session start, prompt submit, after each tool use, before
compaction). A subagent launched from inside another session does not receive the session-start
or prompt-submit hooks, so the plugin's brief pickup and goal anchor would go untested. In
`claude -p` all four hooks fire; this was checked before any run (`.governor/state/log` records
the prompt-submit hook, `session-facts.log` the tool hook, and a fresh session with no access to a
file answered from the brief the previous session's handoff wrote).

## Conditions

**Option A, noisy short condition.** 24 retellings interleaved with 24 unrelated documents in the
fixed order `v3/distractors/ORDER.md`; the reader is replaced after retelling 8 and again after 16
(two seams); the third reader answers the 100-point sheet in three files. Models: haiku, sonnet,
opus. Arms: baseline, plugin. Five runs per cell, 30 runs, 60 gradings.

**Option B, long read-once condition.** The 1.5M-token corpus (eight retellings buried in
62,000-word wrappers, four 220,000-word noise documents), read by a chain of 20+ sessions, each
handing over at a seam, then three question batches answered from the final handover. Models:
sonnet, opus. One run per cell. Direction only.

The v3 runs under `v3/runs*/` were made with a different harness (subagents) and are a cross-check
that this harness reproduces them; they are not the baseline arm.

## What is fixed (both arms)

    claude -p --model <haiku|sonnet|opus> --allowedTools Read,Write --setting-sources "" \
        --output-format json --add-dir v3/test-input --add-dir v3/distractors

- Working directory: a scratch directory outside the user's home, so no `CLAUDE.md` is loaded.
  `--setting-sources ""` excludes user and project settings, hooks, and other plugins.
- Prompt: on standard input (the `--add-dir` flag is variadic and would swallow a trailing
  positional prompt).
- Segment files: `v3/runs/sonnet/noisy/segment-{1,2,3}.md` with the notes path rewritten to the
  run's working directory. Same 17/18/19 numbered steps as v3.
- Prompts: the v3 noisy-condition prompts (`v3/PROMPTS.md`), reproduced verbatim in
  `harness/ab_run.py`. The only wording difference between arms is the last sentence of the
  segment 1 and 2 prompts: baseline "its last step has you write retention notes with ONE Write
  call"; plugin "its last step has you stop before your context is discarded … reply exactly:
  READY FOR HANDOFF".
- Judges: `harness/ab_judge.py`, two independent opus sessions with the v3 judge prompt, each
  given the key and the answers and nothing else. Scores in `score.json` and `score-2.json`.
- Provenance per run: CLI version, model alias, plugin directory and git commit, every fixed
  flag, the goal and handoff text, session ids, tokens, turns, API-equivalent dollars, handover
  word counts, verification result (`provenance.json`, `VERIFY.txt`).

## What is switched (plugin arm only)

1. `--plugin-dir <path>` on every session.
2. Before segment 1, one user turn: `/<plugin>:goal Read the delivered documents in order and
   answer detailed questions later about everything in the retellings, not the unrelated
   documents.` Segment 1 continues in that session (`--resume`).
3. At each seam the segment's last step is replaced by "reply READY FOR HANDOFF", then the harness
   sends, on the same session: `/<plugin>:handoff your context will be discarded; the next session
   must answer detailed questions about everything in the retellings read so far, not the
   unrelated documents`.
4. The next segment starts as a fresh session with the plugin loaded (its session-start hook offers
   the brief) and its step 1 reads the newest file under `.governor/handoffs/` instead of the notes
   file.

Nothing else. In particular the plugin's brief is not told to be exhaustive; it is used as the
plugin designed it.

## Verification before scoring

Every session's transcript (`~/.claude/projects/<cwd>/<session-id>.jsonl`) is reduced with
`v2/harness/capture_transcript.py` and checked: the prescribed reads, in order, and nothing else
opened. Writes to the run's own files and the plugin's bookkeeping (ledger, facts log, brief; its
git or test checks, which the tool allow-list blocks anyway) are counted as benign and listed.
A run that fails is not judged; it is kept in a `void-*/` folder with a note, and re-run with the
identical prompt.

One exception, decided after the pilot: a reader that skips an *unrelated* document (a distractor)
and nothing else is kept and judged, with the skip recorded in `VERIFY.txt`, `provenance.json`
(`noise_skipped`) and the report. Reason: the skipped document carries no scored material, both
arms are subject to the same rule, and re-running until a reader complies would select for
compliant runs. In the pilot, Haiku's baseline reader skipped the last distractor before its notes
write in two runs out of two; the plugin reader, whose last step is a one-line reply, did not. A
missing retelling, notes, brief, or questions read, an extra tool use, or an out-of-order read is
still fatal.

## Cost accounting

The CLI's JSON result reports `total_cost_usd` and token usage per session at API list prices.
This account is a subscription, so the dollars are what the same run would have cost through the
API; turns and tokens are actual. Both are summed per run into `provenance.json`.

## Running it

One run:

    python3 v3/ab/harness/ab_run.py --arm baseline --model haiku --rep 1
    python3 v3/ab/harness/ab_run.py --arm plugin --model haiku --rep 1 \
        --plugin-dir ~/context-governance-plugin --plugin-name context-governor

Judge it twice, then report:

    python3 v3/ab/harness/ab_judge.py v3/ab/baseline/haiku/noisy-r1
    python3 v3/ab/harness/ab_report.py            # -> v3/ab/REPORT.md

A whole lane (one model, both arms alternating, repeats 1–5, judged as they land):

    v3/ab/harness/ab_lane.sh haiku 1 5 ~/context-governance-plugin context-governor

Run lanes for different models in parallel; each lane is one session at a time. A dry run prints
the exact command lines and the generated segment files without calling the CLI:
`ab_run.py ... --dry-run`.

## Adapting to another plugin

Three parameters, no code changes:

- `--plugin-dir <path>`: the plugin's directory (or `.zip`).
- `--plugin-name <name>`: the name in its `.claude-plugin/plugin.json`; commands are invoked as
  `/<name>:<command>` (bare `/command` is "Unknown command" in `claude -p`).
- `--goal-cmd`, `--handoff-cmd`: the plugin's command names for setting a goal and writing a
  handover. If the plugin has no goal command, pass `--goal-cmd ""` and the goal turn is skipped.

One assumption in the code: the handover lands as a markdown file under `.governor/handoffs/` in
the working directory. If the other plugin writes its brief elsewhere, change `newest_brief()` in
`harness/ab_run.py` (one function) to return that path. If the plugin has no handoff command at
all, and relies only on hooks, the plugin-arm seam is instead the baseline's notes step with the
plugin loaded; set `--handoff-cmd ""` (the harness then falls back to the notes step) and say so
in the report.

Check the plugin's hooks fire in `claude -p` before spending anything: run one tiny session with
`--plugin-dir` in an empty directory, read a file, and look for the plugin's state files.

## Reading the result

`REPORT.md` gives, per cell, the mean and a 95% t-interval, and the paired plugin − baseline
difference by (model, repeat) with its interval, paired t, wins, and Cohen's d. The paired table
is the test. An interval that excludes zero at n = 5 is a real effect of the plugin on this task;
one that includes zero means the runs cannot tell the arms apart. Read any gain against the cost
columns: the plugin's extra turns and dollars over the same reading.

Judge disagreement (mean about 2 points in v3) and run-to-run spread are reported separately.

## Results

_Pending. This section is filled from `REPORT.md` when the runs complete._
