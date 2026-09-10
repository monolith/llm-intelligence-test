# Testable claims from the G1–G13 enhancement research

Source: `/home/anatoly/context-governance-plugin/research/2026-07-17-enhancement-research.md`
(deep-research run `wf_5ba62e2d-2d7`, 2026-07-17: 5 angles, 24 sources, 109 claims, 25 verified
3-vote adversarially, 22 confirmed / 3 refuted, 15 findings). Exact figures and study identities
pulled from the companion
`research/2026-07-17-enhancement-source-claims-appendix.md`. Plugin mechanisms quoted from
`/home/anatoly/context-governance-plugin/README.md` ("What it does" table and the "On cost"
paragraph), `skills/governing-context/SKILL.md`, and the hook scripts under `scripts/`.

Harness assumed throughout: `claude -p` headless sessions with Read/Write only, cut at chosen
points or allowed to compact naturally, plugin loaded or omitted via `--plugin-dir`, scored by a
hidden answer key with two independent judges; three models (haiku, sonnet, opus); five runs per
cell (see `/home/anatoly/llm-intelligence-test/v3/ab/README.md`).

**Power note used in every "minimum n" line below.** A paired test at n = 5 per model detects a
mean difference of about 1.24 × the run-to-run SD; pooled over three models (15 pairs) about
0.55 × SD. If the run-to-run SD on the 100-point sheet is ~6 points, that is ~7.4 points within a
model and ~3.3 points pooled. Anything the literature sizes below that is out of reach at this
budget, and the section says so.

---

## G1 — Prompt-cache cost primitives (the baseline every action must beat)

**Claim.** Cache reads bill at 0.1× base input, cache writes at 1.25× (5-minute TTL) or 2× (1-hour
TTL), and the TTL refreshes free on every read, so a continuously-active session pays ~0.1× on its
cached prefix per turn and never re-pays the write; documented break-even is 1.35× uncached for the
5-minute cache and 2.2× for the 1-hour, with 5 minutes the default on API-key billing and 1 hour
auto-requested (free) on a Claude subscription. Sources: Anthropic primary docs —
code.claude.com/docs/en/prompt-caching and platform.claude.com prompt-caching pricing.

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** README "On cost": *"a warm session is cheap (~0.1× base input per
turn; prefix never re-written; TTL refreshes free)"*, and *"Prefer the **1-hour TTL** for gappy
interactive work"*. Also the design constraint on the UserPromptSubmit hook — README calls the goal
anchor *"tiny, cache-safe"* — because the anchor is appended at the end of each prompt rather than
edited into the prefix.

**Testable prediction if the plugin works.** On the Option A noisy-condition reading task, with the
manipulation "plugin loaded vs not", the plugin arm's *cache-creation* input tokens per reading
segment will exceed baseline's by no more than the size of the injected text (goal anchor per turn
plus at most three tier advisories plus the compaction nudge — order 10^3 tokens per segment), and
not by an amount that scales with segment length. Falsified if the plugin arm's cache-creation
tokens grow proportionally to history size, which would mean the anchor is invalidating the prefix
rather than appending to it.

**Substrate and measure.** Substrate: any multi-turn segment where the same session takes several
turns. Manipulate: plugin loaded / omitted. Count: `cache_creation_input_tokens` and
`cache_read_input_tokens` per session from the CLI JSON result, already summed into
`provenance.json`, plus `total_cost_usd`. Minimum n: 1 run per arm suffices for the mechanical
check (cache accounting is near-deterministic); the dollar comparison uses the standard 5 runs.

**Feasibility.** Direct — the harness already records per-session token and dollar accounting in
`provenance.json`; no new instrumentation.

**Caveats the report states.** "TIME-SENSITIVITY: pricing/cache mechanics current for mid-2026 but
Anthropic changes them — the DEFAULT TTL already dropped 1h→5m on 2026-03-06 (claude-code #46829);
re-verify multipliers against live docs before shipping." Also: the test account is a subscription,
so reported dollars are API-equivalent, and the subscription's free 1-hour TTL may not match a
user's API-key billing.

---

## G2 — Compaction invalidates the messages layer but is NOT a cold reprocess

**Claim.** Caching layers as tools → system → messages, and a change invalidates that layer and
everything after it; compaction rewrites history (messages-layer miss) but Claude Code keeps the
cached system layer, reloads project context from disk, and the summarization request itself reuses
the existing prefix — so `/compact` costs one summary pass plus a write on the short new prefix,
not a full cold miss. Microcompaction deletes stale tool-result blocks without rewriting the prefix,
cheaper still. Source: Anthropic's own prompt-caching doc ("Compacting the conversation" section,
quoted verbatim in the appendix verdicts).

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** None — background. The nearest piece is the PreCompact hook,
whose README row is *"Records that compaction happened (marker + log); no steering"* with evidence
column *"—"*. G2 informs how to *price* a compaction, not what the plugin does about one.

