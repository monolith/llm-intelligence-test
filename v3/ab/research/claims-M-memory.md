# Claims M1–M11 — the continuity system's evidence base, turned into testable predictions

Source: [`2026-07-18-memory-efficacy-research.md`](/home/anatoly/context-governance-plugin/research/2026-07-18-memory-efficacy-research.md)
(findings M1–M11; deep-research run `wf_f5967a7a-543`, 2026-07-18, 5 angles, 106 agents, ~4.8M tokens),
with exact numbers and sources cross-checked against
[`2026-07-18-memory-source-claims-appendix.md`](/home/anatoly/context-governance-plugin/research/2026-07-18-memory-source-claims-appendix.md).
Plugin quotes are from [`README.md`](/home/anatoly/context-governance-plugin/README.md) ("What it does" table and the honest-evidence-grade paragraph).

Each finding below carries: the claim (with the task domain and model era of the evidence), the grade as
the report gave it, the plugin mechanism it motivates, a falsifiable prediction on this harness, the
substrate and measure, one line on feasibility, and the caveats the report itself states.

**11 of 11 findings are mapped to a testable prediction.**

## Sizing note (used by every "minimum n" below)

Run-to-run spread on the v3 noisy 100-point sheet, measured from the existing r1/r2/r3 runs (mean of the two
judges per run): haiku 53.5 / 50.5 / 47.5 (SD ≈ 3.0), sonnet 63 / 63 / 63.5 (SD ≈ 0.3), opus 72 / 72.5 / 82
(SD ≈ 5.7), fable 80.5 / 84 / 81 (SD ≈ 1.9). Working figure: **SD of the paired difference ≈ 5 points**.
For a paired t-test at 80% power, α = 0.05: **n ≈ 8·(SD/Δ)² pairs**. So Δ = 10 → n ≈ 2; Δ = 5 → n ≈ 8;
Δ = 3 → n ≈ 22; Δ = 2 → n ≈ 50. The planned design (3 models × 5 repeats = 15 pairs) detects Δ ≈ 4 points
pooled, or Δ ≈ 6–7 points within a single model's cell. Judge disagreement in v3 averaged about 2 points;
treat that as the floor of what any measure can resolve.

---

## M1 — Cross-session degradation is real and large

**Claim.** Forcing recall across sustained multi-session interaction, rather than reading the material
in-context, drops accuracy ~30% on average and up to 64% per system: GPT-4o −30.3%, Llama-3.1-70B −55.1%,
Phi-3-128k −45.9%, ChatGPT+GPT-4o −37%, Coze+GPT-4o −64% (LongMemEval, Wu et al., ICLR 2025, peer-reviewed;
500 curated questions over ~115K-token multi-session chat histories). **Domain:** conversational-assistant QA,
not coding. **Model era:** GPT-4o / Llama-3.1-70B / Phi-3-128k, i.e. 2024–2025 frontier.

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** The continuity system as a whole — the README frames the plugin as a
response to the fact that "long sessions degrade the model gradually and invisibly", and cites for `/handoff`:
"F5: models don't recover in-conversation — external consolidation does; F9: ~300 focused tokens beat ~113K
of history".

**Testable prediction if the plugin works.** On task T (the v3 noisy condition: 24 retellings interleaved with
24 unrelated documents, reader replaced twice, third reader answers the 100-point sheet), with manipulation M
= how much unrelated material sits between the scored retellings (the existing high-distractor order vs a
low-distractor order), arm A (plugin: session answering from a small carried artifact — goal anchor, ledger,
facts log) will score **higher** (direction D) than arm B (baseline: no plugin, nothing crosses the seam) on
measure X = 100-point answer-key total; **and** the paired A−B difference will be **larger** in the
high-distractor condition than in the low-distractor one (arm × distractor-load interaction). If distractor
load does not modulate the arm difference at all, M1's mechanism is not what is operating here.

**Substrate and measure.** v3 noisy corpus + `v3/answer-key`, two independent opus judges, key total.
Source effect ~30pp; if a tenth of it survives the domain transfer (Δ ≈ 3 points) the design needs ≈ 22 pairs;
the 15-pair design resolves Δ ≈ 4. Minimum n for the interaction test: 15 pairs per distractor level.

**Feasibility on a headless harness.** Direct — `ab_run.py --seam none` already runs the A/B; the second
distractor level is a variant of `v3/distractors/ORDER.md`, no code change.

