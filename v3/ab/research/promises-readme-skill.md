# context-governor: promises → mechanisms → measurable outcomes

Source of truth read in full: `/home/anatoly/context-governance-plugin/` — `README.md`, `skills/governing-context/SKILL.md`, `commands/{goal,log,summary,handoff,conclude,merge}.md`, `hooks/hooks.json`, `scripts/{session_start,prompt_submit,capture,precompact}.py`, plus `scripts/governor_lib.py` (all four hooks import it; every path/threshold/format below comes from it).

Purpose: map what the plugin claims, in its own words, to observables an experiment can count. No judgment of whether the plugin is good.

**39 promises inventoried (P01–P39).**

Legend for the "auto / user" column:
- **AUTO** — fires from a hook with no user action.
- **AUTO\*** — fires from a hook, but only after some earlier user command created the state it needs (named in the cell).
- **USER** — only happens if the user types a slash command.
- **MODEL** — a behavioral instruction to the model (skill text or injected hook text); nothing in code enforces it.

---

## 1. Inventory of promises

| ID | Promise (quoted) | Where | Mechanism that delivers it | Auto / user | Findings cited |
|---|---|---|---|---|---|
| P01 | "injects fill-threshold advisories the model can't ignore" | README:3 | `UserPromptSubmit` → `prompt_submit.py` writes `hookSpecificOutput.additionalContext` | AUTO | G8, G9, G10 (F3) |
| P02 | "a **continuity ledger** (`.governor/ledger.md`) that the hook re-shows at the end of every prompt so a long session can't drift off it" | README:17; SKILL "Continuity tools"; goal.md | `UserPromptSubmit` → `build_anchor()` prepends `[goal] …` to `additionalContext` | AUTO\* (needs `/goal`, or a model-written `## Goal`) | F4, M9, M8, F10 |
| P03 | "Re-anchors the goal at the end of every prompt (tiny, cache-safe)" | README:23; goal.md "the anchor must stay tiny" | `build_anchor(max_chars=300)` truncates with `…` | AUTO\* (`/goal`) | F4, F10 |
| P04 | "ruled-out lines ride in the anchor" | README:18; log.md | `build_anchor()` appends `" | ruled out: <last bullet under ## Ruled out>"` | AUTO\* (`/log ruled-out`) | F10 |
| P05 | "injects a fill advisory when a tier (30/50/75% of budget) is newly crossed — once per tier, no nagging" | README:23 | `crossed_tier()` + per-session state `.governor/state/fill-<session_id>.json` (`last_tier` monotone) | AUTO | G8, G9, G10 |
| P06 | "Advisories are additive context — a few hundred tokens per session at most (the monitor emits at most once per tier)" | README:73 | 3 fixed `TIER_LINES` strings, max one per tier per session | AUTO | — |
| P07 | "a 1M-context session is tiered against 1M, not the 200K fallback" | README:53 | `resolve_window()` — longest `model_windows` substring match on `message.model` | AUTO | — |
| P08 | "Auto-captures the factual arc (files touched, tests, commands) to `.governor/session-facts.log` every tool call — the record never depends on remembering to log" | README:24; SKILL "Capture is automatic — do not wait to be asked." | `PostToolUse` → `capture.py` → `append_fact()` | AUTO | M3 ("people forget"; no ID given) |
| P09 | "Noisy tools (Grep/Glob and the like) are skipped to keep the log durable" + consecutive-duplicate dedup | capture.py:7; governor_lib.py:287 | `_fact()` whitelist {Read, Edit, Write, NotebookEdit, Bash}; `.governor/state/last-fact` marker | AUTO | — |
| P10 | "the next session is offered the brief automatically" / "Offers the newest unconsumed handoff brief (<48h)" | README:20, 25; handoff.md Step 3 | `SessionStart(source ∈ {startup, clear})` → `offer_brief()` | AUTO\* (needs a prior `/handoff` **and** a `/clear` or new start) | F9, F5 |
| P11 | "**unconsumed** handoff brief" — each brief is offered once | README:25 | `.governor/state/consumed.json` appended `{path, offered_to}` **at offer time** | AUTO\* | — |
| P12 | "offers to set a goal if none" | README:25 | `SessionStart` prints the `/goal` nudge when `get_goal(cwd)` is empty | AUTO | — |
| P13 | "after a compaction, injects a distrust-the-summary + update-the-ledger nudge" | README:25 | `SessionStart(source == "compact")` prints `COMPACT_NUDGE` | AUTO\* (needs Claude Code to compact) | F9 caveat, G5, F5 |
| P14 | "Records that compaction happened (marker + log); no steering" | README:26 | `PreCompact` → writes `.governor/state/compact-pending`, appends to `.governor/state/log` | AUTO\* (needs compaction) | — |
| P15 | "fail-open: never block the session" / "hooks must never block" | all four script docstrings; governor_lib.py:3 | bare `except: pass` + `sys.exit(0)` in every script | AUTO | — |
| P16 | "Precedence: project `.governor/config.json` → user `~/.claude/governor.json` → shipped defaults" + "Tune the marks" | README:42, 55; SKILL "Thresholds are a prompt to act" | `load_config()` shallow per-key merge | AUTO | G8 |
| P17 | "Keep the goal to one tight sentence. If the user's text is long, offer a compressed version rather than storing a paragraph" | goal.md | `/goal` command prompt (model writes `## Goal`) | USER | F4, F10 |
| P18 | "Append the rest as a one-line bullet under that section… Default to **Decisions** if none is given" | log.md | `/log` command prompt (model writes the ledger) | USER | F10 |
| P19 | "Shows both what would be handed over (the ledger) and what the session is thinking right now — your window to catch drift"; "Close with one line: does the **Core** still match the **Goal**?" | README:19; summary.md | `/summary` command prompt | USER | G13 |
| P20 | "fold in any decision or ruled-out item that happened but isn't in the ledger yet; capturing it is your job, not only the user's" | summary.md | `/summary` command prompt (model reads `session-facts.log`) | USER | — |
| P21 | "Writes a **ground-truth-verified** handoff brief"; "Mark every claim in the brief as **verified**… or **unverified**" | README:20; handoff.md Step 1 | `/handoff` command prompt (model runs `git status`, tests, re-reads files) | USER | F10, F5 |
| P22 | "## Contradicted claims (proven false — do not relearn)"; "record the lesson, DROP the details" | handoff.md Step 2 | `/handoff` fixed section template | USER | F10 |
| P23 | "a brief a fresh session can act on in one read (F9: ~300 focused tokens beat ~113K of history). Do not paste transcripts, logs, or dead-end details into it." | handoff.md | `/handoff` command prompt | USER | F9 |
| P24 | "Distils an investigation to a standalone file… dead ends become one-line lessons, details dropped"; "a reader with zero session context should understand it" | README:21; conclude.md | `/conclude` command prompt → `.governor/conclusions/<slug>.md` | USER | F9, F10 |
| P25 | "Loads one conclusion back into a clean session — the distillate, never the noise"; "List the available conclusions… Do not guess"; "Treat its `[unverified]`-tagged claims as unverified" | README:22; merge.md | `/merge` command prompt | USER | F9, F10 |
| P26 | Skill fires "when a session is getting long, a context-fill advisory fired, the session feels degraded or loopy…, after a compaction, or when deciding between /clear, /compact, /handoff, and /conclude" | SKILL frontmatter `description` | Claude Code skill auto-trigger on description match | MODEL | F1–F10, G1–G13, B1–B7 |
| P27 | Decision matrix: "Related work, next phase, session healthy → `/handoff` → `/clear`"; "`/compact` is acceptable — but compaction quality is unmeasured" | SKILL "Decision matrix" | Skill text read by the model | MODEL | F5, F9, F10 |
| P28 | "Your job: at each seam… distil any new **decisions** and **ruled-out** items from those facts into `.governor/ledger.md` yourself… People forget to log; you should not." | SKILL; `COMPACT_NUDGE` (session_start.py:21-22) | Skill text + injected nudge text | MODEL (prompted by AUTO text after compaction) | M3, M10 |
| P29 | "Session degraded → `/handoff` now — do not push on"; "Two corrections from the user on the same point → offer a handoff" | SKILL matrix + "Degradation signals" | Skill text | MODEL (explicitly labeled heuristic) | F5; G13 (absence of evidence) |
| P30 | "**Goal drift → offer to clear.**… say once: 'looks like a new task — want to clear and start fresh?'" | SKILL | Skill text; depends on the anchor carrying a goal | MODEL, needs `/goal` | heuristic; G13 |
| P31 | "Re-verify against ground truth — files, tests, `git status` — before building on summarized claims; prefer re-reading key files over trusting the summary" | SKILL "After a compaction"; `COMPACT_NUDGE` | Skill text + `SessionStart(compact)` injection | MODEL (prompted by AUTO text) | G5, G6, F5 |
| P32 | "**Prefer dropping stale tool output over summarizing it**"; "keep related tool results / retrieved chunks together and near the task" | SKILL "Content-rot hygiene"/"Placement"; TIER_LINES 0–2 | Skill text + advisory text | MODEL (prompted by AUTO advisory) | G9, G10, G8 |
| P33 | "Push verbose, once-needed output (test logs, audits, big file dumps) into subagents; keep the main thread short" | SKILL; TIER_LINES[1] | Skill text + 50% advisory | MODEL | F3 |
| P34 | "**Consult your native remaining-context sense at every seam** and state the runway aloud ('~40% of the window left')" | SKILL "Degradation signals" | Skill text | MODEL (self-report; marked unverified) | model self-knowledge, unverified |
| P35 | "The clearest single cost win: don't switch `/model` or `/effort` mid-long-session" | SKILL "Cost"; README:57 | Advice only — no code enforces it | USER (behavioral) | B2, G3 |
| P36 | "clearing beats continuing when remaining turns R > 22.5·f/(1−f)… a good `/handoff` keeps f low — that's the plugin's cost justification" | README:57; SKILL "Cost" | `/handoff` + `/clear` discipline | USER | B7 (flagged low-confidence scaffold), B1–B3 |
| P37 | "Works in any project; state is project-local." | README:38 | Every path is `Path(cwd)/.governor/...` from the hook payload's `cwd` | AUTO | — |
| P38 | "the plugin's job is upstream — reach a verifiable seam and hand off *before* a lossy layer decides for you" | README:72; SKILL "What the harness already does" | Advisories (AUTO) + `/handoff` (USER) together | AUTO + USER | — |
| P39 | "carries the verified research it is built on… ships inside the plugin at `skills/governing-context/references/`" (48 sources, ~230 claims, 3-vote adversarial verification) | README:3, 5–9; SKILL header | 10 markdown files under `skills/governing-context/references/` | passive (loaded only if the model reads them) | F/G/B/M sets |

