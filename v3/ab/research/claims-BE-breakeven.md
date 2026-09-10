# Claims — BE (break-even: clear vs continue)

Extracted from the research the `context-governor` plugin was built on, for the purpose of designing an experiment that could confirm or refute it.

Sources:
- [2026-07-18-breakeven-research.md](/home/anatoly/context-governance-plugin/research/2026-07-18-breakeven-research.md) — findings B1-B7, the rule `R > 22.5·f/(1−f)`.
- [2026-07-17-breakeven-empirical.md](/home/anatoly/context-governance-plugin/research/2026-07-17-breakeven-empirical.md) — findings E1-E3, measured on 33 real Claude Code sessions.
- [2026-07-18-breakeven-source-claims-appendix.md](/home/anatoly/context-governance-plugin/research/2026-07-18-breakeven-source-claims-appendix.md) — per-source claims and 75 adversarial verdicts (consulted for exact numbers only).
- [README.md](/home/anatoly/context-governance-plugin/README.md) — "What it does" table and the "On cost" paragraph.

Notation used throughout: **P** = accumulated prefix tokens, **D** = new delta tokens per turn, **R** = remaining turns after the decision point, **f** = probability that dropped context gets re-read after a clear/compact.

Harness assumed for every feasibility line: headless `claude -p` sessions with Read/Write tools, sessions cuttable or allowed to auto-compact, plugin loaded or not, per-session cost reported by the CLI in tokens and notional API dollars (subscription account, so dollars are notional but the cache-read vs cache-creation vs uncached token split is real), three models, five runs per cell.

---

## B1 — Cache multipliers (re-verified against current primary docs)

**Claim.** Cache read is 0.10× base input; a 5-minute-TTL cache write is 1.25×; a 1-hour-TTL write is 2.0×; TTL refreshes free on every read; output is never cached; minimum cacheable block is 1,024 tokens on Opus 4.8 (appendix: 512 for Fable 5 / Mythos 5, 1,024 for Opus 4.8 / Sonnet 5, up to 4,096 for Opus 4.5 / Haiku 4.5). The 2026-03-06 change moved only the *default* TTL (1h→5m); the multipliers themselves did not change. Caching regime: this **is** the regime definition — every other finding is priced with these coefficients.

**Confidence.** CONFIRMED · high · 3-0. Primary-sourced (platform.claude.com prompt-caching); corroborated by third-party rates.json figures for sonnet-4-6 ($3.00 base / $0.30 read / $3.75 5m-write / $6.00 1h-write) and opus-4-6, which give identical multipliers. Not a scaffold.

**Plugin mechanism it motivates.** None — background. It underwrites one clause of the README's cost paragraph: *"a warm session is cheap (~0.1× base input per turn; prefix never re-written; TTL refreshes free)"*.

**Testable prediction if the plugin works.** Not a plugin test — an instrumentation-validation test that must pass before any other cell is interpretable. On task T (a fixed ~40K-token prefix and a scripted second prompt), with manipulation M (issue the second request inside the TTL vs after a sleep longer than the TTL), arm A (warm) will report `cache_read_input_tokens ≈ P` and `cache_creation_input_tokens ≈ D`, while arm B (cold) will report `cache_creation ≈ P`; the implied per-turn input price of A vs B will be ≈ 0.10 : 1.25, i.e. A about 12× cheaper on the same prefix. Refuted if the warm/cold per-turn input cost ratio is not within ~±20% of 1:12.5, or if the CLI's reported dollars imply a different read multiplier than 0.10×.

**Substrate and measure.** Per-turn `input_tokens` / `cache_read_input_tokens` / `cache_creation_input_tokens` / `output_tokens` from the session transcript JSONL, plus the CLI cost line. Deterministic accounting, no effect size published; 3 runs per model would settle it, and the standard 5 runs per cell is more than enough.

**Feasibility.** High — pure read-back of usage blocks from `claude -p` transcripts; needs no plugin; the only open question is whether the harness lets you select the 1-hour TTL at all (if not, the 1h multiplier stays a paper number).

**Caveats the report states.** Multipliers change over time — the report explicitly says to re-verify against live docs, citing the 2026-03-06 default-TTL move (1h→5m) as precedent. The minimum cacheable block varies by model, so a short early-session prefix is silently not cached at all and the break-even arithmetic simply does not apply below it. Output tokens are excluded from every model here.

---

## B2 — How a warm session bills

