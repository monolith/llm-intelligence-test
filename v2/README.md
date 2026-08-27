# Version 2 — "The Sallow Creek Viaduct"

A harder, larger successor to the top-level test ("The Selde Weir"). Same idea — a
benchmark for LLM-powered solutions and bare models alike, scored against an answer
key designed before a word of prose was written — at more than triple the size, with
three different ways of administering it. v2 shares nothing with v1: new names, new
places, new mechanism, checked by grep against the full v1 name list. If you landed
here directly, this file is self-contained; the top-level [`README.md`](../README.md)
covers v1 and links back here.

## What v2 is, and how it differs from v1

| | v1 | v2 |
|---|---|---|
| Original stories | 3 | 4 |
| Retellings | 6 | 12 |
| Test input | ~3,600 words | ~18,600 words |
| Administration | one (hand everything over at once) | three modes — see below |
| Near-tie pairs | 3 | **11** |
| Abstention items ("cannot be determined") | 0 | **6** |
| Decoy theory | no | yes — one, refuted two independent ways |

v1 fits one context window, so a frontier model can ace it in a single pass; that was
the reason to build v2. Scale (four stories, twelve retellings) and depth (harder
arbitration, not more obscurity) were both added, then three administration modes
were layered on top to test not just what a model can reconstruct but what survives
being fed the material in different shapes — all at once, one piece at a time, or one
piece at a time with unrelated noise and a real memory wipe partway through.

**The devices, briefly:**

- **Key first, prose second.** The mechanism (a bridge bearing set one inch short of
  its drawing, so it binds in cold weather only after being re-seated at the wrong
  temperature twelve years later) was designed with its full arithmetic before any
  story was written. Every number in the prose is load-bearing somewhere in the key.
- **Eleven near-tie pairs.** For each, a wrong value is carried by two narrators and
  the correct one by two others — a model that counts sources instead of weighing
  them takes the wrong side every time. Each tie is broken only by a quoted document,
  an arithmetic derivation, or one narrator's own internal consistency, never by
  majority.
- **A recoverability index.** Every scored fact is still guaranteed recoverable:
  correct in at least two narrators, or derivable by arithmetic, or settled by a
  document that outranks memory. Every planted error is unique to one narrator (with
  one declared exception — a shared piece of local folklore, refuted five different
  ways, that exists specifically to be debunked rather than discovered).
- **A decoy theory.** Two of the corpus's most authoritative-sounding narrators offer
  a wrong explanation for the bridge's behavior — a heavier deck, not the bearing —
  that fits nearly every fact except two, which appear elsewhere in the same corpus.
- **Six abstention items.** Questions where the honest answer is "cannot be
  determined from the sources." Two of them are dressed as ordinary factual
  questions with an apparent majority answer that turns out to be one witness
  contradicting herself, not two independent witnesses agreeing.

Design reasoning, calibration targets, and the full change list from the original
(v2.0) design to the shipped (v2.1) material are in `answer-key/AUTHORING-NOTES.md`
and `answer-key/HARDENING-v2.1.md` — both secret, both worth reading if you want to
know *why* a given item is hard rather than just that it is.

## Directory layout