**Caveats the report states.** "Compares bloated-full-history-in-context vs focused-in-context (both hold the
info) — measures long-context distraction + value of focused retrieval, **not cold-vs-seeded**." Plus the
report's biggest caveat, which applies to nearly every finding here: the evidence is conversational-assistant
QA, not coding agents, "the plugin's real setting"; and the biggest deltas are "partly has-info-vs-none".

---

## M2 — Memory beats no-memory by large margins

**Claim.** PlugMem scores 75.1 vs No-Context 14.8 on LongMemEval (+60.3); HotpotQA 22.1 → 61.4 EM (31.0 → 74.1
F1). A related result in the same paper: a 362-token distilled memory beat the 107K-token raw full dump
(75.1 vs 62.4, ~295× fewer tokens). **Domain:** multi-session conversational QA, multi-hop QA, WebArena
web-agent tasks — not coding. **Model era:** 2026 (PlugMem, arXiv 2603.03296, ICML 2026).

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** The ledger. README: "`/goal [text]` — Sets the session goal — a
**continuity ledger** (`.governor/ledger.md`) that the hook re-shows at the end of every prompt so a long
session can't drift off it".

**Testable prediction if the plugin works.** On task T (v3 noisy, two seams), with manipulation M = whether the
ledger's accumulated content survives the seam, arm A (plugin as shipped: goal + ledger + facts cross the cut)
will score **higher** (D) than arm B (plugin loaded, all hooks firing, but `.governor/ledger.md` truncated to
its goal line immediately before each cut) on X = key total. This arm pair isolates the **store** from the
hooks; a null says the plugin's benefit, if any, comes from its prompting, not from what it wrote down.
Secondary: A carries fewer tokens across the seam than an arm that pastes the raw prior transcript, at equal
or better score.

**Substrate and measure.** Same corpus and key; adds a third arm ("plugin, ledger-ablated"). Source effect
+60.3 on a 0–100 scale; if a quarter survives (Δ ≈ 15 points) n ≈ 2 pairs, so 5 reps per cell is ample —
this is the best-powered contrast in the set.

**Feasibility on a headless harness.** Yes — a harness step truncating `.governor/ledger.md` between segments;
plugin dir, model, prompts and material otherwise identical.

**Caveats the report states.** "Partly has-info-vs-none; margin over *rival memory* systems is small (75.1 vs
73.0). Backs 'some ledger beats no ledger'; does not prove this design beats alternatives." A win over an
ablated arm therefore supports the weak form of the claim only.

---

## M3 — Distilled auto-extracted facts raise accuracy

**Claim.** Fact-augmented memory-key expansion (keys = memory value + extracted facts) improves retrieval and
end-task accuracy: **+9.4% recall@k and +5.4% final accuracy**, "across all models" = GPT-4o, Llama-3.1-70B,
Llama-3.1-8B (LongMemEval §5.3 / Table 3, measured against the unaugmented K=V baseline). **Domain:**
conversational-assistant QA. **Model era:** GPT-4o / Llama-3.1, 2024–2025. The report calls this "the single
most direct evidence for the auto-captured-facts feature".

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** Auto-facts. README, PostToolUse hook: "Auto-captures the factual arc (files
touched, tests, commands) to `.governor/session-facts.log` every tool call — the record never depends on
remembering to log. The model distils these into the ledger at seams", with the rationale "Capture must be
automatic: people forget; the factual half needs no judgment".

**Testable prediction if the plugin works.** On task T (v3 noisy), with manipulation M = the PostToolUse
capture hook present or removed from the plugin copy passed to `--plugin-dir`, arm A (capture on) will score
**higher** (D) than arm B (capture off, goal anchor and ledger unchanged) on X = the **specific-detail subset**
of the answer key (items naming concrete entities: names, counts, objects, order of events), by ≥ 5 points;
the gist subset is predicted to move less. Secondary measure matching the source's recall@k: the share of key
items whose supporting detail appears anywhere in the carried artifacts (`ledger.md` + `session-facts.log` +
brief), scored by a script against the key — predicted higher in A.

**Substrate and measure.** Answer key split into specific-detail and gist subsets before running. Source
Δ = +5.4% accuracy ≈ 5 points on the 100-point sheet → **n ≈ 8 pairs minimum**; 3 models × 5 reps = 15 is
sufficient. Recall@k analogue needs no judge.