**Claim.** The cache breakpoint auto-moves to the last block on each request, so every turn re-reads the *entire* accumulated prefix at 0.10× and writes only the new delta (assistant reply plus next user turn) at the write rate — the prefix is never re-written; per-turn continue cost = `0.10·P + write·D`. If turns are spaced beyond the TTL the cache goes cold and the whole prefix is re-written at the write rate. Caching regime: caching on, either TTL; the cold branch is what happens when the TTL lapses.

**Confidence.** CONFIRMED · high · 3-0, from the same primary doc as B1. Not a scaffold.

**Plugin mechanism it motivates.** README, hook row: *"UserPromptSubmit hook | Re-anchors the goal at the end of every prompt (tiny, cache-safe), and injects a fill advisory when a tier (30/50/75% of budget) is newly crossed — once per tier, no nagging"* — "cache-safe" is exactly B2's mechanism (append at the end, never mutate the prefix). Also README notes: *"Advisories are additive context — a few hundred tokens per session at most (the monitor emits at most once per tier)."* And the cost paragraph: *"Clearest single win: don't switch `/model` or `/effort` mid-session (re-reads the whole history)."*

**Testable prediction if the plugin works.** On task T (a 60-turn scripted coding session with fixed prompts), with manipulation M (plugin loaded vs not), arm A (plugin) will exceed arm B (no plugin) on per-turn `cache_creation` by a small roughly-constant amount (the anchor plus at most three advisories, i.e. hundreds of tokens per turn, not thousands) while per-turn `cache_read` stays statistically indistinguishable between arms at equal turn index. Direction: A > B by a small constant on cache_creation; A ≈ B on cache_read. Refuted if any plugin-injected turn shows `cache_creation ≈ P` (prefix-sized) or a collapse in `cache_read` — that would mean the hook invalidates the cached prefix and the "cache-safe" description fails. Companion prediction: a deliberate mid-session `/model` switch produces `cache_creation ≈ P` on the switch turn in both arms.

**Substrate and measure.** Per-turn cache_creation and cache_read deltas, aligned by turn index across arms; total billed input tokens per session. n = 5 runs per cell × 3 models; the predicted effect is small (hundreds of tokens), so prompts must be scripted identically to keep variance down.

**Feasibility.** High — the plugin-on/plugin-off contrast is the harness's native manipulation, and the measure is already in the transcript.

**Caveats the report states.** The cold branch is not hypothetical: per the E2b correction, ~31% of real interactive turn-boundary pauses exceed 5 minutes and pay a full-prefix re-write, so "the prefix is never re-written" holds only inside the TTL. The report verifies the billing rule from Anthropic's doc; it does not verify where Claude Code itself places the breakpoint, so "the hook's injection lands after the cached prefix" is an inference this experiment would be testing, not a sourced fact.

---

## B3 — Real workload parameters (TraceLab)

**Claim.** Across ~4,300 sessions and ~350K steps, replayed prefix is the dominant serving cost (~60-62%; the earlier 59.5% and the current 61.7% are the same finding), with median per-step prefix ~126K tokens against a median append of ~857 — so carrying the prefix costs 0.10·126K ≈ 12.6K tokens/turn against 1.25·857 ≈ 1.07K for the new turn (~12×), yet still ~10× cheaper than re-fetching fresh. Session cost is heavy-tailed: mean $9.70, median $0.61, p99 $178 — calibrate to medians. Caching regime: caching on and largely warm.

**Confidence.** CONFIRMED · high · 3-0 (arXiv:2606.30560). Sourced, not synthesized — but note the same verification pass **refuted** the neighbouring TraceLab specifics: the 95.8% aggregate hit rate, the p90 998s human-wait, and the $5,189 idle cost all failed. Only the prefix-share and the per-step magnitudes survived.

**Plugin mechanism it motivates.** None — background. It supplies the parameter values (P ≈ 126K, D ≈ 857) that make B7's arithmetic land where it does, and independently corroborates E1.

**Testable prediction if the plugin works.** Substrate-calibration, not a plugin test. On task T (a file-heavy investigation run without the plugin to ≥100 turns), cache-read tokens will account for 50-75% of input cost, and the median per-turn append will be at least an order of magnitude smaller than the concurrent prefix. Refuted if the prefix share on long sessions falls below ~30%, or if append and prefix are within a factor of ~3 — either result means this harness does not reproduce the cost shape the plugin's claim was derived on, and every downstream cost cell is being run off-distribution.