| Path | Contents | Visibility |
|---|---|---|
| `originals/01…04*.md` | The four source stories | **SECRET** |
| `answer-key/canon.md` | Ground-truth facts, timeline, relationships, cross-story insights | **SECRET** |
| `answer-key/corruption-map.md` | Per-narrator planted errors, the eleven near-tie pairs, the recoverability index | **SECRET** |
| `answer-key/answers-and-scoring.md` | Every answer, every checklist, the 100-point score sheet | **SECRET** |
| `answer-key/AUTHORING-NOTES.md` | Original (v2.0) design reasoning — superseded in part, kept for the "why" | **SECRET** |
| `answer-key/HARDENING-v2.1.md` | Full record of the v2.0 → v2.1 hardening pass, with expected-score reasoning | **SECRET** |
| `answer-key/KEY-AUDIT.md`, `narrator-briefs.md` | Historical audit record; per-narrator writing briefs | **SECRET** |
| `test-input/retellings/r01…r12*.md` | The twelve retellings | give to system |
| `test-input/questions.md` | Sections A–G | give to system |
| `test-input/bundle-single.md` | The twelve retellings plus the questions, pre-bundled into one 838-line file for single mode | give to system (single mode) |
| `noise/n01…n12*.md`, `noise/questions.md` | Twelve public-domain excerpts (~1,200 words each) and one-line questions about them | give to system, **noisy mode only** |
| `noise/SOURCES.md` | Where the noise excerpts came from | reference |
| `harness/ORCHESTRATION.md` | The subagent-orchestrated administration protocol — how the recorded runs were actually made | reference |
| `harness/run_v2.py`, `judge.py`, `report.py`, `README.md` | The direct-API runner: same three modes, real API calls, for when a key exists | tooling |
| `harness/audit.py`, `audit-triage.md` | A mechanical audit of the corpus (verbatim-quote checks, near-tie carrier uniqueness, planted-error uniqueness, prose-overlap with the originals) and the triage of every finding | tooling / record |
| `harness/validation-blind-solve*.md` | The two blind solves (94, then 96) that set the hardening target — run *with* file-search tools, so not single-pass ceilings | reference |
| `runs/<model>/<mode>/` | Recorded evidence for each of the twelve cells | evidence |
| `runs/kappa.json` | Hand-scored item-level agreement (Cohen's κ) for two cells | evidence |
| `results.md` | The aggregate twelve-cell report this README's numbers come from | evidence |

## Administration protocol

There are three modes. All three share one hard rule: **nothing under `answer-key/`
or `originals/` may reach the system under test** — not as file content, not as a
retrieval source, not as a tool path it could take. The system is handed a fixed,
pre-approved sequence of file reads (retellings, noise documents, questions — one
prescribed read per document; `single` mode's 838-line bundle returns whole) and told
to use nothing else. A transcript check afterward confirms the sequence of paths
touched matches the allowed list exactly; a run that used an extra tool call or
reached a forbidden path is voided and repeated. This is also why the two 94/96 blind
solves in `harness/validation-blind-solve*.md` don't count as ceilings: those ran
*with* open-ended file-search tools that could grep and re-read any file on demand,
which is retrieval doing the work, not a single pass.

- **single.** One dispatch: the system-under-test instructions, then all twelve
  retellings and the questions, in one message. Its reply is the answer sheet.
- **sequential.** One dispatch with retelling 1 and the instruction "acknowledge in
  one line; more retellings follow." Retellings 2–12 arrive as follow-up messages to
  the *same* subagent, one per turn, then the questions. Nothing is discarded —
  everything stays in the same running context.
- **noisy.** As sequential, but after each retelling a noise message follows: one
  public-domain excerpt (text inline) plus its one-line question. After retellings 4
  and 8, the subagent is asked to write `notes-after-r0{4,8}.md` — "the notes you
  would need to answer detailed questions later about everything read so far except
  the unrelated documents" — and a **fresh subagent** of the same model tier is
  started whose first message is those notes verbatim, followed by the next
  retelling. The old subagent's context is genuinely gone; this hand-off *is* the
  compaction. The final segment answers the questions.

## How scoring works

100 points, sections A–G: Reconstruction 30, Relationships 10, Math 20, Logic 15,
Contradictions 10, Theory 10, Summary 5.

- **Sections C and E** are exact-match, graded against the key's stated values and
  tolerances.
- **Sections A, D, F, and G** are yes/no checklists — one point per item, present or
  not, no partial credit. Bold text in a checklist item gates the point; unbolded
  parentheticals are context for the grader only.
- **Section B** is scored against stated criteria (one line each, with reasoning).
- **Six abstention items**, inside D and E, have "cannot be determined from the
  sources" as the only correct answer. A confident guess on one of these — even a
  reasonable-sounding one — triggers a **gullibility deduction**: −2 per item,
  capped at **−12** for all six.
- **Corruption deductions** apply separately, anywhere in the answers: −1, uncapped,
  for each planted wrong fact asserted as true. Hedged mentions ("r09 says fifty
  degrees, but the rule elsewhere gives forty") are not penalized.
- **Two independent judgings.** An opus-tier subagent, given
  `answer-key/answers-and-scoring.md` and one cell's `answers.md`, scores every item
  and writes `score.json` (a strict schema) and `score.md`. Each cell is judged
  *twice* by independent judge subagents; the maximum difference in total between the
  two is reported as judge stability. Two cells are additionally hand-scored by the
  controller, item by item, to compute Cohen's κ.

## Results

These are the twelve recorded cells, one run each, on material version 2.1.

**Table 1 — totals (score.json, with score-2.json in parentheses when it differs)**

| Model | single | sequential | noisy |
|---|---|---|---|
| haiku | 57 (56) | 62 (63) | 54 (52) |
| sonnet | 76 (79) | 76 (77) | 81 |
| opus | 92 | 92 (94) | 86 |
| fable | 93 | 91 | 88 |

**Judge stability** (max absolute difference in total between the two independent
judgings, per cell) ranges from 0 to 3 across all twelve cells. Verbatim from
`results.md`: **Max across all judged cells: 3.**

**Cost (Table 3 in `results.md`, summarized).** Full detail — assistant turns, input
and output tokens, thinking tokens, wall-clock seconds — is per-cell in `results.md`;
the shape of the cost column is: it rises with administration mode (noisy typically
costs 3–5x single at the same model tier — more turns, larger cumulative context, the
compaction hand-off) and it rises with model tier. Across all twelve cells, list-price
cost ranges from **$0.34** (haiku/single) to **$23.69** (fable/noisy), with fable
consistently the most expensive tier and noisy consistently the most expensive mode.

**Caveats, stated plainly, quoting `results.md`:** "The judge is an Opus subagent, the
same model family as the systems under test, which is a potential source of bias in
scoring. Sampling is not deterministic: each cell reflects a single run (n = 1), not
an average over repeats. All results in this report are for version 2.1 of the story
test material."

Two things sharpen that caveat rather than soften it:

- **Judge bias is mitigated, not eliminated.** Every cell is judged twice
  independently (the judge-stability numbers above); two cells are additionally
  hand-scored by the controller for item-level Cohen's κ, recorded in
  `runs/kappa.json`. Per-cell κ ranges from 0.74 (opus/sequential, where the two
  judgings differed by 2 points out of 100) to 1.0 (several cells, both judgings
  identical), mostly at or above 0.90.
- **Material version.** These runs were administered against v2.1. Afterward, six
  small paraphrase edits (v2.1.1) were applied to `test-input/retellings/`, fixing
  near-verbatim prose overlap between three retellings and their source originals
  that a mechanical audit (`harness/audit-triage.md`) caught. Those edits change
  wording only — no scored fact, value, or answer changes — so the v2.1 scores above
  remain valid evidence; they just describe material that has since been very
  slightly reworded.

## What the numbers show

By tier, across all three modes: haiku ~55–62, sonnet ~76–81, opus 86–92, fable
88–93. Four clearly separated tiers, with the top two — opus and fable — sitting much
closer to each other than to sonnet below them.

**Compaction cost**, isolated by comparing sequential (same turn-by-turn delivery, no
noise, no memory wipe) against noisy (identical, but with noise injected and a real
hand-off to a blank subagent after retellings 4 and 8): haiku loses about 8 points,
opus about 6. Fable loses only about 3. Sonnet lost none at all — its noisy score (81)
was actually *higher* than its sequential score (76) on this single run, which given
n = 1 is worth taking as "no measurable cost here," not "compaction helps."

**Ceiling.** The best score anywhere in the twelve cells was 92–93, both in single
mode (opus 92, fable 93) — a careful, uninterrupted single pass. That's the practical
ceiling for this material as administered: hard enough to spread haiku through sonnet
across a 30-point range, but the top two tiers compress into a narrow band rather than
spreading further apart. (This is distinct from the 94 and 96 scored by the two blind
solves in `harness/validation-blind-solve*.md` — those had file-search tools available
and could re-read or grep any retelling at will, which is a different, easier task
than reconstructing from one prescribed pass through the material.)

## Evidence layout

Each of the twelve cells writes its full evidence to `runs/<model>/<mode>/`:

- `answers.md` — the system under test's own answer sheet, written by itself.
- `transcript.jsonl` — the reduced request/response record (role, text, model, usage,
  timestamps) for the whole cell. Noisy-mode cells also keep `transcript-seg1.jsonl`,
  `transcript-seg2.jsonl`, `transcript-seg3.jsonl` — one file per subagent segment,
  split at each real compaction hand-off.
- `notes-after-r04.md`, `notes-after-r08.md` — noisy mode only: the retention notes
  the outgoing subagent wrote for the incoming one at each hand-off.
- `score.json` / `score.md` and `score-2.json` / `score-2.md` — the two independent
  judgings.

`runs/kappa.json` holds the hand-scored item-level agreement described above.
`results.md` is the aggregate report rolled up from every cell's `run.json`-equivalent
totals and `score.json`.

## How to reproduce

**With subagents** — no API key needed, and how the evidence above was actually
produced. Follow `harness/ORCHESTRATION.md` exactly: dispatch one subagent per
(model tier x mode) as the system under test, using the same prescribed reads in the
same order for every run; after each cell, check the transcript against the allowed
path list before treating the run as valid. Judge with a separate opus-tier subagent
against `answer-key/answers-and-scoring.md`, twice per cell, independently.

**With an API key** — `harness/run_v2.py` runs the same three modes as real API calls
from a single Python process. See `harness/README.md` for environment setup (a
git-ignored `.env` file at the repo root supplies the key; without it, even
`--dry-run` exits without running) and the exact commands for one cell, all twelve in
a loop, or a no-network preview. `harness/judge.py` scores a cell against the key;
`harness/report.py` rolls every cell's `run.json` and `score.json` up into a
`results.md`-shaped report. `harness/audit.py` runs the mechanical corpus audit (see
`harness/audit-triage.md` for what it checks: verbatim document quotes, near-tie
carrier uniqueness, planted-error uniqueness, and prose overlap between the
retellings and the originals) independent of any model run.

**One real difference between the two paths:** `run_v2.py`'s `noisy` mode *simulates*
compaction — it asks the model to write retention notes, then discards the real
conversation history in the same process and replaces it with just those notes. The
subagent path used for the evidence above performs *real* compaction: a brand-new
subagent instance, with no access to the old conversation at all, seeded only with
the outgoing instance's notes. These are not the same administration; a noisy-mode
run from the API harness is not directly comparable to the noisy-mode numbers in this
README without noting which path produced it.

## Known limitations

- **No repeats yet.** Every cell is n = 1. Repeats (and reporting mean ± range) are
  deferred until there's a specific reason to think the ranking above might not hold.
- **Simulated vs. real compaction.** As above — the two administration paths
  (subagent hand-off vs. single-process API harness) implement "compaction"
  differently, and results from one should not be read as validating the other.
- **Public repository.** This material, like v1's, will eventually reach some
  vendor's training data through ordinary web crawling or logs. When these numbers
  stop meaning anything, regenerate a fresh corpus using the same recipe: canon
  first, stories second, retellings third, a recoverability audit, then a mechanical
  corpus audit before anything ships.
