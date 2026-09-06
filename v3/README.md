# Story test v3: which Claude model, and what it costs

A reading-and-reasoning test given to four Claude models (Haiku 4.5, Sonnet 5, Opus 5, Fable 5.1).
Twenty-four narrators retell parts of the same invented history. Each knows only part of it, each
gets some of it wrong, and some errors were planted on purpose. The model never sees the eight
underlying stories. It has to reconstruct them, resolve the contradictions, compute a few figures,
and say "the sources do not settle this" where they do not. A 100-point key scores the result.

Everything here is original to this repository, so no model has seen it in training. This README
gives the takeaway first, then the method, the results, and how to repeat the test.

---

## Takeaway: which model, and when

Scores are out of 100. Short = the material fits in one context (about 37,000 words), mean of nine
runs per model. Long = the material does not fit (about 1.5M tokens), one run per model. Dollars are
API list prices applied to the actual token counts; on a subscription plan they are notional and
the currency is turns, which were the same for every model.

| Model | Short score (95% interval) | Short cost per run | Long score | Long cost per run | Long cost per point |
|---|---|---|---|---|---|
| Haiku | 48.9 (43.9 to 54.0) | $0.57 to $2.55 | 6 | $41 | $6.83 |
| Sonnet | 63.5 (61.5 to 65.5) | $2.08 to $6.38 | 23 | $82 | $3.58 |
| Opus | 76.7 (74.0 to 79.4) | $4.03 to $15.98 | 26 | $245 | $9.42 |
| Fable 5.1 | 82.7 (81.5 to 83.9) | $9.67 to $34.20 | 67 | $1,043 | $15.33 |

**The decision rule.** Upgrading from model B to model A pays when the value of one correct point
to you, V, satisfies V × (score A − score B) > cost A − cost B. With the measured numbers, the
break-even V per point on the short variant is:

| Upgrade | Points gained (95% interval) | Break-even V, cheapest to most demanding administration |
|---|---|---|
| Haiku → Sonnet | 14.6 (9.3 to 19.8) | $0.10 to $0.26 per point |
| Sonnet → Opus | 13.2 (9.6 to 16.9) | $0.15 to $0.73 per point |
| Opus → Fable | 6.0 (3.3 to 8.7) | $0.94 to $3.04 per point |

A point on this test is one fact reconstructed, one figure computed, one contradiction caught, or
one planted error not repeated.

**When to use which, on this kind of task:**

- **Haiku** when the material fits in one context and a wrong item costs you less than about ten
  cents. It scored 45 to 51 and cost 0.6 to 2.6 dollars a run. Do not use it when the material does
  not fit: it scored 6 of 100 and cost more per correct point than Sonnet.
- **Sonnet** when the material fits and a wrong item costs between ten cents and about seventy.
  It was the cheapest per correct point when the material did not fit, but its score there (23)
  makes the answers unusable without checking.
- **Opus** when the material fits and a wrong item costs more than fifteen to seventy cents. Under
  compaction it collapsed to 26, and correction rounds did not recover it (see the retry results).
- **Fable 5.1** when a wrong item costs more than one to three dollars, or whenever the material
  does not fit. It was the only model that kept most of its score under compaction (83 → 67), at
  about $1,040 for the run. Its worst short run (80.5) was above Opus's mean.

**Four findings that shape the rule:**

1. When the material fits, the order Fable > Opus > Sonnet > Haiku held in 26 of 27 paired
   administrations. Run-to-run spread was 0.3 to 5.6 points for the three larger models and up to
   11.4 for Haiku.
2. When it does not fit, three of the four models lost two-thirds to seven-eighths of their score.
   Haiku with everything in view (45) beat Opus after compaction (26). Fable held, and its handover
   notes explain why: 75,500 words at the end versus 15,000 to 18,000 for the others.
3. Telling a model its answers are wrong did not close the gap. Sonnet, corrected across three
   regimes, never reached Opus's score, twice got worse, and spent more turns and tool calls than
   Opus used once.
4. Reading is the cost; asking is not. One full read of the long corpus by Sonnet was $158 and
   1,293 turns; a follow-up question afterwards was $0.77 and 3 turns.

Full statistics, intervals and the worked break-evens: `QUANT.md`. Plain-language explanation of
the whole study: `EXPLAINER.md`.

---

## 1. Tests performed and methodology