---

## 2. What fires without any user action

All four hooks are registered unconditionally in `hooks/hooks.json` (no matchers), each as `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<script>.py"`. Every script reads the hook JSON payload on stdin, keys all state off `payload["cwd"]`, wraps `main()` in `try/except: pass`, and exits 0.

Config gate for each: `load_config(cwd)` merges DEFAULTS ← `~/.claude/governor.json` ← `<cwd>/.governor/config.json` (shallow, per top-level key — so supplying `enabled` replaces the whole dict; missing sub-keys then fall back to `.get(key, True)` in each script).

### SessionStart — `session_start.py`
Gate: `enabled.session_start` (default true). Branches on `payload["source"]`:

**`source ∈ {"startup", "clear"}`:**
1. `offer_brief()`:
   - Reads `.governor/state/consumed.json` (list of `{path, offered_to}`). Creating `.governor/state/` is a side effect of this call, so the directory appears on every startup/clear run.
   - Lists `.governor/handoffs/*.md`, newest mtime first; skips any path already in `consumed.json`.
   - Partitions remaining by `time.time() - mtime < 48*3600` (`FRESH_SECONDS`, marked `[NEW - confirm]` in the source).
   - **If ≥1 fresh:** prints to stdout (→ injected as session context) exactly three things: (a) `[context-governor] Unconsumed handoff brief from <YYYY-MM-DDTHH:MM local>: <absolute path>`; (b) the brief's **first 5 lines verbatim** — under the `/handoff` template that is the `# Handoff: <title>` line, a blank, `## Goal`, the goal text, a blank; (c) `Load it fully with Read before resuming that work; verify its claims against ground truth (git status, tests) first.` Then **writes** `{path, offered_to: session_id}` into `consumed.json`.
   - **Else if ≥1 stale:** prints one line — `[context-governor] Stale handoff briefs exist under .governor/handoffs/ (older than 48h).` No preview, no consumption write.
   - **Else:** nothing.