**Feasibility on a headless harness.** Yes — two copies of the plugin directory differing only in the hook
block; `claude -p --plugin-dir <copy>` selects the arm.

**Caveats the report states.** "Measured in conversational-assistant QA, not coding (domain transfer);
retrieval-key augmentation, not 're-inject every prompt'." And from the deliverable table: auto-facts are
BACKED "with caveats… self-generated memory can lock in wrong beliefs (M10) — which is why the human-review
layer is load-bearing".

---

## M4 — Distilled memory ≈ full-context quality at 3–4× fewer tokens

**Claim.** Mem0 reports 92.5 on LoCoMo and 94.4 on LongMemEval under ~7K tokens per query, versus 25K+ for
full-context — framed as **parity at 3–4× lower token cost, not an accuracy gain**. A separate Mem0 page puts
full-context *above* distilled memory on raw accuracy (72.9% vs 66.9% on LoCoMo). **Domain:** multi-session
conversational dialogue benchmarks. **Model era:** 2026 vendor benchmarks.

**Confidence.** CONFIRMED (cost-parity only) · medium · 2-1. The report labels it "vendor-self-reported,
generous LLM judge, contested benchmark".

**Plugin mechanism it motivates.** The economics of handing off rather than continuing. README `/handoff`:
"F9: ~300 focused tokens beat ~113K of history"; and the cost paragraph: "clearing beats continuing when
remaining turns **R > 22.5·f/(1−f)**… the thing to protect is **brief quality, not tokens**".

**Testable prediction if the plugin works.** This one is an **equivalence** prediction, not a superiority one.
On task T (v3 noisy, hinted seam), with manipulation M = distilled brief vs exhaustive retention notes, arm A
(plugin `/handoff` brief) will be **statistically equivalent** to arm B (baseline exhaustive notes) on X = key
total within a pre-declared margin of ±5 points (TOST), **while** carrying ≥3× fewer tokens across the seam
(handover word counts already recorded) and costing no more in total run tokens/dollars. Falsified if A costs
more tokens than B for equal or worse score, or if A falls outside the margin on the low side.

**Substrate and measure.** `provenance.json` token, turn and API-equivalent dollar totals, plus handover word
counts, which the harness already collects; key total for the equivalence leg. At SD_diff ≈ 5, 15 pairs
establish equivalence within about ±4 points — so the ±5 margin is reachable; a tighter margin is not.

**Feasibility on a headless harness.** Yes — the hinted (`AB_SEAM=hinted`) design is exactly this arm pair,
and the cost columns are already in `REPORT.md`.

**Caveats the report states.** Graded medium, 2-1, "a cost-parity signal, not an accuracy win"; adjacent to the
already-verified F9 rather than independent. The appendix adds that the cited Mem0 page discloses no
no-memory/full-context baseline and does not name its scoring metric.

---

## M5 — "Just add memory" is model-dependent; explicit task-state is more robust

**Claim.** Generic memory systems are near-useless on a weak model and competitive on a strong one:
Letta/MemGPT 0/36 (0%) and LangGraph+Memory 2/36 (5.6%) at gpt-4.1-mini, but both 72.2% at gpt-5.4; an
explicit task-state controller (StateQGP) stays flat at 69.4–77.8% across gpt-4.1-mini, gpt-4.1 and gpt-5.4.
**Domain:** QGP-RepoScan long-horizon tool-calling tasks — the closest thing in this corpus to an agentic
coding setting. **Model era:** gpt-4.1-mini / gpt-4.1 / gpt-5.4 (arXiv 2605.23574, May 2026 preprint).

**Confidence.** CONFIRMED · medium · 3-0. "Single preprint, one task family."

**Plugin mechanism it motivates.** The ledger's *shape*. README `/log`: "Records durable state to the ledger as
you go, so the handoff is mostly pre-written; ruled-out lines ride in the anchor" — the Goal / Decisions /
Ruled-out structure the report identifies as the better-supported design.

