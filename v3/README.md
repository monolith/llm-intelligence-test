# Story test v3 — materials, protocol, and results

A synthesis test, not a retrieval test. Twenty-four narrators retell parts of the same history;
each got some things right and some wrong, several ran separate strands together, and none of them
saw the whole. **Eight underlying stories are never shown.** A model's job is to reconstruct them
and answer questions the sources only settle when read against each other.

Nothing here is drawn from published fiction or public-domain text: every retelling, every
distractor, and all of the generated noise is original to this repository, so a model cannot have
seen it in training.

## What is where

| Path | What it is |
|---|---|
| `test-input/retellings/r01…r24.md` | the twenty-four retellings — the scored material |
| `test-input/questions.md` | the full 100-point question sheet (short variant) |
| `test-input/batches/batch-1..3.md` | the same sheet split three ways (long variant) |
| `test-input/bundle-single.md` | all twenty-four retellings plus the questions, as one file |
| `test-input/long/rNN-long.md` | eight retellings each buried inside a ~62,000-word document |
| `test-input/long/MANIFEST.jsonl` | where the needle sits in each of those, by word span |
| `distractors/d01…d24.md` | period documents — plausible, unrelated, each with a surface question |
| `distractors/k01…k16.md` | stories, fake proofs, code specifications, overheard chatter, nonsense |
| `distractors/ORDER.md` | the fixed order distractors are interleaved in, so runs are repeatable |
| `distractors/long/L1…L4.md` | four generated noise documents, ~220,000 words each |
| `answer-key/answers-and-scoring.md` | **the key** — item-by-item scoring, 100 points |
| `answer-key/batches.md` | which key items belong to which batch (34 / 35 / 31) |
| `answer-key/canon.md` | what actually happened — written before the retellings |
| `answer-key/corruption-map.md` | every planted error, and which narrator carries it |
| `harness/` | the administration scripts and the long-variant protocol |
| `results.md` | short-variant results, four models × three administrations |

The answer key is secret from the system under test. It is in the repository because the test is
published for others to run, not because a model should ever see it.

## The two sizes, and why

**Short (~37,000 words).** Fits in one context. Measures synthesis with nothing in the way.
Administered three ways: everything at once, the documents one after another, and the documents
with unrelated reading interleaved and the reader replaced partway through.

**Long (~1.5M tokens).** Deliberately larger than any context window. Eight retellings sit inside
62,000-word documents; four noise documents of ~220,000 words each sit between them. No model can
hold it, so it must be read by a chain of fresh readers handing written notes forward — real
compaction, not simulated. This measures what survives.

## Scoring

Seven sections, 100 points. Sections C and E are exact-match. Some items are abstention items:
the correct answer is that the sources do not settle the question, and a confident answer scores
zero. Asserting a planted error as fact costs points; hedging it ("one source wrongly claims…")
does not. Every cell is scored twice by independent judges and both totals are reported.

## How to run the test

The rule that makes results comparable: **the system under test gets the material and the
questions, and nothing else.** No answer key, no canon, no corruption map, no file listing that
reveals which documents are distractors. Deliver documents in the prescribed order, one read each,
and never let the model go back to a source after the questions arrive.

### Short variant — three administrations

Same material and same questions each time; only the delivery changes.

1. **single** — give it `test-input/bundle-single.md` (all twenty-four retellings followed by the
   questions) in one shot. Ask for the answer sheet back.
2. **sequential** — give it `test-input/retellings/r01.md`, then `r02.md`, … `r24.md`, one at a
   time, asking for a one-line acknowledgement after each. Then `test-input/questions.md`.
3. **noisy** — as sequential, but after each retelling deliver the next distractor from
   `distractors/ORDER.md` and ask its one-line surface question. Replace the reader twice (after
   r08 and after r16): the outgoing reader writes retention notes, and a **fresh** instance starts
   from those notes alone. That handoff is the compaction.

The answer sheet is written in three parts (Section A stories 1–4; Section A stories 5–8 plus
Section B; Sections C–G) — a single write of the whole sheet tends to get truncated.

### Long variant — the part that does not fit

Material: the same twenty-four retellings, but eight of them delivered inside their
`test-input/long/rNN-long.md` wrappers, with `distractors/long/L1…L4.md` after r06, r12, r18 and
r24 and the short distractors in `ORDER.md` between the rest. Roughly 1.5M tokens.