**Testable prediction if the plugin works.** Not directly testable against the plugin: the plugin
takes no action that G2 would make better or worse, and the harness cannot make Claude Code price a
compaction differently. It is testable as a *substrate property* — in a session allowed to
auto-compact, the first post-compaction request should show a cache write roughly the size of the
summary plus reloaded project context, not the size of the discarded history, and non-zero cache
reads. Worth running once because every cost interpretation of the compaction arms depends on it.

**Substrate and measure.** Substrate: the Option B long read-once condition, or any Option A segment
deliberately run past the auto-compact threshold. Manipulate: nothing (observational). Count:
cache-creation and cache-read tokens on the turn immediately after compaction versus the turn
before. Minimum n: 2–3 observed compactions; the mechanism is deterministic.

**Feasibility.** Feasible — the harness can let a session compact naturally and read the
per-session usage out of the CLI JSON; no plugin needed.

**Caveats the report states.** Same time-sensitivity caveat as G1 (mechanics are vendor-current, not
stable). The report also flags, under open question 2, that whether Claude Code's own compaction
retains *task utility* on real coding contexts is unmeasured — G2 is a cost statement only.

---

## G3 — Model/effort switch or post-upgrade resume = full re-read (most expensive request)

**Claim.** `/model`, `/effort`, or resuming a session after a Claude Code upgrade re-keys the cache
so the next request reads the entire history at zero cache hits *"even though the content is
identical"*, with cost scaling in conversation depth; the appendix adds fast-mode toggle, MCP
connect/disconnect, plugin MCP changes and denying a whole tool to the same list. Source: Anthropic
prompt-caching doc. The report calls this *"the most concrete, high-confidence cost tip in the whole
pass."*

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** README "On cost": *"Clearest single win: don't switch `/model` or
`/effort` mid-session (re-reads the whole history)."* SKILL.md cost section: *"**The clearest single
cost win: don't switch `/model` or `/effort` mid-long-session** — either re-reads the *entire*
history at zero cache hits, the most expensive request you can send (B2, G3). Same for resuming a
long session right after a Claude Code upgrade."*