**Testable prediction if the plugin works.** Two predictions.
(a) *Model dependence.* On task T (v3 noisy), with manipulation M = model tier (haiku / sonnet / opus), the
paired plugin−baseline difference will be **largest on the weakest model and shrink toward zero on the
strongest** (D = negative slope of the arm effect against model strength). A flat or reversed slope contradicts
M5's transfer.
(b) *Structure.* With manipulation M = ledger template, arm A (structured task-state: Goal / Decisions /
Ruled-out headings, as shipped) will score **higher** (D) than arm B (a plugin copy whose ledger template is
free-form prose of equal token budget) on X = key total.

**Substrate and measure.** (a) needs no new arm — the three-model design already gives it, 5 reps per model.
(b) needs a prose-template plugin copy. No effect size is given for structure-vs-prose (the source contrasts
structure against *generic memory*, not against prose), so size for the smallest difference worth acting on,
Δ = 5 → **n ≈ 8 pairs**.

**Feasibility on a headless harness.** Yes — model is already a factor in the lane script; the prose variant is
a template edit inside a copied plugin directory.

**Caveats the report states.** Single unrefereed preprint, one task family. The appendix adds a bound the
report's summary compresses: StateQGP's gains came from **active state exposure plus enforcement** (blocking
unsupported final actions, filtering duplicates, routing back to pending work), and the paper "does not isolate
the effect of a passive goal re-statement" — so it validates an enforced ledger, not a re-printed goal line;
it also requires an online verifier and still degrades at the longest horizons.

---

## M6 — Self-written reflections re-read as memory improve results

**Claim.** Reflexion (Shinn et al., NeurIPS 2023): ALFWorld 130/134 solved ≈ 97%, an absolute +22pp over ReAct;
HotPotQA 61% → 75%; HumanEval 91% pass@1 vs GPT-4's 80%. **Domain:** ALFWorld (game), multi-hop QA, HumanEval
(coding — the one coding result in the cluster). **Model era:** GPT-3.5 / GPT-4, 2023. The report calls it "the
closest ledger analogue".

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** `/log` writing durable state plus `/summary` re-reading it. README
`/summary`: "Shows both what would be handed over (the ledger) and what the session is thinking right now —
your window to catch drift".

**Testable prediction if the plugin works.** On task T = a retry-structured coding task family (20 bug-fix
tasks with hidden tests, each attempted up to 3 times in separate sessions), with manipulation M = whether the
failed attempt's ledger entry survives to the next attempt, arm A (plugin: ledger carried) will need **fewer
attempts to pass** (D) than arm B (plugin loaded, ledger cleared between attempts) on X = pass@2 rate and mean
attempts-to-success. Bound-check sub-prediction, straight from the report: in a sub-condition where the
verification signal is unreliable (a test suite seeded with a known false positive), A will **not** beat B and
may fall below it.

**Substrate and measure.** A second substrate, not the retelling corpus: bug-fix tasks scored by hidden tests
run by the harness outside the session. Source Δ = +22pp on success; if a third survives (Δ ≈ 7pp) n ≈ 4–5
runs per cell; keep 5.

**Feasibility on a headless harness.** Yes, with one addition: `claude -p` with Read/Write edits the repo, the
harness runs the hidden tests after the session exits and scores pass/fail — no judge needed, no extra tools
inside the session.

**Caveats the report states.** "Within-task / across-trials, reset per task — a partial analogue of a durable
ledger, **not cross-session**; gains need a verification signal (MBPP fell *below* baseline on false-positive
self-tests — a stale-memory warning)." One of the four refuted items is precisely the ablation that would have
isolated the memory store's own contribution from the quality of what was written into it.

---

## M7 — Externalizing working state helps multi-step and longer-than-trained tasks

**Claim.** Scratchpad (Nye et al. 2021): polynomial evaluation 8.8% → 20.1% few-shot (31.8% → 50.7%
fine-tuned); synthetic Python execution 11% → 26.5% few-shot (20% → 41.5% fine-tuned); MBPP 5.1% → 17.3%
(≈3.4×). Self-Notes (NeurIPS 2023): out-of-distribution-length 24.4% → 85.0%. **Domain:** synthetic program
execution, arithmetic, MBPP, synthetic reasoning. **Model era:** pre-GPT-4 fine-tuned LMs, 2021–2023.

**Confidence.** CONFIRMED · high · 3-0.

**Plugin mechanism it motivates.** Writing state down as you go — the ledger plus automatic capture. README,
PostToolUse: "the record never depends on remembering to log"; `/log`: "Records durable state to the ledger as
you go, so the handoff is mostly pre-written".

