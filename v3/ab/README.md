# Plugin A/B test: does a context plugin change what a Claude Code session retains across a handover?

This directory holds a controlled experiment on top of the v3 story test. The question: when a
Claude Code session has to hand its work to a fresh session (the "seam", which is what compaction
is), does loading a context-management plugin change the score, and what does it cost?

The plugin tested here is the original `context-governor`
(github.com/monolith/context-governor, commit recorded in every run's `provenance.json`). It is a
stand-in: the experiment is written so that a session holding a different plugin can rerun it by
changing three parameters. See "Adapting to another plugin" below.

Results, when present, are in `REPORT.md` (generated) and summarized at the end of this file.

## Two seam designs, and which one is primary

**No hint (`nohint`, primary).** Nobody says anything at the cut. A session reads its documents and
is cut; the next session starts fresh and is told only that earlier sessions began the test and
their context is gone. Identical prompts in both arms. The baseline carries nothing across the cut.
The plugin arm carries whatever the plugin saved on its own: the goal it was given once at the
start, its automatic facts log, anything the model put in the ledger unprompted. No handoff command
is run. This measures what the plugin preserves when the user forgets to ask, which is its pitch.
Decided 2026-09-10 (Anatoly): telling the baseline to write retention notes is extra guidance, and
telling the plugin arm to run its handoff is the same guidance in other words; "no hint to either
is true behavior on its own".

**Hinted (`noisy`, appendix).** The first design. At each cut the baseline is told to write
exhaustive retention notes and the next session reads them; the plugin arm is told to run the
plugin's handoff command and the next session reads its brief. It answers a narrower question:
given an explicit handover, does the plugin's brief carry more or less than exhaustive notes? Runs
made under it before the design changed are kept under `*/noisy-r*/` and reported separately.

## Design in one paragraph

Hold everything fixed and flip one switch. The system under test is a real Claude Code session
run headless (`claude -p`), one fresh session per reading segment, driven from outside by
`harness/ab_run.py`. Both arms get the same model, the same material in the same order, the same
prompts, the same two tools (Read, Write), no user settings, no CLAUDE.md, and the same two
independent judges. The plugin arm adds `--plugin-dir` and sets the plugin's goal once. In the
primary design that is the whole difference; in the hinted appendix the plugin arm additionally
runs the plugin's handoff command at each seam where the baseline writes notes.

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

    claude -p --model <haiku|sonnet|opus> --tools Read,Write --allowedTools Read,Write \
        --disallowedTools Bash Grep Glob Agent WebFetch WebSearch --strict-mcp-config \
        --setting-sources "" --output-format json --add-dir v3/test-input --add-dir v3/distractors

- Working directory: a scratch directory outside the user's home, so no `CLAUDE.md` is loaded.
  `--setting-sources ""` excludes user and project settings, hooks, and other plugins.
- Tool set: exactly Read and Write. `--allowedTools` alone is not enough: headless mode
  auto-approves read-only shell commands (one plugin run listed the material directory with `ls`
  and was voided for it), and the user's MCP connectors were still offered to the session. `--tools`
  removes the other tools from the session; `--strict-mcp-config` removes the connectors. A session
  asked to list its tools under these flags answers "Read, Write". Runs made before this was
  tightened (2026-09-10, before 04:15 UTC) were checked afterwards: none used a shell or
  connector tool except the voided one.
- Prompt: on standard input (the `--add-dir` flag is variadic and would swallow a trailing
  positional prompt).
- Segment files: `v3/runs/sonnet/noisy/segment-{1,2,3}.md` with the notes path rewritten to the
  run's working directory. Same 17/18/19 numbered steps as v3.
- Prompts: the v3 noisy-condition prompts (`v3/PROMPTS.md`), reproduced verbatim in
  `harness/ab_run.py`. The only wording difference between arms is the last sentence of the
  segment 1 and 2 prompts: baseline "its last step has you write retention notes with ONE Write
  call — be exhaustive about everything in the retellings (not the unrelated documents). Your final
  reply to me must be one line: the notes path and an approximate word count"; plugin "its last
  step has you stop before your context is discarded; do not write notes, the handover is done for
  you afterwards. Your final reply to me must be one line: the number of steps you completed".
  The plugin arm's seam step inside the segment file reads: "Your context will now be discarded
  and a fresh reader will continue from a handover. Do not write retention notes yourself: the
  handover will be requested from you as a separate command next, and you should carry it out
  then. Stop here and reply with the number of steps you completed."
  How this wording was arrived at, because it matters for anyone repeating the test on Opus 5:
  the first form ("… reply exactly: READY FOR HANDOFF") was flagged by Opus 5's safeguard as
  "reasoning extraction" two times out of two whenever the plugin's goal anchor was live, while
  the baseline wording passed. A form that said "do not write notes; stop here" passed the
  safeguard but made Sonnet refuse the handoff command ("I was told not to write one"). Putting
  "the handover will be requested from you as a separate command" into the user prompt was flagged
  again (two of two on Opus). The final split, a short prompt tail that passes plus the fuller
  explanation inside the segment file, passed the safeguard and was carried out by all three
  models. Every plugin run made under an earlier wording was voided (scores kept in its `void-*`
  folder) and re-run, so all plugin runs in the report share one wording.
- Judges: `harness/ab_judge.py`, two independent opus sessions with the v3 judge prompt, each
  given the key and the answers and nothing else. Scores in `score.json` and `score-2.json`.
- Provenance per run: CLI version, model alias, plugin directory and git commit, every fixed
  flag, the goal and handoff text, session ids, tokens, turns, API-equivalent dollars, handover
  word counts, verification result (`provenance.json`, `VERIFY.txt`).

## What is switched (plugin arm only)

1. `--plugin-dir <path>` on every session.
2. Before segment 1, one user turn in its own short session: `/<plugin>:goal Read the delivered
   documents in order and answer detailed questions later about everything in the retellings, not
   the unrelated documents.` The plugin stores the goal on disk and its prompt hook re-shows it
   on every later prompt, so segment 1 starts as a fresh session with the anchor live. (The first
   design resumed the goal session for segment 1; Opus 5's safeguard then flagged the next
   message as "reasoning extraction", deterministically, while the identical prompt in a fresh
   session passed. Runs made before 04:30 UTC on 2026-09-10 used the resumed form; their
   `provenance.json` shows the goal and segment-1 session ids equal.)
3. At each seam the segment's last step is replaced by the seam step quoted above, then the
   harness sends, on the same session: `/<plugin>:handoff your context will be discarded; the next
   session must answer detailed questions about everything in the retellings read so far, not the
   unrelated documents. This is the handover the reading instructions said would be requested
   separately: write the brief now, as this command specifies`.
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
still fatal. A Read of a file that does not exist (one no-hint Sonnet session, told that earlier
sessions had begun the test, tried to open a `MEMORY.md` that was never there) returns nothing and
is recorded as benign; the attempt itself is reported, since looking for a memory file is behaviour
worth knowing about.

## Cost accounting

The CLI's JSON result reports `total_cost_usd` and token usage per session at API list prices.
This account is a subscription, so the dollars are what the same run would have cost through the
API; turns and tokens are actual. Both are summed per run into `provenance.json`.

## Running it

One run (`--seam none` is the default and the primary design; `--seam hinted` is the appendix):

    python3 v3/ab/harness/ab_run.py --arm baseline --model haiku --rep 1
    python3 v3/ab/harness/ab_run.py --arm plugin --model haiku --rep 1 \
        --plugin-dir ~/context-governance-plugin --plugin-name context-governor

Judge it twice, then report:

    python3 v3/ab/harness/ab_judge.py v3/ab/baseline/haiku/noisy-r1
    python3 v3/ab/harness/ab_report.py            # -> v3/ab/REPORT.md

A whole lane (one model, both arms alternating, repeats 1–5, judged as they land; set
`AB_SEAM=hinted` for the appendix design):

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

## Results (2026-09-10)

**Primary design, no hint at the cut.** Three models × two arms × five runs, 30 runs, 60 gradings,
every run verified. Judge-averaged score out of 100, mean with 95% interval; paired difference
plugin − baseline by (model, repeat).

| Model | Baseline | Plugin | Plugin − baseline (5 pairs) | Cost per run (both arms) |
|---|---|---|---|---|
| Haiku | 20.3 [15.1, 25.5] | 21.3 [11.5, 31.1] | +1.0 [−10.3, 12.3] | $0.66 |
| Sonnet | 19.5 [9.8, 29.2] | 23.8 [17.3, 30.3] | +4.3 [−11.2, 19.8] | $1.76 |
| Opus | 61.2 [59.1, 63.3] | 62.6 [61.1, 64.1] | +1.4 [−0.9, 3.7] | $3.65 |
| All models | | | +2.2 [−2.5, 6.9], 9 wins of 15 | +3 turns |

Every paired interval includes zero: at this n the runs cannot tell the arms apart. What the plugin
arm carried across each cut was a 29-word goal line and a 112-word list of file paths; no later
session opened either. That is what the plugin's hooks do without a user command (see
`research/promises-readme-skill.md` §2 and §4), so the null is what the code predicts. Opus
scored about 60 in both arms because the last eight retellings alone let it rebuild most of the
history; Haiku and Sonnet, from the same eight, scored about 20.