### Material

- Eight original stories about a dairy cooperative in a farming valley (never shown to the model).
- Twenty-four retellings, each covering part of the history, each with its own errors; several run
  separate stories together. Specific false claims are planted in specific narrators
  (`answer-key/corruption-map.md`).
- Forty unrelated documents (period papers, stories, fake proofs, code specifications, chatter,
  nonsense), each with a one-line surface question, used as noise.
- Four generated noise documents of about 220,000 words each, used only in the long variant.

### Question sheet and scoring

- 100 points in seven sections: A, reconstruct the eight stories (50); B, relationships; C and E,
  exact-match figures and lists; D, logic; F, causal theory; G, summary.
- Ten abstention items: the correct answer is that the sources do not settle it. A confident answer
  scores zero.
- Asserting a planted error as fact costs points. A hedged mention ("one source wrongly claims")
  does not.
- Every answer sheet is scored by two independent judges (Opus instances given the key and the
  answers, nothing else). Both totals are reported. Judges differed by 2.3 points on average, at
  most 8, across 36 short runs.

### Short variant (material fits)

Same material and questions, three ways of delivering them:

- **single**: everything in one message.
- **sequential**: one retelling per message, in a fixed order, then the questions.
- **noisy**: as sequential, with an unrelated document after each retelling, and the reader
  replaced twice (after retellings 8 and 16). The outgoing reader writes retention notes; a fresh
  instance continues from those notes alone. The replacement is the compaction.

Four models × three administrations × three independent runs = 36 runs, 72 gradings. Same
prompts every time (`PROMPTS.md`). Repeats are in `runs-r2/` and `runs-r3/`.

### Long variant (material does not fit)

The same twenty-four retellings, but eight of them buried inside 62,000-word wrapper documents,
with the four large noise documents after retellings 6, 12, 18 and 24 and the short distractors
between the rest. About 1.5M tokens. No model can hold it.

- **Read once, answer from notes**: a chain of fresh readers, each given a token budget of
  110,000, reads its share in prescribed spans and writes retention notes; the next reader starts
  from those notes alone. Haiku needed 35 segments, Sonnet 21, Opus 23, Fable 24. After the
  reading, the 100 points are asked in three batches (34, 35 and 31 points), each answered by a
  fresh reader from the final notes only. One run per model.
- **Re-read per batch**: the whole corpus read again for each batch, with that batch's questions
  in hand from the start. Run for batch 1 only, three models.
- **Correction regimes** (Sonnet only): told its answers were wrong, in three regimes, to see
  whether retries reach Opus's score. Details in `results-retry.md`.
- **Single live session** (Sonnet only): one session reading the corpus with the harness's own
  automatic compaction (five compactions, peak 929,056 tokens) instead of hand-off notes.

### Verification

Every run's transcript was checked before scoring: every prescribed read present, in order, and
nothing else opened. Runs that broke protocol were discarded and re-run with the identical prompt;
the discards are kept beside their cells in `void-*/` folders with a note. Coverage of every
prescribed span was checked separately, because a read that exceeds the tool's size limit fails
silently. `harness/PROTOCOL-LONG.md` records every defect found and how it was handled, including
two harness workarounds needed for Fable's very large notes.

### Cost accounting

Tokens (including cache reads), assistant turns, tool calls, and dollars at API list prices, per
run and per phase. Turns and tool calls are fixed by the administration, not the model: about 15,
83 and 150 turns for the three short administrations, for every model.

---

## 2. Results

### Short variant, three runs per cell (mean; two judges per run)

| Administration | Haiku | Sonnet | Opus | Fable 5.1 |
|---|---|---|---|---|
| single | 45.0 | 63.3 | 78.7 | 84.2 |
| sequential | 51.3 | 64.0 | 76.0 | 82.2 |
| noisy | 50.5 | 63.2 | 75.5 | 81.8 |
| pooled, nine runs | 48.9 | 63.5 | 76.7 | 82.7 |
| cost per run (single / sequential / noisy) | $0.57 / $1.05 / $2.55 | $2.08 / $3.42 / $6.38 | $4.03 / $7.16 / $15.98 | $9.67 / $14.08 / $34.20 |
| cost per point, pooled | $0.028 | $0.062 | $0.120 | $0.235 |