2. If `get_goal(cwd)` is empty (no non-blank body under `## Goal` in `.governor/ledger.md`, or no ledger at all): prints `[context-governor] No session goal set — run /goal <what you're working on> to anchor it at the end of every prompt (optional).`

**`source == "compact"`:** prints the full `COMPACT_NUDGE` paragraph (verbatim in session_start.py:16-23 — "the summary above is lossy…compaction quality is unmeasured (F9 caveat)…re-verify against ground truth…prefer re-reading key files…Also distil any new decisions/ruled-out from .governor/session-facts.log into .governor/ledger.md now"). Deletes `.governor/state/compact-pending` if present. Appends `compact nudge injected` to `.governor/state/log`.

**Any other source (notably `"resume"`):** nothing at all — no brief offer, no goal nudge, no nudge.

### UserPromptSubmit — `prompt_submit.py`
Two independent parts, joined by a newline into one `additionalContext` string; if both are empty the script prints nothing.

**Anchor** (gate `enabled.anchor`, default true): `build_anchor(cwd)` parses `.governor/ledger.md`. Returns `""` when `## Goal` is empty → nothing injected. Otherwise `"[goal] <goal>"`, plus `" | ruled out: <text of the LAST '- ' bullet under ## Ruled out>"` if any exists, truncated to 300 chars with a trailing `…`. Injected on **every** prompt.