**Appendix, hinted seam** (baseline told to write exhaustive notes, plugin arm told to run its
handoff; stopped after the design changed, so cells are uneven and wordings varied — see each
run's `provenance.json` and the `void-*` folders): baseline Haiku 33.5/52/60.5, Sonnet 64/57,
Opus 68.5/71.5; plugin Haiku 22–40 across four runs, Sonnet 59.5, Opus under the final wording
pending judgement at the time of stopping. Handover audits: baseline notes carried 77–104 of 112
canon facts; Haiku's plugin briefs carried a few hundred words. Sonnet's baseline notes also
carried 6–14 distractor answers per seam; Haiku's and Opus's carried none.

**What experiment 1 did not test:** the plugin's stated promises. Experiment 2 below does.

Full tables for experiment 1: `REPORT.md` (condition rows `nohint` and `noisy`).

---

# Experiment 2 — tests derived from the plugin's own research (2026-09-10/11)

Experiment 1 cut a session and measured what crossed. The plugin's research and README promise
something narrower and more specific (`research/claims-*.md`, `research/promises-readme-skill.md`):

1. reseeding a fresh session from the plugin's brief beats letting the session compact (claims F9, F5, M11);
2. the goal anchor at the end of every prompt stops drift from standing rules (F4, M8, M9);
3. the post-compaction nudge and the automatic facts log limit what compaction loses (G5, M3);
4. following its advisories to start a new session on context fill, or for a new topic, is cheaper
   at equal quality (B7, E2, F10, G8).

Each block below is one of those promises made into a manipulation, on a task with a hidden answer
key. Anatoly's scoring rules apply throughout: one point per correct in-context item, credit for
what arrives without a user command, cost alongside.

## The fixture: `v3/build/`

A small original Python project, **ledgerkit**, in two phases. Phase 1 is six scripted turns that
make the session investigate the repository: which module owns what, two approaches that fail and
why, a spec amendment announced mid-way, eight standing rules in `docs/CONVENTIONS.md`, and two
unrelated requests interleaved as noise. Ten facts are planted (`facts-key.md`). Phase 2 is one
prompt: implement the five features in `SPEC.md`. Thirty hidden tests (`hidden-tests/`, 20 feature
items, 10 constraint items for the standing rules) run against the result; the session never sees
them or the reference solution (`reference/`, 30/30). A second, smaller job, **topic B**
(`topic-b/`: a shift-roster package, 10 hidden tests), serves the new-topic test.

Phase-2 sessions get Read, Write, Edit, Bash, Grep, Glob and a pytest on PATH, so a session can run
the public tests in `tests/`; the verification step voids any run whose transcript reads the hidden
tests or the reference.

## Block 1 — reseed from a brief, or carry on (`harness/ab_build.py`)

The seam sits between phase 1 and phase 2. Eight arms decide what crosses it:

| Arm | What happens at the seam |
|---|---|
| A | plugin `/handoff`, then a fresh session that starts from the brief the plugin's hook offers |
| B | same session carries on, `/compact` at the seam |
| C | same session carries on, no compaction (full transcript; the cost reference) |
| D | fresh session, nothing crosses (floor) |
| E | no plugin; the model is asked to write `HANDOVER.md`, fresh session told it exists |
| F | plugin loaded, no `/handoff`, fresh session (hooks only) — Anatoly's test 2 |
| G | plugin + `/goal`, same session, no cut — test 1 |
| H | plugin, no `/goal`, same session, no cut — test 1 |

Measures per run: hidden tests passed (feature and constraint separately), re-derived reads
(phase-2 Reads of files phase 1 had already read; the quantity the plugin's cost rule turns on),
tokens at phase-2 start, phase-2 turns and dollars, and the files phase 1 wrote unprompted.

```bash
python3 v3/ab/harness/ab_build.py --arm A --model haiku --rep 1 --plugin-dir /path/to/plugin
python3 v3/ab/harness/ab_build_report.py        # → v3/ab/BUILD-REPORT.md
```

### Results (three runs per cell, 72 runs, all verified)

Hidden tests passed, mean of three runs (out of 30), with the three runs in brackets:

| Arm | Haiku | Sonnet | Opus |
|---|---|---|---|
| A plugin handoff → fresh | 27.0 [26, 28, 27] | 27.0 [27, 27, 27] | 30.0 |
| B carry on, compact | 15.3 [10, 10, 26] | 29.0 [30, 27, 30] | 30.0 |
| C carry on, no cut | 28.3 [27, 29, 29] | 30.0 | 30.0 |
| D fresh, nothing crosses | 26.3 [25, 27, 27] | 27.0 | 30.0 |
| E naive HANDOVER.md | 25.7 [30, 18, 29] | 27.3 [30, 25, 27] | 30.0 |
| F plugin, hooks only, fresh | 26.3 [27, 27, 25] | 27.0 [27, 27, 27] | 30.0 |
| G plugin + goal, no cut | 29.3 [30, 29, 29] | 30.0 | 30.0 |
| H plugin, no goal, no cut | 21.7 [27, 28, 10] | 30.0 | 30.0 |

Paired contrasts (by model and repeat; percent of items, 95% t-interval; wins–ties–losses):

| Contrast | Haiku | Sonnet | Opus |
|---|---|---|---|
| A−B brief vs compaction (the central claim) | +38.9 [−38, +116], 3–0–0 | −6.7 [−21, +8], 0–1–2 | 0, 0–3–0 |
| A−D brief vs nothing | +2.2 [−3, +7], 2–1–0 | 0 | 0 |
| A−E plugin brief vs hand-written handover | +4.4 [−51, +60], 1–0–2 | −1.1 [−22, +20], 1–1–1 | 0 |
| A−C brief vs full transcript | −4.4 [−9, +0.3], 0–0–3 | −10.0, 0–0–3 | 0 |
| F−D hooks only vs nothing (test 2) | 0 [−17, +17], 1–1–1 | 0, 0–3–0 | 0 |
| A−F handoff vs hooks only (test 2) | +2.2 [−10, +15], 2–0–1 | 0, 0–3–0 | 0 |
| G−H goal anchor vs none, no cut (test 1) | +25.6 [−56, +107], 3–0–0 | 0, 0–3–0 | 0 |
| G−C plugin + goal vs no plugin, no cut (test 1) | +3.3 [−11, +18], 1–2–0 | 0 | 0 |

Re-derived reads in phase 2 (mean per run): Haiku A 11 / B 13 / C 3 / D 17 / E 15 / F 15 / G 2 / H 1;
Sonnet A 17 / B 14 / C 2 / D 13 / E 18 / F 23 / G 2 / H 1; Opus A 0.3 / B 7 / C 0.7 / D 3 / E 0.3 / F 1 / G 4 / H 0.3.

What the table says:

- **Compaction is where Haiku loses, and the brief prevents it.** Two of three Haiku runs that
  compacted collapsed to 10/30 (the ten constraint items only); every Haiku run that reseeded from
  the plugin's brief scored 26–28. The paired interval is wide because the third compaction run did
  not collapse, but the direction is 3–0. Sonnet and Opus lose nothing to compaction on this task,
  so A−B is 0 or slightly negative for them.
- **The brief is not better than nothing, or than a hand-written handover, on score.** A−D and A−E
  include zero for every model. A fresh session re-derives what it needs from the repository; the
  brief's contribution shows in re-derived reads (Haiku 11 vs 17; Opus 0.3 vs 3), not in tests passed.
  For Sonnet the brief did not cut re-reads at all (17 vs 13).
- **The full transcript beats any seam** (A−C negative for Haiku and Sonnet): if a session can
  carry on without compacting, it should. The plugin's advice to cut early is a cost trade, and
  test 3 measures it.
- **Test 2, hooks only after a clear (F):** the score equals a plain fresh session (F−D = 0 for all
  nine pairs but two). The plugin's SessionStart injection alone carries nothing a fresh session
  would not rebuild. For Sonnet it raised re-reads (23 vs 13), presumably because the injected file
  list invites opening files.
- **Test 1, the goal anchor (G vs H):** for Haiku the anchored session kept all ten standing rules
  in every run (30, 29, 29) where the unanchored one dropped a rule in two runs and collapsed once
  (27, 28, 10). Sonnet and Opus were perfect either way: in an uncut session the rules are still in
  view and the anchor has nothing to fix, which is what claim M8 predicts.
- **Opus is at the ceiling on every arm** (24 runs, 30/30 each). The task cannot show an Opus
  effect. Opus also wrote its own `memory/` notes unprompted in phase 1 in every run, so for Opus
  "nothing crosses" never held: it made its own handover. Outside arm E (where the file is requested),
  Opus wrote memory files in 21 of 21 runs, Haiku in 7, Sonnet in 2.
- **Haiku's collapse mode is a false completion claim.** All three 10/30 runs (B r1, B r2, H r3)
  end with "all five features implemented"; the code passes no feature test. Compaction makes it
  more frequent (2 of 3) but it also happened once in an uncut plugin session with no goal.

## Block 2a — one compacting session (`harness/ab_single.py`)

The v3 noisy reading run in one session: 48 delivery turns, `/compact` forced after the 8th and
16th story turns, the plugin's PreCompact hook and post-compaction nudge firing in the plugin arm.
The judges classify every lost item as omission or fabrication (claim G5: compaction loses by
omission, not fabrication).

```bash
python3 v3/ab/harness/ab_single.py --arm baseline|plugin --model sonnet --rep 1 --plugin-dir /path/to/plugin
python3 v3/ab/harness/ab_judge.py <run-dir>; python3 v3/ab/harness/ab_report.py
```

### Results (five runs per cell, 30 runs)

| Model | Baseline | Plugin | Plugin − baseline (5 pairs) | Fabrication items, baseline → plugin |
|---|---|---|---|---|
| Haiku | 20.3 [13.1, 27.5] | 19.0 [11.8, 26.2] | −1.3 [−14.5, 11.9], 2–0–3 | 28.3 → 29.4 |
| Sonnet | 43.3 [34.1, 52.5] | 48.6 [44.1, 53.1] | +5.3 [−4.0, 14.6], 4–0–1 | 13.7 → 10.9 |
| Opus | 75.1 [69.6, 80.6] | 80.8 [78.4, 83.2] | +5.7 [−0.1, 11.5], 5–0–0 | 7.0 → 4.5 |
| All | | | +3.2 [−1.2, 7.7], 11 wins of 15 | |

Cost: the plugin arm adds about 3 turns and 2–10 % dollars per run.

- Sonnet and Opus score higher with the plugin in 9 of 10 pairs; Opus's interval just touches zero
  (its five plugin runs, 78.5–83, are the highest reading scores in the study). Haiku is noise.
- The gain is on the fabrication side: with the plugin Sonnet and Opus make fewer specific wrong
  claims after compaction, omissions unchanged. That is the nudge doing what G5 says compaction
  needs, on the two models that can use it.
- Compare experiment 1's null: same corpus, same plugin, but there the seam was a hard cut with
  nothing to nudge. The plugin's automatic value is at compaction, not at a clear.

## Test 3 — the cost of following the fill advisory (`ab_single.py --arm continue|follow`)

Same reading run, one session, no forced compaction. Arms: `continue` (plugin loaded, its advisories
ignored; the session never compacts — the corpus fits the window) and `follow` (plugin loaded; when its
50 % advisory fires, the user runs `/handoff` and continues in a fresh session that reads the brief).
Three runs per cell. The two compacted arms from Block 2a are shown for comparison.

| Model | No plugin, compacted twice (n=5) | Plugin, compacted twice (n=5) | Plugin, advice ignored, never compacts (n=3) | Plugin, advice followed: handoff + fresh session (n=3) |
|---|---|---|---|---|
| Haiku | 20.3, $1.12 | 19.0, $1.14 | 31.7 [25.5, 38, 31.5], $1.27 | 21.5 [8, 32, 24.5], $1.14 |
| Sonnet | 43.3, $3.14 | 48.6, $3.44 | 58.2 [55.5, 53.5, 65.5], $3.38 | 44.5 [48.5, 41.5, 43.5], $2.83 |
| Opus | 75.1, $7.31 | 80.8, $8.04 | 90.5 [88.5, 91.5, 91.5], $9.01 | 80.2 [77.5, 79, 84], $6.83 |

- **Never compacting is the best score for every model**, by 10–14 points over the compacted plugin
  arm. When the corpus fits the window, the plugin's advice to reach a seam at 50 % costs points.
- **Following the advice trades points for dollars:** Opus −10 points for −24 % cost, Sonnet −14 for
  −16 %, Haiku −10 for −10 %. The follow arm lands about where the compacted plugin arm does: a brief
  written at 50 % and a compaction at 95 % lose about the same.
- **A brief launders what the writing session believed.** Haiku's 8-point follow run took the corpus's
  planted corrupted values whole from its 1,200-word brief and answered abstention items with definite
  claims (−25 in deductions); a fresh session cannot doubt what the brief states as fact.
- **Getting a model to follow the advice was itself the finding on usability** (`void-*` folders under
  `follow/`): under the test's strict rule ("never open any other file") Sonnet 5 refused the
  `/handoff` command three times as prompt injection — the release inside the command's text and a
  mid-session user release both failed ("a classic pattern for getting an agent to lower its guard").
  It complied only once the opening prompt authorized the plugin up front, and then once questioned
  the handoff on the merits ("a condensed brief would almost certainly lose the fine-grained detail")
  and asked whether to proceed. Opus and Haiku complied throughout, but Haiku once wrote the brief to
  the repository root instead of the plugin's folder, so the hook never offered it; and Opus's fresh
  session once declined the hook's offer of the brief because the rules forbade opening files. The
  harness now names the brief to the fresh session and licenses one read; both are recorded per run
  (`follow_reason`, `follow_protocol`, `handoff_confirmations` in `provenance.json`).

## Test 4 — a new topic mid-work (`harness/ab_topic.py`)

Sequence: ledgerkit phase 1 → topic B (a separate directory, own hidden tests) → ledgerkit phase 2.
Arms: S (one plain session), P (one session, plugin + goal, advisories ignored), N (the plugin's
flow: `/conclude`, fresh session for topic B, fresh session with `/merge` for phase 2). Three runs per
cell, 27 runs, all verified.

```bash
python3 v3/ab/harness/ab_topic.py --arm N --model haiku --rep 1 --plugin-dir /path/to/plugin
python3 v3/ab/harness/ab_topic_report.py       # → v3/ab/TOPIC-REPORT.md
```

| Model | Arm | Main job % (3 runs) | Side job % | Re-derived reads after the return | $ per run | Turns |
|---|---|---|---|---|---|---|
| Haiku | S one plain session | 72 [93, 93, 30] | 100 | 2.7 | $0.98 | 107 |
| Haiku | P plugin loaded, ignored | 93 [93, 93, 93] | 100 | 2.3 | $0.83 | 94 |
| Haiku | N plugin flow | 91 [100, 83, 90] | 100 | 12.3 | $0.93 | 140 |
| Sonnet | S one plain session | 100 | 100 | 2.3 | $2.18 | 76 |
| Sonnet | P plugin loaded, ignored | 100 | 100 | 1.3 | $2.15 | 77 |
| Sonnet | N plugin flow | 96 [90, 100, 97] | 100 | 17.3 | $1.98 | 101 |
| Opus | S one plain session | 100 | 100 | 4.3 | $4.82 | 66 |
| Opus | P plugin loaded, ignored | 100 | 100 | 3.0 | $5.04 | 70 |
| Opus | N plugin flow | 100 | 100 | 3.7 | $3.91 | 80 |

- **The side job never suffers**: 10/10 in every run of every arm. Doing it inside the main session
  costs nothing on this task; the plugin's conclude/merge detour buys no quality.
- **The plugin's flow is cheaper for the strong models** (Opus −19 %, Sonnet −9 %; N−S paired
  differences −$0.91 and −$0.21 per run) because three short sessions never carry the whole history.
  It also takes more turns (+14 to +33) and, for Sonnet, ~15 more re-reads after the merge: the
  conclusion file is not enough for Sonnet, which rebuilds its picture from the repository. The
  cost of those re-reads is inside the dollar figures, so the saving is net.
- **Haiku's one-session arm collapsed once more** (S r3, 9/30 with a false completion claim). Its
  collapse tally across experiment 2: 4 in 18 long single-session runs (arms B, C, G, H, S, P), 0 in 15
  fresh-session runs (A, D, E, F, N). Every seam arm avoided it; the plugin's flows are among them.
- One Sonnet S run was voided and rerun (`void-logdeleted-topic-r1`): its phase-2 session listed the
  repository root, found the harness's call log, deleted it in its final cleanup and said so. The log
  now lives outside the session's directory for every build and topic run.

## What experiment 2 says, in one place

1. **Where the plugin helps:** Haiku at a compaction (brief 26–28 vs compaction 10–26); Sonnet and
   Opus after compaction (+5 points, fewer fabricated claims); the goal anchor keeps Haiku's standing
   rules (30/29/29 vs 27/28/10); the conclude/merge flow is cheaper for Sonnet and Opus at equal
   quality; every fresh-session arm avoided Haiku's long-session collapse.
2. **Where it does not:** a fresh session after a clear scores the same with the plugin's brief, its
   hooks alone, a hand-written handover, or nothing (Sonnet/Opus/Haiku alike); Sonnet and Opus lose
   nothing to compaction on the build task; never compacting beats every plugin arm on the reading
   task by 10–14 points, and following the fill advisory trades 10–14 points for 10–24 % cost.
3. **Usability:** under a strict user rule Sonnet 5 treated the plugin's injected advisories and its
   handoff command as prompt injection until the plugin was authorized up front, then questioned the
   handoff on the merits once; Haiku once wrote the brief where the hook could not find it; Opus's
   fresh session once declined the hook's offer. A brief launders what the writing session believed
   (Haiku's 8-point follow run).
4. **Ceiling:** Opus scored 30/30 on every build and topic run (45 runs) and Sonnet on nearly all;
   this fixture cannot show an effect for them on the build task. A harder task is the next step
   (`docs/superpowers/brainstorms/2026-09-11-plugin-end-to-end-test.md`).
5. **A window mismatch worth reporting:** Sonnet 5 and Opus 5 run a 1M window in this CLI and
   auto-compact at ≈ 970K (probe, 02:57 UTC). The plugin tiers against 200K unless the model name
   carries "[1m]", which native-1M models do not, so its advisories fire at 6 / 10 / 15 % of the real
   window and its 75 % line calls 150K "auto-compact territory".

## Adapting experiment 2 to another plugin

The same flags as experiment 1: `--plugin-dir`, `--plugin-name`, `--goal-cmd`, `--handoff-cmd`
(`ab_build.py`, `ab_single.py`), plus `--conclude-cmd` and `--merge-cmd` (`ab_topic.py`). The
harness finds the brief through the plugin's SessionStart output, the fill advisory through
`.governor/state/fill-<session>.json`, and the conclusion through `.governor/conclusions/*.md`;
those three paths are the only plugin-specific reads (`newest_brief()`, `advisory_fired()`, and
the glob in `ab_topic.py`). Full tables: `BUILD-REPORT.md`, `REPORT.md` (single-session
section), `TOPIC-REPORT.md`.