Paired differences, by administration and repeat: Fable over Opus 6.0 points (8 wins of 9), Opus
over Sonnet 13.2 (9 of 9), Sonnet over Haiku 14.6 (9 of 9). Per-cell intervals, standard
deviations and paired t statistics: `QUANT.md`. First-run tables with section profiles:
`results.md`.

### Long variant, one run per model

| Model | Read once, answer from notes (judge 2 in parentheses) | Batches 1 / 2 / 3 | Segments | Notes at end | Total cost | Cost per point |
|---|---|---|---|---|---|---|
| Haiku | 6 (8) | 4 / 2 / 0 | 35 | 14,700 words | $41 | $6.83 |
| Sonnet | 23 (24) | 5 / 4 / 14 | 21 | 18,200 | $82 | $3.58 |
| Opus | 26 (24) | 10 / 10 / 6 | 23 | 15,900 | $245 | $9.42 |
| Fable 5.1 | 68 (66) | 29 / 16 / 23 | 24 | 75,500 | $1,043 | $15.33 |

Re-read per batch, batch 1 only (of 34): Haiku 3, Sonnet 12 (11), Opus 18 (20). Against 4, 5 and
10 when answering from notes. Re-reading with the questions in hand doubled Sonnet's and Opus's
batch score and did nothing for Haiku.

Sonnet correction regimes, batch 1 (of 34), with total turns / tool calls / dollars:

| Condition | Score | Turns | Tool calls | Cost |
|---|---|---|---|---|
| Opus, one re-read pass (the target) | 18 (20) | 1,455 | 662 | $225 |
| Sonnet, one re-read pass | 12 (11) | 1,350 | 616 | $77 |
| Sonnet, whole sheet flagged wrong, 5 retries | 15 (16) | 1,478 | 714 | $88 |
| Sonnet, specific items flagged, 3 rounds | 12 | 1,372 | 628 | $80 |
| Sonnet, one live session with automatic compaction | 14 | 1,293 | 546 | $158 |

Full tables: `results-long.md`, `results-retry.md`, and `scoresheet.md` (every cell, every round,
with tokens, turns, tool calls and dollars).

### What the losses were

Across every model and both variants the dominant loss is the same: asserting a planted error as
fact. Under compaction the models did not become vague; they stated the planted claims at full
confidence, with nothing on the surface of the answer to mark them. Section profiles per cell are
in `results.md` and in each run's `score.md`.

---

## 3. How to replicate

The rule that makes results comparable: **the system under test gets the material and the
questions, and nothing else.** No answer key, no canon, no corruption map, and no file listing that
reveals which documents are noise. Deliver documents in the prescribed order, one read each, and
do not let the model return to a source after the questions arrive.

### Manually, with a chat window

Short variant:

1. *single*: paste the whole of `test-input/bundle-single.md` into one message. It ends with the
   questions. Ask for the answer sheet in three messages (Section A stories 1 to 4; stories 5 to 8
   plus Section B; Sections C to G), because one reply gets truncated.
2. *sequential*: paste `test-input/retellings/r01.md`, ask for a one-line acknowledgement, repeat
   for r02 to r24 in order, then paste `test-input/questions.md`.
3. *noisy*: as sequential, but after each retelling paste the next distractor named in
   `distractors/ORDER.md` and ask its one-line question. After r08 and again after r16, ask for
   "the notes you would need to answer detailed questions later about everything you have read
   except the unrelated documents", copy them out, start a brand-new chat, paste the notes as its
   first message, and continue from the next retelling.

Long variant: the same shape, with r03, r06, r09, r12, r15, r18, r21 and r24 delivered as their
`test-input/long/rNN-long.md` versions and `distractors/long/L1..L4.md` after r06, r12, r18 and
r24. Start a fresh chat whenever the current one is nearly full, carrying only the notes across.
Expect twenty or more restarts. Then answer the three files in `test-input/batches/` instead of the
single question sheet. For the re-read condition, do the whole reading again per batch and show the
batch's questions before the first document.

Scoring: open `answer-key/answers-and-scoring.md` and go item by item. Exact-match items take no
near misses; abstention items score only if the answer abstains; every planted error asserted as
fact costs points; hedged mentions do not. Have two people score independently and report both.
Run each cell three times if you want an error bar.

### Systematically, with the scripts

The exact prompts for every reader and for the judge are in `PROMPTS.md`. The scripts assume an
agent harness with a Read tool that returns at most about 25,000 tokens per call and a Write tool.