**Testable prediction if the plugin works.** On task T = the Option B long read-once condition (the 1.5M-token
corpus read by a chain of 20+ sessions, each handing over at a seam), with manipulation M = plugin loaded or
not, arm A (plugin, state written continuously) will show a **shallower decline** (D) than arm B (baseline)
on X = per-question-batch score plotted against chain position — i.e. the arm difference grows with chain
depth. Falsified if the two decay curves are parallel.

**Substrate and measure.** Option B, sonnet and opus, per-batch scores from the three question batches.
Currently 1 run per cell (direction only); testing a **slope** difference needs at least 3 runs per arm per
model, better 5 — the source effect sizes (roughly 2–3.5× on absolute accuracy) do not translate to a slope,
so this is sized by design, not by the source.

**Feasibility on a headless harness.** Mechanically supported — the harness already defines Option B; the
constraint is run cost, not machinery.

**Caveats the report states.** "**Critical bound:** in-context write-then-reason within one task, not
cross-session persistent memory. Foundational support, adjacent to the ledger." The Self-Notes-beats-CoT margin
is one of the four refuted items; the appendix also records a low-data regime where the no-scratchpad model
beat the scratchpad model (10% vs 5%).

---

## M8 — Goals live in context, not hidden state; but re-injection alone isn't sufficient

**Claim.** Plan signal decays ~4.1× in a single action-observation step (0.453 → 0.110, Llama-3.1-70B on
ALFWorld; 12.4× on HotpotQA; ~0.027 by step+5). Dropping the plan is costly: naive eviction cut ALFWorld
success 56.7% → 22.0% (−34.7pp, p<0.001; 30 tasks × 5 runs = 150 runs). **But** re-injection alone did not
recover it: probe-gated re-surfacing re-injected the plan ~6.1×/run for +2.7pp (95% CI [−6.7, +12.0], p=0.67),
and static plan-protection was −1.3pp (p=0.89). **Domain:** ALFWorld game + HotpotQA. **Model era:**
Llama-3.1-70B (arXiv 2606.22953, June 2026 preprint, ~1 month old at report time).

**Confidence.** CONFIRMED · medium · 3-0.

**Plugin mechanism it motivates.** The goal anchor. README, UserPromptSubmit hook: "Re-anchors the goal at the
end of every prompt (tiny, cache-safe), and injects a fill advisory when a tier (30/50/75% of budget) is newly
crossed — once per tier, no nagging".