**Substrate and measure.** Per-session cost decomposition computed from logged tokens: `read_share = 0.10·cache_read / (0.10·cache_read + 1.25·cache_creation + 1.0·input)`. Report **medians**, per the report's own instruction. n = 5 runs per cell × 3 models is the floor; the heavy tail (mean $9.70 vs median $0.61, p99 $178) means 5 runs cannot estimate a mean at all, only a median with wide uncertainty.

**Feasibility.** High — no plugin, no manipulation; it is a read of the same usage fields as B1.

**Caveats the report states.** The traces mix Claude Code and Codex and are not this harness. The distribution is heavy-tailed, so means are meaningless at small n. Seven neighbouring cost claims from this literature were killed in verification — the *mechanism* survived, the literature's *frequency numbers* did not, which is why the report leans on its own measurement instead.

---

## B4 — Anthropic's official guidance has NO numeric threshold

**Claim.** code.claude.com/costs says "clear between unrelated tasks; stale context wastes tokens on every subsequent message" and names un-cleared long sessions (plus Opus-as-default) as the top overspend driver, but gives no formula, multiplier, session length, or turn threshold. The report reads the task-boundary rule as a proxy for "dropped context has low re-read probability", i.e. low f. Caching regime: none assumed — the guidance is qualitative.

**Confidence.** CONFIRMED · high · 3-0, primary-sourced (the page itself). The *interpretation* ("task boundary = low f") is the report's own inference, not sourced.

**Plugin mechanism it motivates.** This is the gap the plugin's numeric layer fills. README: *"UserPromptSubmit hook | Re-anchors the goal at the end of every prompt (tiny, cache-safe), and injects a fill advisory when a tier (30/50/75% of budget) is newly crossed — once per tier, no nagging"*, with the tiers configurable (`"tiers": [0.30, 0.50, 0.75]`). Because B4 establishes there is no published threshold, the 30/50/75 tiers are a design choice rather than a sourced value — which makes them a direct experimental target.

**Testable prediction if the plugin works.** On task T (a long multi-stage task that will exceed the window if left alone), with manipulation M (plugin loaded vs not), arm A (plugin) will take its first governance action — handoff, clear, or manual compact — at a *lower* context fill and *earlier* turn index than arm B (model governing itself unaided), and arm B will reach involuntary auto-compaction more often than arm A. Measure X: fill % at first governance event; fraction of sessions that hit auto-compact before any deliberate action. Refuted if arm A's first governance event occurs at the same fill as arm B (the advisory changes nothing), or if advisories fire but no action follows within ~3 turns (the model ignores them).

**Substrate and measure.** Transcript token counts at each turn; the plugin's own advisory log (`.governor/`); the PreCompact marker as the auto-compact detector. n = 5 per cell × 3 models; no effect size is published anywhere, so this cell is powered only for large differences and should be reported as exploratory.

**Feasibility.** High — the cleanest plugin-on/plugin-off contrast available, and both the trigger and the response are visible in the transcript.

**Caveats the report states.** The report's own consolidated implication is *"Don't hardcode f or a turn threshold. No published value; ship the rule as guidance"* — so the tier numbers being unsourced is acknowledged in the research, not a discovery of this experiment. The "task boundary = low f" reading is inference.

---

## B5 — The only published break-even is caching-vs-uncached

**Claim.** Published break-evens all concern caching vs no caching: 5-minute caching wins on the 2nd request (1.25 + 0.10 = 1.35× < 2.0× uncached), with a per-write break-even of ~0.28 reads; the 1-hour tier needs ~2 reads (2.0 + 0.1 + 0.1 = 2.2× < 3.0×) and turns positive on the third request; a cache write that is never re-read is pure overhead — +25% at 5-min, +100% at 1-hour. Caching regime: both TTLs, explicitly contrasted with caching off.

**Confidence.** CONFIRMED · high · 3-0, and corroborated verbatim by the bundled claude-api reference. Sourced. But the report states plainly that this *"prices the reset write-spike but not the accumulated-context or re-read cost that drive the clear decision"* — i.e. it is the wrong break-even for the plugin's question.

**Plugin mechanism it motivates.** None — background. It prices only the one-time write spike that `/handoff` + `/clear` incurs, and supports the README's *"Prefer the **1-hour TTL** for gappy interactive work"* by making the 1h write premium concrete.