**Testable prediction if the plugin works.** On a governance-decision probe appended after a long
reading segment ("I want to switch to a cheaper model for the rest of this session — should I, and
what does it cost?"), the plugin-loaded arm will name the full-history re-read at zero cache hits
and advise against a mid-session switch at a higher rate than the no-plugin arm, scored against an
answer key. Direction: plugin arm > baseline on the "identifies the cache re-read" key item.
Separately and mechanically: switching model mid-session will produce a next-request uncached-input
count ≈ full history size, versus ~0 in the unswitched control.

**Substrate and measure.** Substrate: a single scripted decision question at the end of segment 2,
plus a mechanical control session where `--model` genuinely changes between turns. Manipulate:
(a) plugin loaded / omitted for the advice half; (b) switch / no switch for the mechanical half.
Count: key-item hit rate over runs (advice half); `input_tokens` uncached versus
`cache_read_input_tokens` on the post-switch request (mechanical half). Minimum n: the mechanical
half is deterministic (n = 1–2); the advice half is a binary outcome, so at 5 runs × 3 models = 15
per arm it detects a hit-rate gap of roughly 35 percentage points and no less — under-powered for a
subtle effect, adequate for "never mentions it" versus "always mentions it".

**Feasibility.** Feasible with one extra scripted turn per run; the mechanical half needs a
purpose-built two-turn session because the A/B harness fixes one model per session.

**Caveats the report states.** Time-sensitivity of all cache mechanics. Note also that the advice
half tests whether the plugin's *skill text* is reachable and acted on, not whether G3 is true —
G3's truth rests on vendor documentation, not on this experiment.

---

## G4 — Replayed prefix is 59.5% of serving cost

**Claim.** TraceLab (UW SyFI, June 2026; arXiv:2606.30560), 357,161 steps across 4,265 real
coding-agent sessions: prefix tokens account for 59.5% of cost, appended tokens 29.2%, output 11.2%
— despite the prefix billing at ~1/10 the fresh rate — because the context is replayed every step.
The report flags this as **"a workload characterization, NOT a savings analysis"**: it does not
prove clearing is cheaper.

**Confidence.** CONFIRMED · medium · 3-0.

**Plugin mechanism it motivates.** None as an action — background/motivating fact. It appears in
SKILL.md only as the reason pruning beats clearing: *"file reads are ~70% of fill (G9) and prefix
replay is ~60% of serving cost (B3), so dropping stale reads is where the tokens are."*

**Testable prediction if the plugin works.** Not directly testable against the plugin, for the
reason the report itself gives: 59.5% is a cost *decomposition* of ordinary agent sessions, and no
plugin action is predicted to change it. The plugin's cost claim rests on B7's break-even rule
(`R > 22.5·f/(1−f)`), not on G4. What the harness *can* do is check the decomposition holds on this
substrate (cache-read tokens dominating cost per run), which sets the scale for any cost claim made
about the arms.

**Substrate and measure.** Substrate: any run. Manipulate: nothing. Count: share of billed dollars
attributable to cache reads versus cache creation versus output, from per-session usage. Minimum n:
observational, all runs pooled.

**Feasibility.** Direct — the decomposition comes out of the per-session usage the harness already
records; no plugin, no extra sessions.

**Caveats the report states.** Verbatim: *"a workload characterization, NOT a savings analysis —
because prefix is already cheap while `/clear`/`/compact` force write spikes, this does NOT prove
clearing is cheaper."* And open question 1: the Claude-specific break-even is not supplied by any
source in this pass.

---

## G5 — Real summarization loses information by omission, not fabrication; the compactor model is the lever

**Claim.** OmniCSEval (arXiv:2606.15974, Zhou et al., June 2026 — 28 LLMs, 1,800 conversations, six
scenarios, 128–32k-token contexts, bidirectional fact-checking): faithfulness clusters tightly at
93–96% (real floor ~91%) regardless of model scale, while completeness swings from 16.8%
(GPT-4.1-nano, Screenplay) to 91.2–91.5% (GPT-5 Healthcare / GPT-5-mini) and is model-dominated
(GPT-5 81.7% aggregate versus GPT-4.1-nano 42.6%). So a compaction step drops facts far more often
than it invents them, and *which model writes the summary* is the dominant variable. Degradation is
worst in the long, multi-party, open-ended scenarios (Meeting, Screenplay).

**Confidence.** CONFIRMED · medium · 3-0.

**Plugin mechanism it motivates.** Two hook-driven pieces, both firing without a user command.
(1) SessionStart, README row: *"after a compaction, injects a distrust-the-summary + update-the-ledger
nudge"*; the injected text (`scripts/session_start.py`, `COMPACT_NUDGE`) is verbatim: *"[context-governor]
This session was just compacted — the summary above is lossy and compaction quality is unmeasured
(F9 caveat). Re-verify against ground truth (files, tests, git status) before building on summarized
claims; prefer re-reading key files over trusting the summary (F5: recovery needs consolidation, not
continuation). Also distil any new decisions/ruled-out from .governor/session-facts.log into
.governor/ledger.md now, so the durable state survives this compaction."* (2) The 75% tier advisory
(`scripts/prompt_submit.py`): *"summary fidelity is model-dependent and lossy by omission (G5).
Prefer a clean /handoff over trusting an in-place summary."* Plus SKILL.md's "After a compaction"
section, which states the omission-not-fabrication asymmetry outright.

**Testable prediction if the plugin works.** On the Option A retelling task run so that the reader
session **auto-compacts** rather than being cut cleanly, with the manipulation "plugin loaded (compaction
nudge fires) vs omitted", the plugin arm will lose fewer answer-key points to *omission* — items
answered "not stated / I don't recall" or left blank — than the baseline, with **no** increase in
*fabrication* points (confidently wrong specifics). Direction: omission-loss plugin < baseline;
fabrication-loss plugin ≈ baseline. Two further predictions from the same finding: (a) in both arms,
omission losses will outnumber fabrication losses by a wide margin (the report's asymmetry: ~4%
fabrication against 9–83 percentage points of omission), and (b) the **model** main effect on
retained detail will be larger than the **arm** main effect (haiku < sonnet < opus), because
completeness is model-dominated.

**Substrate and measure.** Substrate: 24 retellings interleaved with distractors, read by a session
allowed to run past the auto-compact threshold, then questioned from the 100-point sheet. Manipulate:
plugin on/off; secondarily, model, to test the model-dominance half. Count: every lost point
classified by the judge as *omission* (no claim made) or *fabrication* (specific claim contradicting
the key) — this classification must be added to the judge prompt, it is not in the v3 rubric.
Minimum n: the model-dominance prediction is backed by a 39-percentage-point spread (81.7 vs 42.6),
so n = 5 per model is ample. The arm effect has no literature size; treat as unknown and report the
paired interval rather than a verdict.

**Feasibility.** Feasible and central — the harness can let a session compact naturally, and the
plugin's SessionStart hook fires on `source=compact` in `claude -p` (the README records that all four
hooks were verified to fire headless). The one addition needed is the omission/fabrication split in
the judging rubric.

**Caveats the report states.** *"DOMAIN TRANSFER: fidelity numbers are financial-filings +
general-conversation, NOT Claude /compact or coding."* *"MODEL TRANSFER: none of the
compaction/pruning studies test Opus 4.8 or Fable 5."* Open question 2: whether Claude Code's own
compaction retains task utility on real contexts is unmeasured. Also, OmniCSEval's contexts top out
at 32k tokens — an order of magnitude below the fill levels the plugin's tiers target.

---

## G6 — Reasoning summarizers: more completeness, slightly more fabrication

**Claim.** Same OmniCSEval paper, Table 4: DeepSeek-R1 versus DeepSeek-V3 scores completeness 71.7%
vs 60.1% and conciseness 83.4% vs 75.8%, but faithfulness 95.7% vs 96.2% (p < 0.01) — a hallucinated-fact
rate moving ~3.8% → ~4.3%. A reasoning compactor retains more and fabricates slightly more.