**Testable prediction if the plugin works.** On task T (v3 noisy), with manipulation M = compression pressure
(normal run vs a run whose budget forces a compaction before the questions), arm A (plugin with the
end-of-prompt anchor live) versus arm B (identical plugin copy with the anchor re-injection removed from the
UserPromptSubmit hook):
- Under **no compression**: A > B (D positive) on X = key total **and** on the on-goal share (fraction of scored
  answers drawn from the retellings rather than the distractor documents, from the judges' per-item marks).
- Under **forced compaction**: the report's own bound predicts A − B ≈ 0 (within ±3 points). A large positive
  effect here would contradict the source; a null is the predicted result, not a failure of the test.
This pair is what separates "the anchor does something" from "the anchor is sufficient".

**Substrate and measure.** Key total plus the on-goal share; the PreCompact marker records that compaction
happened. Source's own re-injection effect (+2.7pp) was non-significant at n = 150 runs — detecting a
2–3-point effect here would need ≈ 50–70 pairs, far beyond the planned 15, so the anchor-alone arm is powered
only for Δ ≥ 4 points. State that limit before running.

**Feasibility on a headless harness.** Yes — the anchor-off arm is a plugin copy with the hook's re-injection
block removed; the compression condition is induced by shrinking the run's effective budget so the session
compacts mid-chain.

**Caveats the report states.** Hard boundary #1: "The anchor is necessary, not sufficient… The plugin needs a
real prune/evict policy, not just an end-of-prompt anchor." Single ~1-month-old preprint. The appendix adds
that the paper's contribution is representational — it "does NOT demonstrate a statistically significant
task-success gain from any plan-memory/re-injection intervention", an absence-of-evidence finding for exactly
the claim the anchor makes.

---

## M9 — End-of-prompt placement is the high-recall zone

**Claim.** Recall is U-shaped across the window (Lost-in-the-Middle, ~20-point mid-context penalty, replicated
across six model families). Instructions placed only at the start of a long input get forgotten: BAMBOO
MeetingQA on ChatGPT-16k falls 45.0% (4K) → 20.5% (16K) under instruction-first. Placing the instruction
*after* the input gives up to **+9.7 BLEU** on WMT zero-shot translation across 1B/7B/13B scales. Anthropic
recommends end-placement explicitly ("putting the instructions at the end of the prompt, as we want Claude's
recall of them to be as high as possible"), reporting up to ~30% quality improvement on 75–90K-token document
inputs. **Domain:** long-document QA, translation and summarization — single-query, not multi-turn agent runs.
**Model era:** GPT-3.5-16k / Claude 2 / Vicuna / LongChat era, plus Anthropic's long-context guidance.

**Confidence.** CONFIRMED · high · 3-0 — the report calls this "the most durable finding", peer-reviewed and
heavily replicated.

**Plugin mechanism it motivates.** The anchor's *placement*. README, `/goal` row: "the hook re-shows [the
ledger] at the end of every prompt" — evidence column: "F4: the end of the window is the best-attended
position; keep it tiny (F10)".

**Testable prediction if the plugin works.** On task T (v3 noisy), with manipulation M = where the goal text
sits, arm A (goal re-shown at the end of every prompt, as shipped) will score **higher** (D) than arm B (the
same goal text, same token count, injected once at session start and never again) on X = key total and on-goal
share; and the gap will **widen with session length** (compare the score contribution of items from segment 1
vs segment 3). Falsified if B ≥ A at equal tokens — which would say placement is not what the anchor is buying.
A third arm (goal re-shown at the *start* of every prompt) separates "re-injection" from "end-placement".

**Substrate and measure.** Key total, plus per-segment item scores from the judges' marks. Source effects span
+9.7 BLEU to ~30% quality; if a fifth survives (Δ ≈ 5–6 points) **n ≈ 6–8 pairs**, so 15 pairs is comfortable.

**Feasibility on a headless harness.** Yes — start-only and start-of-every-prompt variants are one-line changes
in copied plugin hook scripts; everything else identical.

**Caveats the report states.** "Tests retrieval/generation position, not goal-re-injection specifically." The
appendix adds two bounds: BAMBOO's authors find position is **not** the dominant driver of long-text failure
(fixing evidence location yields only minor improvement; they attribute poor performance mainly to
reasoning/coding ability), and one adversarial verdict rejects equating high attention weight with effective
utilization. The attention-decay "instruction-forgetting" mechanism for one source is among the four refuted
items (the BAMBOO version of the effect survived).

---

## M10 — RISK: self-generated memory can lock in wrong beliefs

**Claim.** Reflexion-style agents stored confident-but-wrong interpretations and kept acting on them across
resets: in 16 "frozen" ALFWorld environments, **0 of 121 stored reflections named the correct target object**,
plus 4 analogous HumanEval cases; an ablation isolated **2 of 16 as strictly memory-harmful** (removing memory
helped). Replacing open-ended self-diagnosis with programmatic extraction of failure signals raised
correct-object mention **0% → 86%**, cut the reflection-repetition rate 0.64 → 0.10, and solved 3 of the 16
frozen environments. **Domain:** ALFWorld + HumanEval. **Model era:** arXiv 2605.29463 ("Honest Lying", Dixit
et al.), May 2026, ICML 2026 workshop tier.

**Confidence.** CONFIRMED · medium · 3-0.

**Plugin mechanism it motivates.** The human-review layer over auto-facts. README honest grade: "auto-captured
facts are backed but carry a self-generation lock-in risk (so the human-review layer matters)"; `/summary`:
"Shows both what would be handed over (the ledger) and what the session is thinking right now — **your window
to catch drift**".

**Testable prediction if the plugin works — and the test that detects lock-in harm.** Seed the corpus with
**knowledge-update items**: a fact stated in an early retelling and *corrected* in a later one, with the answer
key scoring only the corrected value. (LongMemEval scores exactly this ability, so the item type is standard.)
On task T (v3 noisy plus seeded update items), with manipulation M = what the plugin carries and whether it is
reviewed, run three arms:
- **A** — plugin as shipped: auto-facts + ledger cross both seams, no human review.
- **B** — baseline: no plugin, nothing crosses.
- **C** — plugin plus a scripted correction step at each seam standing in for `/summary` review: any ledger or
  facts line contradicting the latest material is struck before the next session starts.

Predictions if the plugin works: A ≥ B on the **overall** key total **and** A ≥ B on the **corrected-fact
subset**.
**Lock-in harm is detected** when A ≥ B overall but **A < B on the corrected-fact subset** (direction D
negative on that subset) — the plugin carrying a stale early belief past its correction, at the cost of the
items where the correction matters. Second, sharper measure, no judge needed: **source-attributable error
rate** — for every wrong answer in arm A, check whether the identical wrong value appears verbatim in that
run's `.governor/ledger.md` or `.governor/session-facts.log`. If the plugin's own written memory predicts the
final wrong answers at a rate above arm B's error rate on the same items, that is the lock-in mechanism caught
in the act. Third, **C − A** quantifies how much harm the review layer removes — the analogue of the source's
0% → 86% mitigation; if C ≈ A, the review layer is not doing the work the report assigns to it.

**Substrate and measure.** Seed the corrected-fact items into the retellings and the key. The source effect is
a **prevalence** (2/16 environments strictly harmful ≈ 12.5%), so size on items, not runs: detecting a 12.5%
harmful rate against a null of zero at 80% power needs roughly **30 seeded update items** across the run set
(≈10 per repeat across three models). The verbatim-persistence check is a script, so it costs nothing extra.

**Feasibility on a headless harness.** Yes — corpus and key edits, plus a grep of each run's `.governor/` files
against the key's list of superseded values; arm C is a harness step between segments, not a session action.

**Caveats the report states.** Hard boundary #2: "Self-generated memory can poison… Maps strongest to
auto-captured facts (self-generated → highest lock-in risk); weakest to a human-curated ledger. This is the
evidence that the review/correct layer is not optional." Single workshop-tier preprint on two task families;
and the report's open question 3: for a human-curated ledger, "how much does the false-belief risk actually
apply? Untested; human editing may blunt it." The appendix records two adjacent risks that ride the same
channel: memory-injection persists across session boundaries (>95% injection success, MINJA), and badly
structured memory can push an agent **below** its no-memory baseline (AWM 26.3/28.2 SR vs no-memory 42.1/43.6
on WebArena Shopping; a random-retrieval ablation collapsed HotpotQA to 20.0 EM, below the 22.1 no-context
baseline).

---

## M11 — ABSENCE: cold-vs-seeded handoff is unmeasured

**Claim.** No study in the corpus measures a cold fresh session against one seeded by a distilled brief (or
against continuing bloated). The closest are bloated-vs-focused in-context (M1) and memory-vs-none QA (M2),
neither of which isolates fresh-session seeding, and **no source measures CLAUDE.md-style coding-agent repo
memory**. **Domain:** not applicable — this is an absence over the whole 2026 corpus. The report's verdict:
"The handoff brief is evidence-motivated, not backed — the highest-value target for a dedicated eval," and
"the one feature needing a real A/B experiment".

**Confidence.** CONFIRMED (absence) · high.

**Plugin mechanism it motivates.** The handoff brief and its pickup. README `/handoff`: "Writes a
ground-truth-verified handoff brief, then you `/clear`; the next session is offered the brief automatically";
SessionStart hook: "Offers the newest unconsumed handoff brief (<48h)". README honest grade: "the
handoff-brief seeding is inference, not directly measured — the one feature still awaiting a real experiment."

**Testable prediction if the plugin works — the experiment, spelled out.**
*Task T:* the v3 noisy condition — 24 retellings interleaved with 24 unrelated documents in the fixed order,
the reader replaced after retelling 8 and again after 16, the third reader answering the 100-point sheet in
three files. Fixed across all arms: model, material and order, prompts, Read+Write only, no user settings, no
CLAUDE.md, two independent opus judges.
*Manipulation M — what crosses each seam, four levels:*
- **A (seeded).** Plugin loaded; at each seam the outgoing session runs `/<plugin>:handoff`; the incoming fresh
  session is offered the brief by the SessionStart hook and reads it.
- **B (cold).** No plugin; the incoming session starts fresh and is told only that earlier sessions read
  material that is now gone. Nothing crosses.
- **C (bloated).** No seam at all: one session reads all 48 documents and answers with the whole history in
  context — the "continue bloated" leg the report names.
- **D (notes control).** No plugin; the outgoing session writes exhaustive retention notes and the incoming
  session reads them — isolates "a distilled brief" from "any written handover".
*Measure X:* 100-point answer-key total (two judges), plus carried-artifact tokens and total run cost.
*Predictions if the plugin works, pre-registered before running:*
- **A > B** — seeding beats cold. This is the primary contrast and the one the corpus has never run; direction
  D positive; falsified if A ≤ B.
- **A ≥ C** on score while carrying far fewer tokens — the parity leg that M4 predicts.
- **A ≥ D** within an equivalence margin of ±5 points, at fewer carried tokens — the brief-vs-exhaustive-notes
  contrast. Falsified if A < D by more than the margin at equal or greater cost.
*Pairing unit:* (model, repeat).

**Substrate and measure.** 4 arms × 3 models × 5 repeats = 60 runs, 120 gradings, on the v3 noisy corpus and
key. **No effect size exists for A vs B — that absence is the finding** — so size for the smallest difference
worth acting on: Δ = 5 points → **n ≈ 8 pairs minimum**; pooled across three models, 15 pairs resolve Δ ≈ 4.
Arm C is one long single-session variant per model per repeat.

**Feasibility on a headless harness.** Directly supported — `ab_run.py --seam hinted` already runs A and D and
`--seam none` runs the unassisted variant; C needs a seam-free segment file; costs are recorded per run in
`provenance.json`.

**Caveats the report states.** The brief is an inference from M1 + M2, not a measurement; nothing in the corpus
measures CLAUDE.md-style repo memory; and the domain gap applies in full — the corpus is conversational QA and
synthetic/game tasks, not coding agents. Two appendix items bound the prediction: summarization can drop the
detail a later query needs (ChatGPT+Summarization fell to 51.5% on AltQA vs a 72% baseline, while *retrieval*
matched or beat baseline on PaperQA 75→79% and MeetingQA 72→78%) — so a brief that replaces the source can lose
to a queryable store; and the nearest measured analog, PlugMem's WebArena offline protocol (a new agent
inheriting a pre-built memory graph: Shopping 58.4 vs 52.6, GitLab 55.2 vs 51.4), is flagged in the appendix as
transferring a **structured graph, not a distilled prose brief**, so it maps only partially.