Plan the reading with `harness/plan_segments.py`, which walks the fixed order and cuts a new
segment every time a token budget would be exceeded, splitting documents mid-file where a cut
falls inside one:

    python3 harness/plan_segments.py --root v3 --model <name> --budget 110000 \
        --out runs/<name>/long-notes/ingest/plan.json
    python3 harness/plan_segments.py --root v3 --model <name> --out … --render 1

Then, per segment: run `harness/split_big_reads.py` on the rendered file (a single Read call
cannot return more than ~25k tokens, and a reader's own notes are few lines of enormous length —
splitting on line count alone is not enough), hand the file to a fresh reader, and step the chain
with `harness/ingest_step.sh <model> <segment> <transcript> <budget>`, which captures the
transcript, verifies it, checks that every prescribed span actually came back, and renders the
next segment.

Two modes, and the comparison between them is the point:

- **long-notes** — ingest once, then answer each question batch from the final notes alone. One
  expensive pass; every later question is cheap.
- **long-reread** — re-read the whole corpus for each batch, with that batch's questions in hand
  from the first page. Three expensive passes, but the reading is targeted rather than blind.
  Use `harness/reread_step.sh <model> <batch> <segment> <transcript> <budget>`.

### Scoring

Give a judge `answer-key/answers-and-scoring.md` and the run's answers — and nothing else. Score
every item; exact-match sections take no near misses; abstention items score only when the run
actually abstains; subtract for planted errors asserted as fact, but not for hedged mentions.
Section A is credited wherever a keyed fact appears among the run's eight reconstructions, since
the run chooses its own partition, but never from another section.

Judge every cell **twice, independently**, and report both totals. Across the twelve short-variant
cells the two judges differed by 0–8 points out of 100, which is the honest precision of a single
number here.

### Running it by hand, with no scripts at all

Nothing here requires the harness. The scripts exist to make a 1.5M-token run auditable; a person
with a chat window can reproduce the short variant in an afternoon and the long variant over a few
sittings.

**What the model may see:** the retellings, the distractors, and the question sheet. **What it may
never see:** anything in `answer-key/`, and any file listing that reveals which documents are
distractors. Do not tell it how many documents are noise, or that the long documents contain
anything hidden.

**Short variant, by hand:**

1. *single* — paste the whole of `test-input/bundle-single.md` into one message. It ends with the
   questions. Ask for the answer sheet back. One message in, one answer out.
2. *sequential* — paste `test-input/retellings/r01.md`, ask only for a one-line acknowledgement,
   and repeat for r02 … r24 in order, one message each. Then paste `test-input/questions.md`.
3. *noisy* — the same, but after each retelling paste the next distractor named in
   `distractors/ORDER.md` and ask its one-line question. After r08 and again after r16, ask for
   "the notes you would need to answer detailed questions later about everything you have read
   except the unrelated documents", copy those notes out, **start a brand-new chat**, paste the
   notes as its first message, and carry on from the next retelling. Those two restarts are the
   point of this administration: they are the compaction.

Ask for the answer sheet in three messages (Section A stories 1–4; Section A stories 5–8 plus
Section B; Sections C–G). Asking for all 100 points in one reply tends to get it truncated.

**Long variant, by hand:** the same shape, with two changes. Deliver r03, r06, r09, r12, r15, r18,
r21 and r24 as their `test-input/long/rNN-long.md` versions — each a ~62,000-word document with the
retelling buried inside — and after r06, r12, r18 and r24 deliver one of `distractors/long/L1..L4.md`.
Start a fresh chat whenever the current one is nearly full, carrying only the notes across. Expect
twenty or more restarts. Then answer the three batch files instead of the single question sheet.

For the second long condition, do the whole reading again from the start for each batch, but show
the model that batch's questions **before** it reads anything. That is the only difference, and in
this run it doubled two models' scores and did nothing for the third.

**Scoring by hand:** open `answer-key/answers-and-scoring.md`, go item by item, and award each
point only where the criterion is actually met — exact-match items take no near misses, abstention
items score only if the answer abstains, and every planted error asserted as fact costs points
(hedged mentions do not). If you can, have two people score it independently and report both
totals; across the twelve cells here the two judges differed by 0–8 points out of 100, which is the
honest precision of any single number.

### Verifying a run before you believe it

`harness/read_coverage.py` compares what each segment prescribed against the spans the reader
actually received, and `v2/harness/verify_transcript.py` checks that the reader opened only what it
was given. Both exist because runs failed silently without them: a prescribed read that exceeded
the tool's limit cost one chain its entire carried memory, and one model skipped a read containing
scored material and then reported the segment complete. `harness/PROTOCOL-LONG.md` records those
failures, what was lost, and what was re-run.