**Fill advisory** (gate `enabled.fill_monitor`, default true):
- `parse_last_usage_and_model(transcript_path)` tail-reads the transcript file — starting at the last 256 KiB, quadrupling to a 4 MiB cap — and scans lines in reverse for the first one containing `"usage"` that parses as JSON with `message.usage.input_tokens` present.
- **Fill estimate** = `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` of that single most-recent assistant usage record. Output tokens are not counted; the current prompt is not yet counted (the number lags one turn). If no such record is found (e.g. the first prompt of a fresh session, or a missing/unreadable transcript path) the function returns `None` and **no advisory is possible**.
- `window` = longest key of `model_windows` that is a substring of `message.model` (shipped: `"[1m]" → 1000000`), else `window_tokens` (200000).
- Thresholds = `round(tier * window)`; default 60,000 / 100,000 / 150,000 tokens (or 300K / 500K / 750K on a `[1m]` model).
- `crossed_tier()` returns the **highest** index whose threshold is met, and only if it exceeds `last_tier` in `.governor/state/fill-<session_id>.json` (default −1). So: at most one advisory per prompt; only upward crossings; if the session opens already past 75%, only the 75% line ever fires; if occupancy falls (post-compaction) and rises again, nothing re-fires within the same session id. A `/clear` produces a new session id, which resets the counter to −1.
- On fire: writes `{"last_tier": N}` to that state file, appends `advisory tier=<N> occupancy=<tokens>` to `.governor/state/log`, and emits **two different strings** — `TIER_LINES[N]` into `additionalContext` (model-visible; 30% = "start pruning dead tool results", 50% = "Prune before you summarize… /conclude or /handoff… push verbose output to subagents", 75% = "auto-compact territory… Prefer a clean /handoff over trusting an in-place summary: /handoff, then /clear") and `SYSTEM_LINES[N]` as top-level `systemMessage` (user-visible only).
- On the first run of a session it also appends `prompt_submit first run; stdin keys=[...]` to `.governor/state/log`.

### PostToolUse — `capture.py`
Gate `enabled.capture` (default true). **Injects nothing into context — no stdout at all.** Writes only.
- `Read`/`Edit`/`Write`/`NotebookEdit` → `"<read|edit|write> <tool_input.file_path or .notebook_path or ?>"`.
- `Bash` → `"bash: <first line of the command, truncated to 80 chars>"`.
- Every other tool (Grep, Glob, Task, WebFetch, TodoWrite, MCP tools, …) → no line.
- `append_fact()` collapses whitespace, then **skips the write if the line is byte-identical to `.governor/state/last-fact`** (the immediately previous captured fact only — non-consecutive repeats are not deduped), otherwise appends to `.governor/session-facts.log` and rewrites the marker.
- "tests" and "commands" in the README's phrase are captured only insofar as they were run through `Bash`; there is no test-specific parsing.

### PreCompact — `precompact.py`
Gate `enabled.precompact` (default true). **Injects nothing.** Writes `.governor/state/compact-pending` containing `"<ISO-8601 seconds> <trigger>"` (trigger = `manual` / `auto` / `unknown`) and appends `precompact trigger=<t>` to `.governor/state/log`. The marker is only ever *deleted* by `SessionStart(source=="compact")`; no code branches on its existence, so the docstring's stated purpose ("lets the next SessionStart know compaction occurred even if that event ever fires without this one") is not implemented — the compaction nudge is driven purely by `source == "compact"`.

