# LLM Implementation Intelligence Test — "The Selde Weir"

A benchmark for **LLM-powered solutions** (systems making multiple orchestrated LLM
calls plus application logic), not just bare models — though it works for bare-model
comparison too. Built 2026-08-25. All content (places, people, dates, numbers, plot
mechanism) was invented for this test and interlocked deliberately.

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
