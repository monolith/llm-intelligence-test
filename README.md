# LLM Implementation Intelligence Test — "The Selde Weir"

A benchmark for **LLM-powered solutions** (systems making multiple orchestrated LLM
calls plus application logic), not just bare models — though it works for bare-model
comparison too. Built 2026-08-25. All content (places, people, dates, numbers, plot
mechanism) was invented for this test and interlocked deliberately.

**A larger, harder version 2 exists** — see [Version 2 below](#version-2--the-sallow-creek-viaduct), or the full guide at [`v2/README.md`](v2/README.md).

## How it works

Three original interlinked stories were written first, with relationships, dates, and
math planted intentionally (the answer key was designed before the prose). Each story
stands alone; seven insights emerge only from reading all three. The stories were then
deconstructed into **six retellings** by fictional narrators who each knew part of the
history — some facts right, some wrong, two of them juxtaposing separate stories. The
system under test sees **only the retellings and the questions** and must reconstruct
the originals and answer logic, math, relationship, theory, and summary questions whose
answers are known in advance and scored on a 100-point sheet.

## Directory layout

| Path | Contents | Visibility |
|---|---|---|
| `originals/` | The three source stories | **SECRET** |
| `answer-key/canon.md` | Ground-truth fact sheet, timeline, relationships, cross-story insights | **SECRET** |
| `answer-key/corruption-map.md` | Per-narrator errors + how each contested fact resolves | **SECRET** |
| `answer-key/answers-and-scoring.md` | All answers, rubrics, 100-pt score sheet | **SECRET** |
| `test-input/retellings/` | The six retellings (r1–r6) | give to system |
| `test-input/questions.md` | Sections A–G | give to system |

## Administration protocol

1. Give the system under test the six retellings and `questions.md`. **Nothing else.**
   No file from `originals/` or `answer-key/` may enter its context, its retrieval
   store, or its tool reach. Contamination voids the run.
2. Let the system use whatever it is built from — multiple calls, agents, retrieval
   over the retellings, code execution. That's the point: this measures the
   *implementation*, not one forward pass.
3. Score with `answers-and-scoring.md`. Sections C and E are exact-match; A, D, F and G
   are yes/no checklists (1 point per item, no partial credit); B has stated criteria.
   Scoring is done by a human or by an **independent judge LLM** given the key — never by
   the system under test, and never by a model in its own family. Validate the judge once
   by hand-scoring two runs and reporting Cohen's κ per section.
4. For comparisons, fix the questions and retellings verbatim, run each system once (or
   n times, report mean ± range), and report the seven section subscores, not just the
   total — the profile is more diagnostic than the sum (e.g., strong C/weak E means
   good arithmetic, poor source arbitration).

## What each section measures

- **A Reconstruction (30)** — synthesis across conflicting partial sources
- **B Relationships (10)** — relational/genealogical inference
- **C Math (20)** — multi-step arithmetic over facts scattered across sources
- **D Logic (15)** — necessary vs. sufficient, eliminative reasoning, causal explanation
- **E Contradictions (10)** — conflict detection and source arbitration (majority,
  arithmetic, document-beats-memory, internal consistency)
- **F Theory (10)** — abductive theory formation from distributed evidence
- **G Summary (5)** — compression without loss of causal structure
- **Corruption deductions** — gullibility penalty: asserting a planted error as fact

## Design guarantees (what makes it fair)

- Every canonical fact needed for a question is recoverable from the retellings: it
  appears correctly in ≥2 narrators, **or** is derivable by arithmetic, **or** is
  settled by a documentary quote outranking a memory. See the recoverability index in
  `corruption-map.md`.
- Every planted error is unique to one narrator, so no error can win a majority.
- One retelling (r6) contains a deliberate *internal* contradiction as a bonus probe.

## Reuse / regeneration

The corpus burns slowly: a system can't have memorized it, but if these files ever leak
into training data or a vendor's logs-to-training pipeline, regenerate a fresh corpus
using the same recipe (canon first, stories second, retellings third, recoverability
audit last). One line of honesty: the stories were invented fresh here — no known
source, borrowed plot, or existing place/person — but no author, human or model, can
formally prove non-derivation from everything they've ever read.

## Version 2 — "The Sallow Creek Viaduct"

v2 lives under `v2/`, is untouched by v1, and shares nothing with it — new names, new
places, new mechanism. It is the same idea at more than triple the size, tested three
different ways instead of one. v1 was three stories, six retellings, ~3,600 words, one
administration (hand everything over at once). v2 is **four** interlinked stories,
**twelve** retellings, ~18,600 words of test input, and **three administration modes**
that vary how the material arrives rather than what it says.

Depth comes from devices designed into the answer key before any prose was written:
**eleven near-tie pairs**, where the numerically popular answer is wrong and only a
quoted document or a piece of arithmetic breaks the tie; a fully worked **decoy
theory** that explains the evidence right up until two independent facts rule it out;
multi-step math and inference chains that need three different retellings to close;
and **six items** whose only correct answer is "cannot be determined from the
sources" — a confident guess on one of those costs points beyond just getting it
wrong. Every scored fact is still recoverable (present correctly in at least two
narrators, or derivable, or settled by a quoted document), the same design guarantee
v1 used.

### Directory layout

| Path | Contents | Visibility |
|---|---|---|
| `v2/originals/` | The four source stories | **SECRET** |
| `v2/answer-key/canon.md`, `corruption-map.md`, `answers-and-scoring.md` | Ground truth, planted errors and near-ties, the 100-point key | **SECRET** |
| `v2/answer-key/AUTHORING-NOTES.md`, `HARDENING-v2.1.md`, `KEY-AUDIT.md`, `narrator-briefs.md` | Design records for how the corpus was built and hardened | **SECRET** |
| `v2/test-input/retellings/` (r01–r12), `questions.md`, `bundle-single.md` | The twelve retellings, the questions, and a pre-bundled copy for single mode | give to system |
| `v2/noise/` (n01–n12, `questions.md`) | Twelve public-domain excerpts and their one-line questions | give to system, **noisy mode only** |
| `v2/harness/` | Reproduction tooling: the orchestration protocol, the API runner, the judge, the mechanical corpus audit | tooling |
| `v2/runs/<model>/<mode>/`, `v2/results.md` | Recorded evidence and the aggregate report | evidence |

See the fuller guide at [`v2/README.md`](v2/README.md) for what's in every one of those
files. This section covers the protocol, the scoring, and the results in brief.

### Administration protocol

Across all three modes, the system under test is never given a way to reach anything
under `v2/answer-key/` or `v2/originals/` — not as content, not as a retrieval source,
not as a tool path it could take. It is handed a fixed, pre-approved sequence of file
reads (retellings, noise documents, questions — one prescribed read per document) and
nothing else; a transcript check afterward confirms no other path or tool call
happened, and a run that touches a forbidden file or an unlisted tool is voided and
repeated. (Two earlier solves scored 94 and 96, but with open-ended file-search tools
that could grep and re-read anything on demand — that's retrieval doing the work, not
one pass, so they don't count as a ceiling. Every recorded cell below used only the
prescribed reads.)

- **single** — one dispatch: all twelve retellings and the questions arrive together;
  one reply.
- **sequential** — one retelling per turn, "acknowledge briefly, more follow," through
  all twelve, then the questions — same system under test throughout, nothing
  discarded.
- **noisy** — as sequential, but an unrelated public-domain document plus a one-line
  question about it follows each retelling. After retellings 4 and 8, the system is
  asked to write the retention notes it would need later, and a **brand-new** instance
  of the same model tier takes over with only those notes as its starting context —
  a real memory wipe, not a summary kept in the same conversation.

### Scoring

100 points across sections A–G (Reconstruction 30, Relationships 10, Math 20, Logic
15, Contradictions 10, Theory 10, Summary 5). Sections C and E are exact-match; A, D,
F and G are yes/no checklists, one point per item, no partial credit. Six items
(inside D and E) have "cannot be determined from the sources" as the only correct
answer — a confident answer on one of those triggers a **gullibility deduction** (−2
each, capped at −12). Separately, stating any planted wrong fact as true anywhere
costs a **corruption deduction** (−1 each, uncapped). Every cell is scored twice,
independently, by an opus-tier subagent judge given the key; the two totals are
reported side by side.

### Results (material version 2.1)

**Table 1 — totals (score.json, with score-2.json in parentheses when it differs)**

| Model | single | sequential | noisy |
|---|---|---|---|
| haiku | 57 (56) | 62 (63) | 54 (52) |
| sonnet | 76 (79) | 76 (77) | 81 |
| opus | 92 | 92 (94) | 86 |
| fable | 93 | 91 | 88 |

Judge stability, the largest disagreement between two independent judgings of any
cell: **Max across all judged cells: 3**.

Table 3 in `v2/results.md` breaks out tokens, wall-clock time, and list-price cost per
cell. Cost rises with both administration mode (noisy runs roughly 3–5x the cost of
single at the same tier, mostly extra turns and the compaction hand-off) and model
tier; across all twelve cells it ranges from $0.34 (haiku/single) to $23.69
(fable/noisy).

Caveats, stated plainly: **n = 1 per cell** — one run each, not an average, no
confidence interval. The judge is an **opus subagent — the same model family as three
of the four systems under test** — a real, not fully removable, source of possible
bias; it's mitigated by judging every cell twice (above) and by hand-scoring two cells
for item-level agreement (Cohen's κ, in `v2/runs/kappa.json`, mostly at or above 0.90
and no lower than 0.74 anywhere). These runs used **material version 2.1**; six small
paraphrase edits (2.1.1) were applied afterward to fix near-verbatim overlap between
three retellings and the originals — wording only, no scored fact changed, so the
scores above still stand.

### What the numbers show

haiku scores ~55–62, sonnet ~76–81, opus 86–92, fable 88–93. Using sequential as the
apples-to-apples baseline against noisy (same turn-by-turn delivery, the only
difference being injected noise and a real memory wipe), compaction costs haiku about
8 points and opus about 6 — but fable only about 3, and sonnet lost none at all
(it scored higher noisy than sequential on this single run). The best a careful single
pass reached anywhere was 92–93 (opus and fable, single mode): that looks like the
practical ceiling for this material. The test clearly separates the four tiers, but
the top two compress into a narrow band instead of spreading out.

### Evidence, reproducing, and limitations

Each cell's full evidence — answers, transcripts, the noisy-mode retention notes, and
both independent score files — lives under `v2/runs/<model>/<mode>/`. Reproduce it
either by dispatching subagents per the protocol in `v2/harness/ORCHESTRATION.md` (no
API key needed — this is how the recorded evidence was made), or, when an API key
exists, with `v2/harness/run_v2.py` (see `v2/harness/README.md` for setup and
commands). Known limitations: no repeats yet (n = 1 throughout); the API harness's
`noisy` mode *simulates* compaction in one process rather than handing off to a
genuinely blank subagent, so numbers from the two paths aren't directly comparable;
and this is a public repo, so assume the material will eventually reach training data
and regenerate a fresh corpus with the same recipe when these numbers stop meaning
anything. Full detail on all of the above: [`v2/README.md`](v2/README.md).