---

## Findings ranked by how directly the plugin's continuity claim depends on them

1. **M11 — cold-vs-seeded handoff is unmeasured.** The handoff brief is the plugin's central move (reach a
   seam, distil, clear, reseed) and the finding is that nothing in the literature tests it. Every claim the
   plugin makes about session seams rests on this gap.
2. **M8 — goals live in context; re-injection alone isn't sufficient.** The goal anchor fires on every prompt,
   making it the plugin's most-executed mechanism; M8 both justifies keeping the goal visible and bounds the
   anchor to necessary-not-sufficient.
3. **M9 — end-of-prompt placement.** The anchor's specific design choice, and the only well-replicated,
   peer-reviewed cluster in the set. If end-placement carries no benefit on this substrate, the anchor's
   rationale goes with it.
4. **M3 — distilled auto-extracted facts raise accuracy.** The single direct evidence for auto-facts, the
   plugin's other always-on hook.
5. **M10 — self-generated memory can lock in wrong beliefs.** The risk that makes the review layer
   load-bearing; it is the one finding under which the plugin's own written memory can subtract from the score.
6. **M1 — cross-session degradation is real and large.** The problem statement the whole system answers. If it
   does not reproduce on this substrate, no arm can differ and the rest of the tests are unpowered.
7. **M5 — model-dependence and explicit task-state.** Governs both the ledger's shape and whether an effect
   should be expected at all on a strong model — directly testable by the three-model design.
8. **M2 — memory beats no-memory.** Supports the weak form ("some ledger beats no ledger"); the report is
   explicit that it does not show this design beats another.
9. **M6 — self-written reflections re-read as memory.** The closest analogue for write-then-re-read, but
   within-task across trials, not across sessions — one step removed from what the ledger does.
10. **M7 — externalizing working state.** Foundational and adjacent: in-context scratchpads inside one task,
    while the plugin's ledger is a durable cross-session file.
11. **M4 — distilled memory at 3–4× fewer tokens.** Bears on the plugin's economics rather than on whether
    continuity works; graded cost-parity only, medium, 2-1.