**Confidence.** CONFIRMED · medium · 3-0.

**Plugin mechanism it motivates.** SKILL.md "After a compaction": *"If you control the compaction, a
stronger model loses fewer facts; a reasoning model retains more but fabricates slightly more (G6)."*
No command or hook acts on it; it is advice the model is meant to apply when choosing how to compact
or who writes the brief.

**Testable prediction if the plugin works.** On the hinted-seam design, holding the *reading* material
and the *answering* model fixed and manipulating which model writes the handover (haiku / sonnet /
opus, or low vs high effort on one model), the brief written by the stronger/reasoning model will
carry more scored facts across the seam — direction: retained-fact count opus > sonnet > haiku, with
the gap on the order of the 11.6-percentage-point completeness gap the study reports. The fabrication
half (+0.5 percentage points) is **not** testable at this budget and should be reported as
unresolved rather than as "no difference".

**Substrate and measure.** Substrate: segment 1 read by model X, which writes the handover; segment 3
answered by a fixed model Y reading only that handover. Manipulate: X across the three models with Y
fixed (a 3 × 1 writer sweep, 15 runs). Count: fraction of the answer key's facts recoverable from the
brief alone (score a "brief-only" answering session), plus fabricated statements in the brief checked
against the source retellings. Minimum n: an 11.6-point completeness gap against ~6-point run SD needs
~5 runs per writer model within-model, or pooled 15 for the ordering; the 0.5-point faithfulness gap
would need hundreds of runs — out of reach.

**Feasibility.** Feasible but it multiplies cells: the writer sweep is a separate 15-run block on top
of the main A/B, and it only exists in the hinted-seam design (in the primary no-hint design nobody
writes a brief on request).

**Caveats the report states.** *"a tradeoff to surface, not a free lunch."* Plus the blanket model-transfer
caveat: the R1/V3 comparison is on non-Anthropic models at ≤32k context, and no study in the set tests
current Anthropic models.

---

## G7 — Restoring compaction-lost facts buys ~8.4pp accuracy

**Claim.** LANTERN (arXiv:2606.05182, Cisco, single author, 2026): re-injecting facts lost to
compaction improved accuracy by +8.4 percentage points across four LLMs including Claude Sonnet 4.5
on fact-bearing questions. The same paper reports ">50% of specific facts are lost after a single
compaction event". The report grades the source **WEAK** and the companion claim that LANTERN-Rerank
recovers 78.3% of lost facts was **refuted** (1-2) — only the +8.4pp effect survived.