Short variant: run the prompts in `PROMPTS.md` against `test-input/`, assemble the three answer
parts with `harness/cell_finish.sh <model> <mode> <transcript>`, which also verifies the reads.
Repeats go in `runs-r2/`, `runs-r3/` by setting `RUNS=v3/runs-r2` in the environment.

Long variant, read once:

    python3 harness/plan_segments.py --root v3 --model <name> --budget 110000 \
        --out runs/<name>/long-notes/ingest/plan.json --render 1 > runs/<name>/long-notes/ingest/segment-1.md
    python3 harness/split_big_reads.py runs/<name>/long-notes/ingest/segment-1.md
    # give segment-1.md to a fresh reader with the ingest prompt from PROMPTS.md, then:
    harness/ingest_step.sh <name> 1 <transcript> 110000     # verifies, checks coverage, renders segment 2

Repeat per segment. Then run the three batch prompts against the final notes, and the batch judge
prompt twice per batch. Re-read condition: `harness/reread_step.sh <name> <batch> <segment>
<transcript> 110000`. If a chain's notes outgrow the budget (Fable's did), `harness/tail_segments.py`
builds hand-sized final segments and `harness/tail_verify.sh` checks them.

Reports:

    python3 harness/stats_short.py --trees v3/runs v3/runs-r2 v3/runs-r3 --prices v2/harness/prices.json --out v3/QUANT.md
    python3 harness/results_long.py --runs v3/runs --batches v3/answer-key/batches.md --prices v2/harness/prices.json --out v3/results-long.md
    python3 harness/scoresheet.py --root v3 --prices v2/harness/prices.json --out v3/scoresheet.md

### Verifying a run before you believe it

`v2/harness/verify_transcript.py` checks that a reader opened only what it was given, in order.
`harness/read_coverage.py` checks that every prescribed span actually came back. Both exist because
runs failed silently without them. `harness/PROTOCOL-LONG.md` lists every failure found, the fix,
and which earlier numbers it changed.

---

## What is where

| Path | What it is |
|---|---|
| `test-input/retellings/r01…r24.md` | the twenty-four retellings, the scored material |
| `test-input/questions.md` | the 100-point question sheet (short variant) |
| `test-input/batches/batch-1..3.md` | the same sheet split three ways (long variant) |
| `test-input/bundle-single.md` | all twenty-four retellings plus the questions, as one file |
| `test-input/long/rNN-long.md` | eight retellings each buried inside a ~62,000-word document |
| `distractors/d01…d24.md`, `k01…k16.md` | the unrelated documents, each with a surface question |
| `distractors/ORDER.md` | the fixed order distractors are interleaved in |
| `distractors/long/L1…L4.md` | four generated noise documents, ~220,000 words each |
| `answer-key/answers-and-scoring.md` | **the key**, item by item, 100 points |
| `answer-key/batches.md` | which key items belong to which batch |
| `answer-key/canon.md`, `corruption-map.md` | what actually happened; every planted error and who carries it |
| `PROMPTS.md` | the exact prompts given to readers and judges |
| `EXPLAINER.md` | the study explained for someone new to language models |
| `QUANT.md` | means, intervals, paired tests, cost per point, the break-even rule |
| `results.md`, `results-long.md`, `results-retry.md`, `scoresheet.md` | generated result tables |
| `harness/` | the scripts, and `PROTOCOL-LONG.md` with every defect found |
| `runs/`, `runs-r2/`, `runs-r3/` | every run's answers, transcripts, notes and both judges' scores |

The answer key is in the repository so the test can be repeated. It must never be shown to the
system under test.

## Caveats

- Long-variant scores are one run per model. The direction is reliable; the digits are not.
- Two Opus instances did the grading. They agree with each other and with a hand-scored sample,
  but they are not human graders.
- One task family: synthesis from contradictory sources with planted errors. Other work may rank
  the models differently.
- Fable 5.1's long run needed two harness workarounds for its very large notes, and its batch
  readers re-read their own notes after seeing the questions. Both are recorded in
  `harness/PROTOCOL-LONG.md` and neither gave it access to anything the condition disallows.
- Five short-variant runs and several long-variant segments were discarded for protocol slips and
  re-run with the identical prompt. Every discard is kept beside its cell with a note.