**Testable prediction if the plugin works.** On task T, with manipulation M (cut the session after a single request vs let it run ≥2 requests inside the TTL), the single-request arm will be strictly more expensive than its own uncached counterfactual (a write never re-read = +25% at 5-min), and the ≥2-request arm will be cheaper than its uncached counterfactual from the second request onward. Measure X: blended multiplier computed from logged tokens, `(1.25·cache_creation + 0.10·cache_read + 1.0·input) / (total_input_tokens)`, compared against 1.0. Refuted if the blended multiplier does not cross below 1.0 by the second request on a 5-min-TTL session, or if a never-re-read write is not ~25% overhead.

**Substrate and measure.** Counterfactual re-pricing of logged token splits — no uncached arm can actually be run, since prompt caching is not user-disableable in the harness. Deterministic given B1's multipliers; 3 models × 3 runs confirms the multipliers are identical across models (the appendix shows opus-4-6 and sonnet-4-6 give the same ratios).

**Feasibility.** Partial — the "uncached" arm is a computed counterfactual, not a runnable cell; the 1-hour arm requires TTL control the harness may not expose.

**Caveats the report states.** The report itself disclaims this as the wrong break-even for the clear decision. The appendix flags a third-party "1-hour break-even ≈ 12 reads" claim as arithmetically suspect (simple math gives ~3), so any secondary number in this family needs re-derivation before use.

---

## B6 — Caching-on floor

**Claim.** A workload needs roughly a 22% cache-hit rate on the 5-minute tier, or ~53% on the 1-hour tier, to beat paying full price; warm continuing sessions sit far above this, so the floor bites only when the cache is repeatedly cold — idle gaps, model or effort switches mid-session, post-upgrade resumes. Caching regime: both TTLs, as a threshold against caching off.

