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

## Running it yourself

The short variant needs only `test-input/`. For the long variant see
`harness/PROTOCOL-LONG.md`, which documents the segment schedule, the delivery rules, the
verification steps, and the failures found while running it — including the ones caused by the
harness rather than the models.