**Confidence.** CONFIRMED · low · 3-0, on an explicitly weak source ("single-author preprint,
small/mini model panel, LLM-judge — magnitude likely doesn't transfer").

**Plugin mechanism it motivates.** The entire continuity chain: `/handoff` (README: *"Writes a
ground-truth-verified handoff brief, then you `/clear`; the next session is offered the brief
automatically"*), the PostToolUse capture hook (*"Auto-captures the factual arc (files touched, tests,
commands) to `.governor/session-facts.log` every tool call"*), and the SessionStart nudge's second half
(*"distil any new decisions/ruled-out from .governor/session-facts.log into .governor/ledger.md now, so
the durable state survives this compaction"*). This is the closest thing in the G set to a direct
prediction about the plugin's headline value.

**Testable prediction if the plugin works.** On the Option A noisy condition with two seams, with the
manipulation "plugin loaded vs not" (primary no-hint design), the plugin arm's final 100-point score
will exceed the baseline's, paired by (model, repeat), by a margin in the neighbourhood of 8 points.
Falsified if the paired interval is centred at or below zero.

**Substrate and measure.** Substrate: the existing three-segment noisy condition, unmodified.
Manipulate: plugin loaded / omitted. Count: the 100-point sheet, two judges, paired difference by
(model, repeat). Minimum n: at 8 points against a ~6-point run SD, within-model n = 5 sits right at
the detection edge (~7.4 points detectable); pooled across three models (15 pairs, ~3.3 points
detectable) it is comfortable. So: report the pooled paired interval as the test and the per-model
intervals as description.

**Feasibility.** Direct — this is exactly what the existing harness runs; no modification.

**Caveats the report states.** *"WEAK SOURCE: single-author preprint, small/mini model panel,
LLM-judge — magnitude likely doesn't transfer to Opus 4.8 / Fable 5 … treat 8.4pp as illustrative."*
The recovery-fraction half was refuted outright. Also relevant from the plugin's own README: the
handoff-brief seeding is *"inference, not directly measured — the one feature still awaiting a real
experiment."*

---

## G8 — The 16–32K knee is obsolete; arrangement drives failure, not token count

**Claim.** PredicateLongBench (arXiv:2607.08284, Jain & Velingker, NVIDIA, 9 July 2026) at a **fixed**
128K budget: Opus 4.6 scores 97% on plain lexicographic locate but 1% under scattered adversarial
near-miss decoys (GPT-5.4 2%, best model Gemini 3.1 high 10%); holding tokens at 128K while growing
the unique-word search space from ~26K to ~60K words drops GPT-5.4 from 92% to 10%; and identical
distractors **clustered** near the target restore Opus 4.6 to ~98% while the same distractors
**scattered** collapse it to ~1% — *"clustering near-sorted decoys near the target sequence restores or
even exceeds baseline accuracy, while the same decoys scattered across the context cause catastrophic
collapse."*

**Confidence.** CONFIRMED · medium · three 3-0 votes and one 2-1 (the dissent: the paper says "not
*just* token count", so "not token count" overstates it).

**Plugin mechanism it motivates.** The 30% tier advisory (`scripts/prompt_submit.py`): *"Not a
degradation claim — fill is a prompt to act, not a cliff (G8). The real risk is scattered
stale/duplicate tool output accumulating"*; the 50% advisory: *"Cluster related context near the task —
scattered near-duplicates are a specific rot trigger (G8)"*; README's tier paragraph: *"The tiers are a
**prompt to act, not a degradation claim** … failure is driven by task difficulty and content
*arrangement* at a fixed budget, not raw count (G8)"*; SKILL.md's "Placement" section, bullet
*"Arrangement beats token count for current models (G8)."*

**Testable prediction if the plugin works.** On the retelling task at a **fixed** total token count,
with the manipulation "retellings scattered among distractors (the current `v3/distractors/ORDER.md`)
versus retellings clustered contiguously and adjacent to the question segment", the scattered
condition will score lower than the clustered condition in **both** arms, and the plugin's advantage
(plugin − baseline) will be **larger** in the scattered condition than in the clustered one — because
scattering is the condition its advisories are written for. Falsified if arrangement makes no
difference at fixed length, or if the plugin's advantage is flat across arrangements.

**Substrate and measure.** Substrate: two orderings of the same 24 retellings + 24 distractors,
identical token totals, identical prompts. Manipulate: arrangement (2) × plugin (2) × model (3).
Count: the 100-point sheet; secondarily, whether the plugin arm's notes/ledger actually group related
material (a manipulation check on whether the advice was acted on). Minimum n: the literature's
arrangement effect is enormous (98% vs 1% synthetic, ~49% on the real-word variant), so if any
meaningful fraction transfers, 5 runs per cell is far more than enough; the *interaction* with the arm
is unsized — unknown.

**Feasibility.** Feasible — a second ORDER file and a rerun; no harness code changes beyond the
segment generator's input order. It doubles the run count for that block (12 cells × 5 = 60 runs), so
it is the most expensive addition proposed here.

**Caveats the report states.** *"single 8-day-old preprint; 'not token count' overstates its own 'not
JUST token count' (length still contributes — the one dissent); ~1% is the synthetic-string variant
(real-word → ~49%, same pattern)."* The benchmark is a synthetic predicate-retrieval task, not prose
comprehension — transfer to a retelling task is an assumption this experiment would be testing, not
inheriting.

---

## G9 — File reads dominate coding-agent fill (67–76%)

**Claim.** SWE-Pruner (arXiv:2601.16746, Wang/Shi et al., Jan 2026) on SWE-bench Verified: for Claude
Sonnet 4.5, read-type operations consume 76.1% of total tokens against execute 12.1% and edit 11.8%;
for GLM-4.6, reads are 67.5%. The appendix adds a stronger neighbouring figure from "The Complexity
Trap": observation (tool-result) tokens are ~84% of an average SWE-agent turn, with a practitioner
source citing 30,400 of 48,400 tokens (~63%) per trajectory.

**Confidence.** CONFIRMED · medium · 3-0. Caveat carried in the finding itself: it is a
reads-versus-other-tools composition, not a literal tool-versus-conversation split.

**Plugin mechanism it motivates.** The 30% tier advisory: *"file reads are ~70% of fill (G9). Plan a
verifiable seam and start pruning dead tool results."* SKILL.md content-rot hygiene: *"**File-read
output is 67-76% of a coding session's context (G9)** — it is the primary thing to govern. When a read
is no longer needed, drop it."*

**Testable prediction if the plugin works.** On the reading task, with the manipulation "measure the
composition of each session's context", Read tool results will be the dominant share of non-system
input tokens (predicted >60%), which is the precondition the 30% advisory asserts. Arm-level
prediction: because the advisory names reads specifically, the plugin arm's post-advisory behaviour
should show fewer redundant re-reads of already-read files than baseline (direction: plugin <
baseline on repeat-read count). Falsified if reads are not the dominant share on this substrate — in
which case the advisory's premise does not hold here and any G10/G11 result on this harness is
uninterpretable.

**Substrate and measure.** Substrate: any run; measured from the reduced transcript
(`v2/harness/capture_transcript.py`). Manipulate: none for the composition check; plugin on/off for
the re-read count. Count: token share of Read tool-result blocks versus assistant text versus prompts;
number of Read calls on a path already read in the same session. Minimum n: composition is stable —
3 runs; the re-read count is bounded near zero in this harness (reads are prescribed) so the arm half
is likely to be a null by construction — say so rather than reporting a null as evidence.

**Feasibility.** Feasible now; the transcript reducer already exists and every run is verified against
a prescribed read list, so re-reads are already detectable.

**Caveats the report states.** *"CAVEAT: reads-vs-other-tools composition, not literal
tool-vs-conversation split."* And the domain gap: SWE-bench coding trajectories versus a document
reading task — the share may hold while the *prunability* does not.

---

## G10 — Dropping stale tool output matches summarization at half the cost

**Claim.** "The Complexity Trap: Simple Observation Masking Is as Efficient as LLM Summarization for
Agent Context Management" (Lindenbauer et al., JetBrains Research/TUM; arXiv:2508.21433; NeurIPS 2025
DL4Code workshop — **the only peer-reviewed and reproducible source in the whole set**, code at
JetBrains-Research/the-complexity-trap). In SWE-agent on SWE-bench Verified across five model configs,
masking older environment observations halves total cost relative to the raw agent while matching or
slightly exceeding LLM-summarization solve rate (Qwen3-Coder-480B 54.8% masked vs 53.8% summarized;
the five configs are within ±1 point either way), and a masking+summarization hybrid saves a further
7% / 11%.

**Confidence.** CONFIRMED · medium · 3-0 · PEER-REVIEWED.

**Plugin mechanism it motivates.** The 50% tier advisory, verbatim: *"Prune before you summarize: for
coding tool-output, DROPPING stale reads matches summarization at half the cost (G10). Wrap the step,
then /conclude (finished) or /handoff (next phase)."* SKILL.md: *"**Prefer dropping stale tool output
over summarizing it (G10 — peer-reviewed).**"* This fires from a hook, with no user command.

**Testable prediction if the plugin works.** The harness cannot let a session delete its own context,
so test the mechanism by *constructing* the seam. On the Option A task, at the seam, build three arms
that receive identical prior material: **masked** (prior Read results elided from the next session's
input, actions and reasoning retained), **summarized** (an LLM-written summary of the same prior
material), and **raw** (everything carried). Prediction: masked ≈ summarized on the 100-point sheet
(difference within a few points, no consistent sign), masked ≈ half the billed cost of raw, and masked
cheaper than summarized (it skips the summarizer call). Separately, the plugin-arm prediction: when a
plugin-loaded session is asked at a seam how to shrink its context, it will recommend dropping stale
reads over summarizing them at a higher rate than a no-plugin session.

**Substrate and measure.** Substrate: the constructed three-arm seam above, plus the scripted seam
question for the plugin half. Manipulate: seam treatment (3) × model (3). Count: the 100-point sheet;
`total_cost_usd` and token totals per run; for the advice half, key-item hit rate. Minimum n: the cost
half is a ~2× effect and is detectable at n = 1–2 per cell. The *equivalence* half is not reachable —
the paper's masked-vs-summarized gap is ≤1 point over 500 tasks; at 5 runs a 1-point difference is
invisible, so report an interval and explicitly decline to claim equivalence.

**Feasibility.** Feasible with Read/Write only: the harness already generates each segment's input
file, so eliding or summarizing prior reads is a change to that generator, not to the CLI invocation.
The summarized arm costs one extra session per run.

**Caveats the report states.** *"DOMAIN TENSION: mechanical dropping is fine for coding tool-output but
token-pruning flipped ~50% of financial decisions — pruning safety is content-dependent"* (see G12).
The retelling task is prose, not tool output, so this substrate sits on the *dangerous* side of that
tension — which is precisely why the G12 manipulation below belongs in the same block.

---

## G11 — Task-aware pruning saves ~23–38% on coding without hurting success

**Claim.** SWE-Pruner (arXiv:2601.16746) on SWE-bench Verified with a 0.6B goal-conditioned "skimmer":
Claude Sonnet 4.5 −23.1% tokens with success 70.6% → 72.0%, GLM-4.6 −38.3%, interaction rounds down
18–26%. The report grades this **WEAK**: self-reported, single preprint, two models, Python-only; the
"54%" ceiling comes from SWE-QA, not SWE-bench Verified; the apparent third-party corroboration turned
out to be mirror pages (which drove the 2-1 vote).

**Confidence.** CONFIRMED · low · 2-1.

**Plugin mechanism it motivates.** None — background. The plugin ships no pruner; README lists it under
credits as *"Related 2026 research, not yet integrated: SWE-Pruner"*. The finding only supports the
advisory's *claim that pruning is worth doing*, not any mechanism that does it.

**Testable prediction if the plugin works.** Testable, but as a **negative**: on the reading task, with
the manipulation "plugin loaded vs not", the plugin arm will **not** show a 23–38% reduction in input
tokens, because the plugin has no pruning mechanism — its additions (per-turn goal anchor, up to three
advisories, ledger and facts-log writes, and in the hinted design an extra handoff turn) push tokens
and dollars *up*. Predicted direction: plugin arm total tokens ≥ baseline. If a token *reduction*
appears anyway it would have to come from changed model behaviour and should be traced in the
transcripts before being credited. This is the honest test of whether the 23–38% figure has any bearing
on this plugin.

**Substrate and measure.** Substrate: the existing runs. Manipulate: plugin on/off. Count: total input
tokens and `total_cost_usd` per run, decomposed into cache-read / cache-creation / uncached. **Measure
billed dollars, not token counts** — an appendix search-lead ("Token Reduction Is Not Cost Reduction",
2,848 Claude Code runs over Haiku 4.5 / Sonnet 5 / Opus 4.8) found a −38.4% raw-token cut producing a
+6.8% billed-cost *increase* (95% CI +2.8…+11.3), because cost is caching-dominated. That lead is
appendix-only and was not promoted to a graded finding, but it is the reason token savings must not be
reported as cost savings. Minimum n: the plugin's overhead is small and deterministic; 5 runs per cell
gives a usable interval.

**Feasibility.** Direct — the accounting is already collected per run.

**Caveats the report states.** *"WEAK: self-reported, single preprint, 2 models, Python-only; the '54%'
ceiling is not from SWE-bench Verified; apparent third-party corroboration is mirror pages … bank the
low end, treat '20-40% Claude Code savings' as unvalidated until reproduced."*

---

## G12 — Mechanical token-pruning is dangerous for decision-bearing prose

**Claim.** "When Summaries Distort Decisions: Information Fidelity in LLM-Compressed Financial Analysis"
(arXiv:2606.29251, Lee et al., June 2026, ~18 authors incl. Zhangyang Wang and Alejandro Lopez-Lira),
Table 2 decision-flip rates on MD&A 10-Q / earnings-call transcripts: no compression 11.0% / 8.8%;
one-shot LLM summarization 33.0% / 23.9%; LLMLingua token-pruning 53.0% / 50.8%; LongLLMLingua 50.0% /
39.1%. Mechanical pruning distorted roughly half of all decisions and did *worse* than an LLM-written
summary — the mirror image of G10's coding result.

**Confidence.** CONFIRMED · medium · 3-0.

**Plugin mechanism it motivates.** The drop-versus-summarize split the hooks encode: SKILL.md hygiene —
*"Reserve summarization for content where omission changes meaning (decisions, requirements) —
mechanical pruning of *decision-bearing prose* flipped 24-53% of choices in one study (G12), but stale
*tool output* is safe to drop"* — and the `/conclude` and `/handoff` templates, whose ledger sections
are explicitly Goal / Decisions / Ruled-out so that decision-bearing lines survive a seam while details
are dropped.

**Testable prediction if the plugin works.** Add a decision-bearing layer to the material: a chain of
stated decisions and reversals inside the retellings, with answer-key items of the form "which option
was settled on, and what was ruled out". On that task, with the seam manipulated as in G10 (masked /
summarized / raw), the **masked** arm will flip more decision items than the **summarized** arm, while
on plain descriptive-detail items masked ties or beats summarized. Direction: interaction between seam
treatment and item type. And the plugin-arm prediction: because the ledger keeps decisions and
ruled-out lines explicitly, the plugin arm will lose fewer decision items across the seam than the
baseline, even where it does no better on descriptive items.

**Substrate and measure.** Substrate: the retelling corpus with a decision chain planted and ~20
decision items added to the key. Manipulate: seam treatment (3) × item type (2) × plugin (2). Count:
decision-flip rate (answer contradicts the settled decision) versus omission rate, per item type.
Minimum n: the literature's gap is 53.0% vs 33.0% — about 20 percentage points. With ~20 decision items
per run and 5 runs, each cell holds ~100 items, enough to resolve a 20-point flip-rate difference; the
per-run pairing is what carries the interval.

**Feasibility.** Feasible but it requires new material (a planted decision chain) and new key items —
the largest content change proposed here. Everything else in the harness is unchanged.

**Caveats the report states.** *"CAVEAT: financial domain, GPT compressor — conflicts with G10
(coding)."* The reconciliation the plugin relies on ("drop stale tool output freely; be careful
compressing reasoning/decisions") is the report's own inference from two studies in two domains, not a
measured boundary — testing it is the point.

---

## G13 — In-flight behavioral rot detection: no surviving evidence (absence IS the finding)

**Claim.** No claim survived verification about mid-session behavioral signals of degradation —
correction counts, self-consistency drift, abstention or sycophancy shifts, loops — nor about models
self-reporting degradation, nor about monitors that trigger resets from behavioral signals; the seed
article's claim (e) (models can self-report rot) remains UNVERIFIED. The two claims put to a vote from
the rate-distortion survey (arXiv:2607.08032, Colaco & Lahjouji) were refuted 0-3 and 1-2. The report
treats the absence as the finding and says any behavioral detector *"would ship AHEAD of published
evidence."*

**Confidence.** Graded MEDIUM as a finding-of-absence; the underlying votes were 0-3 and 1-2 refuted.

**Plugin mechanism it motivates.** A deliberate non-mechanism, plus one command. README's `/summary`
row: *"Shows both what would be handed over (the ledger) and what the session is thinking right now —
your window to catch drift"*, evidence column *"G13: the model can't reliably self-report degradation,
so you check"*. SKILL.md's degradation-signals section keeps the two-corrections rule but labels it:
*"(heuristic — from the seed article. A dedicated research pass found NO published evidence for any
in-flight behavioral rot signal … So this is an untested rule of thumb, not an evidence-backed
detector; use it, but don't build automation on it yet.)"* The plugin builds no correction-counter,
which G13 is cited to justify.

**Testable prediction if the plugin works.** Testable as a negative, and worth running because it is the
justification for a whole class of features *not* built. On the reading task, ask the session at fixed
intervals (after each block of retellings) two questions: how much of its window remains, and how
reliably it could answer detail questions about what it has read. Prediction: the self-reported
reliability estimate will correlate near zero with the score subsequently earned on the items covering
that block (predicted |r| < 0.3), across all three models and both arms. If instead self-report tracks
accuracy well, G13's basis weakens and an in-flight signal becomes worth building. Second, cheaper
prediction: the count of user corrections in a run will not predict that run's score either.

**Substrate and measure.** Substrate: interval probes inserted into the existing reading segments.
Manipulate: nothing about the plugin (this tests the finding, not the plugin); optionally probe
position (early / mid / late in the window). Count: self-reported confidence (0–100) per block against
scored accuracy on that block's key items; and the remaining-window estimate against the transcript's
actual occupancy. Minimum n: none supplied by the literature (the finding is an absence). A correlation
estimate needs pairs, not runs: 3 blocks × 5 runs × 3 models = 45 pairs, enough to bound |r| but not to
prove a null.

**Feasibility.** Feasible — the probes are extra turns in an existing session, and the plugin's own
`.governor/state/log` plus the transcript give the ground-truth occupancy to compare against. Cost:
a few extra turns per run.

**Caveats the report states.** *"CAVEAT: absence in one pass ≠ empty field"* and, under open question 4,
that a dedicated targeted search is warranted. The appendix supports that hedge: it holds extracted but
never-verified leads that bear directly on the probe design — SYCON Bench's Turn-of-Flip / Number-of-Flip
sycophancy metrics; an "Arbiter" monitor whose passive detection of subtle misalignment ran at F1 0.12
against 0.51 with active interrogation (i.e. passive telemetry, which is what this plugin's hooks
collect, is the weak version); a finding that the first clear failure indicator in agent trajectories
appears only after 59.0–83.6% of the trajectory, with high-relevance evidence in just 4.7–11.3% of
turns; and a metacognition study that *deliberately avoids* model self-reports as its measure. None of
these are graded findings — treat them as design input for the probe, never as support.

---

## Findings ranked by how directly the plugin's value depends on them

1. **G5 — compaction loses by omission, model-dominated.** The SessionStart nudge and the 75% advisory
   exist because of it, both fire without a user command, and the "distrust the summary" instruction is
   only worth its tokens if omission is the real failure mode.
2. **G7 — restoring compaction-lost facts buys accuracy.** The whole ledger → facts-log → handoff-brief
   chain is a bet on this effect; it is also the plugin's weakest-sourced load-bearing finding, and the
   README already concedes the brief is *"inference, not directly measured."*
3. **G10 — drop beats summarize for tool output.** The 50% advisory's central instruction, hook-driven,
   and the peer-reviewed anchor of the whole pruning argument.
4. **G8 — arrangement, not token count.** It sets the framing of every advisory (*"a prompt to act, not
   a degradation claim"*) and supplies the one concrete piece of new advice (cluster related context,
   prune scattered near-duplicates). If arrangement does not matter on the substrate, the tier copy is
   decoration.
5. **G9 — reads are ~70% of fill.** The premise that makes the 30% advisory point at anything specific.
   Not itself an action, but every pruning claim inherits it.
6. **G12 — mechanical pruning distorts decisions.** Draws the boundary that keeps G10's advice from
   being harmful; the `/conclude` and `/handoff` templates' Decisions / Ruled-out structure depends on
   it.
7. **G13 — no in-flight detector evidence.** Justifies a non-feature and the `/summary` command's
   framing. High value if wrong (a real signal would change the plugin's shape), low value if right.
8. **G3 — model/effort switch is a full re-read.** The single actionable cost tip the plugin repeats;
   high confidence, but it lives in prose the user reads, not in a mechanism.
9. **G1 — cache primitives.** Sets the baseline every action must beat and constrains the anchor's
   design (append, don't rewrite), but the plugin's cost case now rests on B7's break-even rule.
10. **G6 — reasoning compactors trade completeness for fabrication.** One advisory sentence in the skill;
    nothing acts on it.
11. **G4 — prefix replay is 59.5% of cost.** Motivating background; the report itself says it proves
    nothing about savings.
12. **G11 — task-aware pruning saves 23–38%.** Names a target the plugin has no mechanism to reach;
    listed in the README as unintegrated related work.
13. **G2 — compaction is not a cold reprocess.** Pure cost accounting; the PreCompact hook explicitly
    does no steering.