**Confidence.** CONFIRMED · **medium** · 3-0 — the only B-finding below "high". Sourced from a secondary analysis (the appendix's 22%/53% source), not from Anthropic docs. Not a scaffold, but weaker than B1-B5.

**Plugin mechanism it motivates.** README cost paragraph: *"Clearest single win: don't switch `/model` or `/effort` mid-session (re-reads the whole history)."*

**Testable prediction if the plugin works.** On task T (a 30-turn session with a large accumulated prefix), with manipulation M (a `/model` or `/effort` switch at turn 15 vs no switch), arm A (switch) will show `cache_creation ≈ P` at the switch turn and a whole-session cache-hit rate lower than arm B (no switch) by a margin that grows with P; total billed input tokens will be higher in A. With several switches, A's hit rate approaches or falls below the ~22% floor and A becomes more expensive than an uncached counterfactual. Measure X: session cache-hit rate = `cache_read / (cache_read + cache_creation + input)`, and total billed input. Refuted if a mid-session model switch does not re-write the prefix, or if session cost is materially unchanged by switching.

**Substrate and measure.** Session-level hit rate and total billed input; n = 5 per cell × 3 models. The predicted effect (a full-prefix re-write on a ≥100K prefix) is large, so 5 runs is adequate.

**Feasibility.** High, and unusually natural here — the harness already has three models, so the switch arm is a scripted resume under a different `--model`.

**Caveats the report states.** Graded medium, not high. The floor compares caching-on to caching-off, a regime the harness cannot run, so only the *mechanism* (cold event → full-prefix re-write) is directly observable; the floor crossing is counterfactual arithmetic. Cold events are frequent in real use (~31% of interactive turn-boundary pauses, per E2b) but back-to-back `claude -p` calls will show almost none unless sleeps are injected.

---

## B7 — BREAK-EVEN MODEL (the rule)

**Claim.** Continuing warm costs ≈ `0.10·P + 1.25·D` per turn and cold ≈ `1.25·P`; clearing drops P but pays a one-time rebuild — re-reading the still-needed fraction `f·P` at 1.0× plus re-caching it — so, treating P as roughly constant over R turns, clearing wins when `0.10·P·R·(1−f) > 2.25·f·P`, i.e. **R > 22.5·f/(1−f)**: f=0.1 → ~3 turns, f=0.3 → ~10, f=0.5 → ~22, f→1 → never. Caching regime: 5-minute-TTL warm continuation (1.25× write); the constant 22.5 = (1.0 re-read + 1.25 re-cache) / 0.10 comes straight out of B1's multipliers.

**Confidence.** **Low — the report flags it explicitly as a scaffold and a synthesis, "not directly published"**, and calls it *"a first-order sketch — directionally sound, threshold only as good as the measured f."* No source answers continue-vs-reset; the rule is assembled from verified primitives (B1, B2, B5) plus assumptions. It is the only B-finding that is not sourced.

**Plugin mechanism it motivates.** The plugin's entire cost justification. README cost paragraph: *"When to clear/compact reduces to one rule — clearing beats continuing when remaining turns **R > 22.5·f/(1−f)**, where **f = the chance dropped context gets re-read** (B7). So on a substantial session clearing is very likely token-cheaper, and the thing to protect is **brief quality, not tokens** (a good `/handoff` keeps f low — that's the plugin's cost justification)."* The mechanism itself is the `/handoff` row: *"Writes a ground-truth-verified handoff brief, then you `/clear`; the next session is offered the brief automatically | F5: models don't recover in-conversation — external consolidation does; F9: ~300 focused tokens beat ~113K of history"*, supported by `/goal`, `/log`, the PostToolUse fact capture, and `/conclude` + `/merge`.

**Testable prediction if the plugin works.** Two nested predictions — one for the rule, one for the plugin.

*The plugin prediction (the falsifiable claim about the product).* On task T (a two-stage task in a fixed repo where stage 2 provably depends on facts established in stage 1, run to a seam at P ≥ 150K), with manipulation M (how the reset is performed), arm A (`/handoff` brief written by the plugin, then `/clear`, then resume from the brief) will show **lower measured f** and lower post-reset re-read token volume than arm C (unaided "summarize what matters and continue in a fresh session", no plugin), and correspondingly lower total billed input from seam to task completion at equal completion quality. Direction: A < C on f, on re-read tokens, and on cost-to-completion. Refuted if f is the same in both arms — that would mean the brief apparatus is not the f-lowering machine the cost claim says it is — or if A's lower f is paid for with worse completion quality.

*The rule prediction (what an experiment must measure to confirm or refute `R > 22.5·f/(1−f)`).* Three quantities, all measurable on this harness:
- **f — the probability dropped context gets re-read.** Operationalize as: over the R turns after the reset, sum the tokens of tool results (Read / Grep / file dumps) whose content was already present in the pre-reset prefix, and divide by the pre-reset prefix P. Match by file path plus line range against the pre-reset transcript. The empirical half's cruder proxy also works: count discrete ~8K-token file re-reads. Report both; they should track.
- **R — remaining turns after the decision point.** Set it experimentally rather than observing it: fix R ∈ {3, 10, 22, 40} to bracket the thresholds the rule predicts for f = 0.1 / 0.3 / 0.5. (Two levels, R = 10 and R = 40, is the affordable version.)
- **Cost of clearing-with-a-brief vs continuing.** For each arm, total billed input from the decision point to task completion, priced from the real token split — `1.0·input + 0.10·cache_read + write_mult·cache_creation` — reported in tokens and in notional dollars, plus the one-time brief-writing cost (the `/handoff` turn itself: its output tokens and the tool calls it makes to ground-truth-verify) charged to the clearing arm.

*What confirms the rule.* For each (model, arm) cell, take the measured f̂ and the observed sign of `cost_continue − cost_clear` at each R. The rule is confirmed if the crossover R — the R at which clearing becomes cheaper — moves with f̂ in the predicted direction and lands within roughly a factor of 2 of `22.5·f̂/(1−f̂)`: cells with f̂ ≈ 0.1 should flip by R ≈ 3-6, cells with f̂ ≈ 0.5 should not flip until R ≈ 20-40, and cells with f̂ near 1 should never flip.

*What refutes it.* Any of: (a) the crossover R shows no monotonic relationship with f̂, i.e. f has no explanatory power; (b) clearing is cheaper even at high f̂, or never cheaper at low f̂, at R values the rule says it should have flipped; (c) the crossover is off by more than an order of magnitude in a consistent direction, indicating a missing term — most likely because P is not constant over R (context regrows, per B3's finding that context grows on 99.6% of steps) or because post-reset re-derivation turns cost far more than the re-read tokens they consume.

**Substrate and measure.** Transcripts plus a tool-call log for the f̂ matching. Measures: f̂; re-read token volume; billed input tokens and notional dollars from seam to completion; turns to completion; and a completion/correctness score, because a cheaper session that fails the task is not cheaper. No effect size is published anywhere in the report, so the floor is 5 runs per cell: 3 arms × 2 R-levels × 3 models × 5 = **90 sessions minimum** (180 if all four R-levels are run).

**Feasibility.** Medium — every manipulation is native (cut a session, load or unload the plugin, resume from a file, per-session cost from the CLI), but f̂ requires post-hoc matching of post-reset tool results against pre-reset content, and it is the one number the whole design turns on.

**Caveats the report states.** The report labels B7 low-confidence scaffold and lists three must-measure unknowns: *"(a) f itself; (b) the real idle-gap/cold-cache frequency; (c) whether microcompaction (preserves prefix) lowers effective f vs full compaction."* It notes prior attempts to find a published f were REFUTED. Its consolidated implication says *"Don't hardcode f or a turn threshold."* The model treats P as constant over R (B3 contradicts this), assumes re-reads land at full 1.0× price (they don't fully — a re-read enters the new prefix and is cached from the next turn), excludes output tokens, and open question 4 flags the whole quality dimension: *"does clearing/compacting cost quality (re-work, error rate)? A quality penalty shifts the threshold toward continuing."* The cold term is not negligible — the E2b correction below raises it to ~31% of real pauses.

---

## E1 — Prefix re-reads dominate cost, confirming TraceLab on real data

**Claim.** Cache-read tokens as a share of input cost: **interactive median 54%**, automated median 74% (TraceLab's independent figure was 59.5%), and the share climbs with session length — short sessions 17-30%, long ones 66-84%. Caching regime: caching on, with real inter-request gaps taken from transcript timestamps and the regime (off / 5m / 1h) modeled explicitly; output excluded as roughly equal across strategies.

**Confidence.** Not letter-graded in the report — it is the author's own measurement over 33 real sessions (n=16 interactive, n=17 automated) from one user, reproducible via `analyze_sessions.py`. Measured, not sourced from literature; independently corroborated by B3.

**Plugin mechanism it motivates.** None — background, but it is the premise the whole product rests on. The report states it directly: *"This is the mechanism that makes governance matter: most of the spend on a long session is replaying context, not generating output."*

**Testable prediction if the plugin works.** Substrate-calibration. On task T (run without the plugin), long-session cells (≥100 turns, ≥150K peak) will show cache-read share above 50%, and will exceed short-session cells (≤30 turns) by at least 20 percentage points. Direction: long > short on read-share; long > 50% absolutely. Refuted if long sessions in this harness sit below ~30% read-share, which would mean the harness does not reproduce the cost profile the plugin's cost claim was measured on — and every B7/E2 cell would then be testing the rule outside its domain.

**Substrate and measure.** Per-session cost decomposition from logged tokens; report medians across runs. n = 5 runs per cell × 3 models × 2 session-length cells.

**Feasibility.** High — no plugin, no manipulation, same usage fields as B1/B3.

**Caveats the report states.** Single user's workload. Output excluded. The interactive and automated regimes differ sharply (54% vs 74%), and the report explicitly says the automated regime — long agent loops that already auto-compact — is **not the plugin's target**. A headless `claude -p` harness may resemble the automated regime more than the interactive one it is meant to stand in for; that resemblance should be checked before the harness is used as a proxy for interactive work.

---

## E2 — The caching regime moves the break-even ~12×, but clearing a substantial session wins in all three

**Claim.** Modeling a disciplined handoff as a 100K prefix ceiling, the median break-even — how many ~8K-token file re-reads the saving covers before governance goes net-negative — is **838 re-reads with caching OFF, 128 at the 5-minute TTL, 70 at the 1-hour TTL** for interactive sessions (automated: 38,712 / 4,602 / 2,303). Since the report assumes a good handoff brief causes ~0-5 re-reads, clearing a substantial interactive session wins on tokens in every caching regime; the regime only changes how large the win is.

**Sub-finding E2b (folded here — this is where both self-corrections live).** An earlier draft reported "~4% of gaps over 5 minutes → 96% warm"; that number was **diluted by millisecond inner tool-steps** (a tool-heavy turn fires many sub-second requests, all trivially warm). Re-measured on turn-boundary waits only (>60s, i.e. real human pauses): **~31% of interactive turn-boundary pauses exceed 5 minutes and go cold** (automated 34%). That **reverses the earlier TTL claim**: because cold events are frequent and each re-writes the whole large prefix, the **1-hour TTL is cheaper in 12/15 interactive sessions — median 5-minute costs ~18% more** (automated 18/18, ~34% more), and it is free on a subscription.

**Confidence.** Not letter-graded — a counterfactual cost model computed over the same 33 real sessions, reproducible via `analyze_regimes.py`. Measured inputs (real per-request gaps, real token counts), **modeled** output (the 100K-ceiling counterfactual was never executed as an A/B). The "~0-5 re-reads with a good brief" figure that turns the model into a verdict is an **assumption, not a measurement** — it is the untested half of the claim.

**Plugin mechanism it motivates.** README cost paragraph: *"So on a substantial session clearing is very likely token-cheaper… Prefer the **1-hour TTL** for gappy interactive work (~31% of real pauses go cold under the 5-min default; 1h ran ~18% cheaper on measured sessions; free on subscription)."* Mechanism: the `/handoff` row — *"F9: ~300 focused tokens beat ~113K of history"*.

**Testable prediction if the plugin works.** Two.

*Break-even prediction.* On task T at a seam with P ≥ 150K, arm A (`/handoff` + `/clear` + resume from brief) vs arm B (continue in the same session), both run to task completion over R ≈ 20-40 turns: A's total billed input tokens from the seam onward will be lower than B's, and A's count of post-reset ~8K-scale file re-reads will be far below the regime's modeled break-even — predicted 0-5 observed against 128 (5-min) or 70 (1-hour). Refuted if the observed re-read count per reset approaches or exceeds ~70-128, or if A is not cheaper than B despite few re-reads.

*TTL prediction.* On task T, with manipulation M (inject sleeps at turn boundaries so that ~31% of pauses exceed 5 minutes, vs back-to-back turns with no pauses), arm A (1-hour TTL) will cost less total billed input than arm B (5-minute TTL) by roughly 18% median in the gappy condition, and the two will be within noise (or 5-min slightly cheaper) in the no-pause condition. Refuted if 1h is not cheaper under injected gaps, or if the gap does not actually produce cold events (detectable as `cache_creation ≈ P` on the post-pause turn).

**Substrate and measure.** Billed input tokens from seam to completion; count and token volume of post-reset re-reads; cold-event count (turns where cache_creation ≈ P); completion quality. n = 5 runs per cell × 3 models minimum. The break-even prediction has a predicted effect size that is enormous (0-5 vs 70-838, a 15-150× margin), so if it is real, 5 runs will show it unmistakably; the TTL prediction's ~18% median difference is far smaller and 5 runs per cell is thin for it.

**Feasibility.** High for the break-even prediction (seam cut, plugin on/off, resume from file, cost from the CLI). Partial for the TTL prediction: the caching-OFF regime cannot be run at all (counterfactual only), the 1-hour TTL arm requires TTL control the harness may not expose, and back-to-back `claude -p` calls have no natural think-breaks — the 31%-cold statistic does **not** transfer to a headless harness unless sleeps are injected deliberately.

**Caveats the report states.** Re-reads are modeled at a flat ~8K tokens each, priced at the regime's write rate. Output excluded. Single user's workload. Cold-turn cost approximated as a full-prefix re-write at the write multiplier. The ceiling model assumes a disciplined handoff actually holds the 100K cap — if it does not, the saving shrinks. Automated Sir Lunch loops are a separate regime the plugin does not target. And the report's own "what this does not settle": *"the reason to hesitate about clearing is **not** token cost — it is **redo cost and omission**"*, which the token model captures only crudely via the re-read proxy. Both E2b corrections above are the report correcting itself: the "96% warm" figure was an artifact of counting millisecond tool-steps, and the TTL recommendation flipped from 5-minute to 1-hour as a result.

---

## E3 — Below ~150K / ~100 turns, don't bother (in the cached regimes)

**Claim.** Short sessions show near-zero savings and low read-share (17-30%) — the prefix never grows large enough for re-reads to dominate under caching, so a reset saves almost nothing and mostly just costs the brief; governance earns its keep only once a session is genuinely long. **Exception:** with caching OFF the floor drops sharply, because even a modest session re-bills its whole prefix at full price every turn (a measured 31-turn / 129K session breaks even at 15 re-reads under OFF vs 7 under the 5-minute TTL) — so a user without prompt caching should govern earlier.

**Confidence.** Not letter-graded — derived from the same 33-session dataset and the same counterfactual ceiling model as E2. Measured inputs, modeled conclusion; single user.

**Plugin mechanism it motivates.** The applicability boundary for the whole cost claim, and the reference point for the shipped tier configuration: `"window_tokens": 200000, "tiers": [0.30, 0.50, 0.75]` — the first tier fires at 60K on a 200K window, below E3's ~150K floor. Also README: *"`model_windows` maps a substring of the transcript's model id to a window size (longest match wins) — so a 1M-context session is tiered against 1M, not the 200K fallback."*

**Testable prediction if the plugin works.** On two task sizes — T-short (completes in ≤30 turns / ≤60K) and T-long (≥100 turns / ≥150K) — with manipulation M (plugin loaded vs not), the direction of the cost difference will **reverse across task size**: on T-long, arm A (plugin) < arm B (no plugin) on total billed input tokens to completion; on T-short, arm A ≥ arm B, because the brief and reseed cost more than the shortened prefix saves. Measure X: total billed input tokens and notional dollars to completion, plus whether the plugin arm actually triggered a reset in the short cell (recorded from `.governor/` state and the transcript). Refuted if the plugin arm is cheaper on short sessions too (E3's floor is wrong), or if the sign does not reverse. Note the confound to record explicitly: if the short-cell plugin arm never resets — because the model declined the tier-1 advisory — then E3's floor was respected by the model's judgment rather than by the tier design, and the cell tests nothing about the floor.

**Substrate and measure.** Total billed input to completion; reset occurrence and turn index; completion quality. Cells: 2 task sizes × 2 plugin conditions × 3 models × 5 runs = **60 sessions**. No effect size published for the short cell (the report says "near-zero savings"), so a null there is expected and should be pre-registered as such rather than read as a failure.

**Feasibility.** High — both task sizes are scriptable and the manipulation is plugin-on/off; the caching-OFF exception is not runnable and stays counterfactual.

**Caveats the report states.** The OFF regime that drives the exception cannot be reproduced where caching is always on. Single-user derivation. The floor is stated in tokens only — it says nothing about whether a short session benefits from governance on quality grounds, and the report's own "does not settle" note points at redo cost and omission as the real risk that the token model does not capture.

---

## Findings ranked by how directly the plugin's cost claim depends on them

The plugin's cost claim is the README "On cost" paragraph: a warm session is cheap; clearing beats continuing when `R > 22.5·f/(1−f)`; the lever is brief quality, not tokens; prefer the 1-hour TTL; don't switch model mid-session.

1. **B7** — the rule *is* the cost claim. Every quantitative sentence in the README's cost paragraph is B7, and B7 is the single low-confidence, self-declared scaffold in the set. If the rule is wrong, the cost claim has no content.
2. **E2 (with E2b)** — supplies both remaining assertions: "clearing a substantial session is very likely token-cheaper" (the 70-838 break-even re-reads) and "prefer the 1-hour TTL, ~18% cheaper". Its weakest link is the unmeasured "~0-5 re-reads with a good brief" assumption, which is exactly the quantity the plugin claims to control.
3. **B2** — gives the per-turn cost form `0.10·P + write·D` that B7 accumulates, and separately underwrites the "cache-safe" hook design. If the prefix were re-written per turn, both the rule and the hook rationale change.
4. **B1** — sets the constant. 22.5 = (1.0 + 1.25)/0.10 comes directly from these multipliers; a pricing change moves the threshold linearly. Highest-confidence finding in the set, and the report already warns it is the most likely to age.
5. **E1** — the premise that makes any of this worth doing: most of a long session's spend is replaying context. If read-share were small, governance would have no cost case regardless of the rule.
6. **B3** — external corroboration of E1 plus the parameter magnitudes (P ≈ 126K, D ≈ 857) that make the ~12× ratio concrete. Supporting evidence rather than a term in the formula, and several of its neighbouring numbers were refuted.
7. **E3** — bounds where the cost claim applies (~150K / ~100 turns) rather than generating it. Wrong here means the plugin's advice is mistimed, not that the rule is wrong.
8. **B6** — yields the "don't switch `/model` mid-session" corollary and the cold-cache framing. Real but peripheral; the only medium-confidence B-finding.
9. **B5** — prices the reset write-spike only. The report states outright that it is not the break-even the clear decision needs; it constrains one term in B7's rebuild cost.
10. **B4** — establishes that no official numeric threshold exists. It motivates the plugin's existence and marks the 30/50/75 tiers as a design choice, but contributes no term to the cost math.