### Nothing else fires
No hook ever writes `.governor/ledger.md`, `.governor/handoffs/*`, or `.governor/conclusions/*`. Every ledger line, brief, and conclusion is written by the model in response to a command prompt or the skill's instruction. No hook removes anything from context; all injections are additive.

**Free instrumentation for an experiment:** `.governor/state/log` is an append-only, timestamped record of `advisory tier=N occupancy=T`, `compact nudge injected`, and `precompact trigger=X`. `.governor/state/consumed.json` records which brief was offered to which `session_id`. `.governor/state/fill-<session_id>.json` records the highest tier reached. These are ground truth for "did the mechanism fire", independent of the transcript.

---

## 3. A measurable outcome per promise

Task-shape codes: **R** = reading task with an answer key · **B** = multi-session build with hidden tests · **C** = long session driven past auto-compaction · **D** = debugging task with planted dead ends · **M** = mechanical replay (hook scripts fed synthetic payloads; no model) · **X** = cross-arm token/cost comparison. Arms throughout: plugin-on vs plugin-off (`tests/ab/combinations.json` already defines a `baseline` arm with all hooks disabled).

| ID | Observable that shows it kept or broken | How to count | Task shape |
|---|---|---|---|
| P01 | Advisory text present in the model's input for the turn after a threshold crossing, and the model's next turn references it (prunes, seams, or names the fill) | Count `advisory tier=` lines in `.governor/state/log`; then count turns where the assistant's next message takes a governance action (prune/handoff/conclude) within 2 turns. "Can't ignore" = action-rate ≥ some threshold vs the same prompt with the advisory withheld | C, X |
| P02 | Goal restated/observed at end of context every turn; task-drift rate at high fill | Grep transcript for `[goal] ` occurrences = should equal prompt count after `/goal`. Drift = fraction of assistant turns whose work is off the stated goal, scored by a rubric or an answer key of "in-scope" artifacts | R (long, with an off-topic distractor injected mid-session), B |
| P03 | Anchor length per turn | Measure the `[goal] …` string length in each injected block; assert ≤300 chars; sum across the session for total anchor tokens | M, X |
| P04 | Latest ruled-out item present in every turn's anchor; the model does not re-try a ruled-out approach | Count re-attempts of an approach previously `/log ruled-out` (grep for the tool call or command that implements it) after the log entry | D (dead ends explicitly logged) |
| P05 | Exactly one advisory per tier per session, and never twice for the same tier | Count `advisory tier=N` lines per N per session id in `.governor/state/log`; must be ≤1 each | M, C |
| P06 | Total advisory tokens added per session | Tokenize the three `TIER_LINES` (fixed strings) × number fired; compare against total session input tokens | M, X |
| P07 | On a `[1m]` model, no advisory below 300K occupancy | Replay a fixture that reaches 280K on a `[1m]` model id (`tests/ab/fixtures.py::one_m_model` already does) and assert zero `advisory tier=` lines | M |
| P08 | Every Read/Edit/Write/Bash the model made appears in `session-facts.log`, with no `/log` ever typed | Diff the set of file paths + bash first-lines in the transcript against the lines in `session-facts.log`; recall should be 1.0 for those five tools, 0.0 for Grep/Glob/Task | B, D (any task; the point is the user never logs) |
| P09 | Log contains no Grep/Glob entries; no two adjacent identical lines | Count adjacent duplicates and non-whitelisted tools in `session-facts.log` | M, D |
| P10 | Brief offer text present in session 2's context with zero user action | Presence of `[context-governor] Unconsumed handoff brief from` in session 2's transcript; count sessions where it appeared / sessions where a fresh brief existed | B (two sessions with a `/clear` between; `/handoff` run at the end of session 1) |
| P11 | A brief is offered exactly once across all subsequent sessions | Count entries in `consumed.json` per brief path (must be 1) and count offers across three consecutive sessions (1, then 0, then 0) | B (three sessions) |
| P12 | Goal nudge appears iff `ledger.md` has no `## Goal` body | Presence/absence of `No session goal set` in session start, crossed against ledger state | M, B |
| P13 | Nudge text present immediately after a real compaction | Grep post-compaction transcript for `This session was just compacted`; count compactions with a nudge / total compactions (from `.governor/state/log` `precompact trigger=` lines) | C |
| P14 | `compact-pending` marker written with the right trigger; `precompact trigger=` in the log | Count `precompact trigger=` lines vs the number of compactions the harness actually performed | C |
| P15 | Zero session interruptions when state is corrupt/absent | Feed each hook malformed stdin, a read-only `.governor/`, a truncated `ledger.md`, a non-existent transcript path; assert exit 0, no stderr blocking, session continues | M |
| P16 | Advisory firing points shift when a project `.governor/config.json` sets different tiers | Run the same fixture under `default`, `tiers-early`, `single-tier` arms; compare `fires_at_fill` lists | M |
| P17 | Goal stored is one sentence; long input produces a compression offer, not a stored paragraph | Line/char count of the `## Goal` body after `/goal <200-word paragraph>`; count runs where the model offered a compressed version | R/B with a deliberately verbose goal |
| P18 | `/log ruled-out X` lands as a `- X` bullet under `## Ruled out`; bare `/log X` lands under `## Decisions` | Parse `ledger.md` sections after a scripted sequence of `/log` calls; count correct section routing / total | M-ish (needs the model, but deterministic input) |
| P19 | `/summary` output has both labeled parts and a closing match/drift verdict | Structural check: `## Handover` and `## Core` present, verdict line present; then, on a session deliberately steered off-goal, count runs where the verdict says "drift" (true-positive rate) and runs on-goal where it wrongly says drift (false-positive rate) | R with a planted mid-session task switch |
| P20 | Decisions visible in `session-facts.log` but absent from `ledger.md` are surfaced by `/summary` | Plant N decisions that were never `/log`ged; count how many appear in the Handover section | D |
| P21 | Fraction of brief claims that are true against the repo at brief-write time; presence of verification commands actually run | Score each `[verified]` bullet against `git status`/test output captured independently; count `[verified]` bullets that are false (should be 0) and count whether `git status`/tests appear in the transcript before the brief was written | B, D |
| P22 | Brief contains the fixed sections; every dead end appears as one line with no attached detail | Section presence check (8 headings); count `Failure lessons`/`Contradicted claims` bullets vs the number of dead ends the task planted (recall); count lines >1 sentence (leakage) | D (with k planted dead ends) |
| P23 | Brief token count, and whether a fresh session can act on it in one read | Tokenize the brief (target band ~300–800); then score session 2 against hidden tests **without** giving it the repo history — pass rate is the real measure | B (hidden tests) |
| P24 | Conclusion file is self-contained and lossless on lessons | Give the conclusion file alone to a zero-context grader/model and score it against an answer key of "facts a follow-up must know"; count planted dead ends recorded as one-liners | D, R |
| P25 | `/merge` injects only the conclusion; no transcript content enters | Diff session-3 context against the conclusion file — assert no strings unique to the original session appear; count `[unverified]` claims the model re-checked before using | B (three sessions) |
| P26 | Skill actually loads under each named trigger condition | For each of the 5 trigger conditions in the frontmatter, run a prompt that instantiates it and count skill-invocation events / trials | R, C, D (one trial per condition) |
| P27 | Choice made at a seam: `/handoff`+`/clear` vs in-place `/compact` vs push on | Present a scripted degraded-session decision point; count the distribution of chosen actions, plugin-on vs plugin-off (`evals/decision-clear-vs-compact/` targets exactly this) | C |
| P28 | Ledger grows without any `/log`, and grows specifically at seams | Count `ledger.md` writes (mtime/diff snapshots) in a session where the user never types `/log`; correlate their timing with advisory/compaction events | C, D |
| P29 | Handoff offered after the 2nd correction on the same point | Script a user who corrects the same claim twice; count trials where the model offers a handoff within 1 turn of correction #2 (and false-positive offers on a control with unrelated corrections) | D with scripted corrections |
| P30 | Exactly one "want to clear and start fresh?" offer after a sustained topic switch, and none after a passing tangent | Two conditions (sustained switch / one-off tangent); count offers in each; measure repeat-nagging (should be ≤1 per switch) | R with a planted switch |
| P31 | Post-compaction re-reads before asserting summarized facts | Plant a fact that the compaction summary will lose or garble; count post-compaction turns where the model re-reads the file / runs the test before using it, and count wrong assertions carried from the summary | C with a planted lossy fact |
| P32 | Stale tool output dropped rather than re-summarized; related reads clustered | Count explicit prune actions (re-reads replaced, "dropping" statements) after each advisory; measure fill trajectory slope before vs after the advisory turn | C, X |
| P33 | Verbose output routed to a subagent after the 50% advisory | Count `Task`/subagent launches for log-heavy steps after tier 1 fires, plugin-on vs off; measure main-thread token growth per such step | C, X |
| P34 | Runway statement present at seams | Count assistant turns at seams containing an explicit remaining-context statement; separately check its accuracy against the transcript's actual usage numbers (calibration error) | C |
| P35 | Zero mid-session `/model` or `/effort` switches; if one occurs, the cache-miss cost | Count model/effort switch events; measure the input-token spike on the following request (cache_read → 0) | X (observational; behavioral advice only) |
| P36 | Total tokens and total cost to finish an identical multi-phase task: continue-through vs handoff-and-clear | Sum billed input/output tokens per arm on the same task with the same hidden tests; also estimate `f` empirically = fraction of dropped context re-read in the post-clear session (count re-reads of files already read pre-clear) | B + X (the decisive experiment for the plugin's cost claim) |
| P37 | Two projects run concurrently keep separate ledgers/facts/state | Run two sessions in different cwds; assert no cross-contamination of `ledger.md`, `session-facts.log`, `fill-*.json` | M |
| P38 | A seam is reached before the harness compacts | Count sessions where `/handoff` (or `/conclude`) occurred **before** the first `precompact trigger=auto`, vs sessions where auto-compact landed first, plugin-on vs off | C |
| P39 | Research files are actually consulted, and cited claims match the reference text | Count `Read` calls on `skills/governing-context/references/*` in sessions where the skill fired; spot-check that F/G/B/M IDs quoted in model output match the reference file's text | R, C |

---

## 4. What the plugin does NOT promise

These are the things a tester could reasonably but wrongly expect. What the code actually does is stated in each case.

1. **It does not carry document or file content across a hard session cut when no `/handoff` was run.** Concretely, with no `/handoff` and no `/goal`, `SessionStart(startup|clear)` injects exactly one line — the "No session goal set" nudge — and nothing else. `.governor/session-facts.log` and `.governor/ledger.md` are **never** injected by any hook at session start. The ledger only re-enters context on the *next* `UserPromptSubmit`, and only as the ≤300-char anchor (goal + last ruled-out line), and only if a `## Goal` body exists. The facts log is only ever read if the model chooses to `Read` it. So a hard cut with no commands run carries zero task content forward.
2. **It does not auto-load the handoff brief.** `SessionStart` prints the path, the brief's **first 5 lines**, and an instruction to `Read` it. If the model doesn't read it, the brief's content never enters context — and the brief is marked consumed **at offer time**, so no later session will be offered it again.
3. **It does not fire on session resume.** `session_start.py` handles only `source ∈ {startup, clear, compact}`. A `--resume`/`--continue` start (source `"resume"`) gets no brief offer, no goal nudge, no nudge of any kind.
4. **It does not prune, compress, or remove anything from context.** Every hook output is additive; the advisories themselves *increase* fill. All pruning is a request to the model.
5. **It does not detect degradation.** There is no behavioral signal anywhere in the code. The only input is an occupancy number, and the skill states explicitly (G13) that no published in-flight rot detector survived verification. "Two corrections → offer a handoff" and "goal drift → offer to clear" are labeled heuristics in the skill, with nothing in code behind them.
6. **It does not measure true context fill.** The estimate is the token sum of the **last assistant usage record** (`input + cache_read + cache_creation`), excluding output tokens and excluding the prompt currently being submitted. It lags one turn, and it silently produces no advisory at all when no usage record is found (first prompt of a session, unreadable transcript).
7. **Tiers do not re-fire.** `last_tier` is monotone per session id. After a compaction drops occupancy inside the same session, re-crossing 30% or 50% produces nothing. A session that starts above 75% gets one advisory (the 75% one), never three.
8. **No hook writes the ledger, a brief, or a conclusion.** Those are entirely model output driven by command prompts. If the model ignores the instruction, the files simply don't exist and every downstream promise (anchor, brief offer, merge) silently no-ops.
9. **"Ground-truth-verified" is an instruction, not a verification step in code.** Nothing checks that `git status` or tests were actually run, and nothing validates the `[verified]` tags.
10. **The PreCompact marker does nothing functional.** It is written and later deleted; no branch reads it. Compaction detection is entirely `source == "compact"`.
11. **It makes no claim about compaction quality.** README:25 and the skill both flag compaction fidelity as unmeasured (F9 caveat, G5). The plugin's stated job is to reach a seam *before* a lossy layer runs, not to improve the summary.
12. **The handoff-brief seeding benefit is explicitly not measured.** README:11 and M11 say so in the plugin's own words: "the handoff-brief seeding is inference, not directly measured — the one feature still awaiting a real experiment." The break-even rule B7 is likewise flagged as "synthesis, not directly published… low confidence, flagged as scaffold."
13. **It does not deduplicate the facts log beyond adjacent repeats,** does not rotate or cap it, and does not distinguish tests from other Bash commands.
14. **State is per-`cwd`, not per-user and not per-repo.** Starting a session from a subdirectory yields a different `.governor/` tree with no ledger, no briefs, no tier state.
15. **`/summary`'s "Core" is not a self-diagnosis.** The command itself says a fogged session "can describe its own Core confidently and wrongly" (G13); it is presented as a check for the human to read.
16. **No cost enforcement.** The `/model`-switch rule and the 1-hour TTL preference are prose advice; nothing in the plugin sets a TTL, blocks a switch, or measures spend.

---

## 5. Dependencies between promises

**Hooks alone, no user action, no prior state (the true zero-input arm):**
P01, P05, P06, P07, P08, P09, P12, P15, P16, P37. This is everything a plugin-on-but-user-does-nothing arm can possibly deliver. (P01/P05/P07 additionally require the transcript to contain at least one assistant usage record, i.e. not the first prompt.)

**Require `/goal` to have been run at least once (or the model to have written `## Goal` itself):**
P02, P03, P17, and the drift half of P30 (the skill's rule is conditioned on "if a session goal is set"). Without it, `build_anchor()` returns `""` and the UserPromptSubmit hook contributes nothing but advisories.

**Require `/log` (or model-side distillation, P28) to have populated `## Ruled out`:**
P04, P18.

**Require `/handoff` in the *previous* session, plus a `/clear` or fresh start:**
P10, P11, P23, and the "low f" half of P36. If `.governor/handoffs/` is empty, `offer_brief()` prints nothing and P10/P11 are unobservable rather than broken. If the brief is older than 48h, only the one-line "stale briefs exist" message appears.

**Require `/conclude`, and then `/merge`:**
P24 → P25. `/merge` with no conclusions lists nothing and asks; the chain is dead without `/conclude`.

**Require Claude Code's own compaction to occur:**
P13, P14, P28's post-compaction trigger, P31, and the "before a lossy layer decides" half of P38. If the experiment never drives a session to auto-compact (or never runs `/compact`), `PreCompact` never fires and `SessionStart(source="compact")` never fires, so these promises cannot be tested at all.

**Require the model to load the skill (or to have read the injected hook text and complied):**
P26 → P27, P29, P30, P32, P33, P34, and P28's seam behavior. P31 and P32 have a partial backstop: their instruction text also arrives via the compaction nudge and the tier advisories, so they can fire without the skill loading — that difference is itself worth measuring (skill-on-vs-off, separate from hooks-on-vs-off).

**Require a specific `SessionStart` source:**
P10, P11, P12 need `startup` or `clear`. P13 needs `compact`. Nothing fires on `resume` — an experiment that continues sessions with `--resume` will observe none of these and should not score them as broken.

**Chains worth stating explicitly:**
- `/goal` → anchor (P02/P03) → drift detection (P30) → `/summary`'s verdict line (P19). Break the first link and the last three are untestable.
- `PostToolUse` capture (P08) → model distils at a seam (P28) → ledger (P02/P04) → `/handoff` brief content (P21/P22/P23) → next session's brief offer (P10/P11) → cost claim (P36). This is the plugin's spine: it is fully automatic only at the first step; every later link needs either a command or model compliance.
- Advisory (P01/P05) → pruning/seaming behavior (P32/P33/P38) → the outcome the cost model (P36) assumes. The advisory firing is measurable in `.governor/state/log`; everything downstream is model behavior.

**Independent of everything else:** P15 (fail-open), P16 (config precedence), P37 (project-local state), P39 (research ships in-tree) — all testable mechanically with no model in the loop.
