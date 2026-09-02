# The exact prompts — so the test can be repeated in any harness

Every run in this repository was administered by sending one of the prompts below to a fresh
model instance with file-reading and file-writing tools and nothing else. Paths are absolute
because the model reads files by path; substitute your own. Nothing here mentions the answer key,
the original stories, or which documents are noise — the model must never see those.

Two graders, each a fresh Opus instance given the judge prompt, scored every answer sheet
independently. Both totals are always reported.

---

## Short variant

### single — everything in one read

> You are taking a reading-comprehension and reasoning test. Rules that are part of the test: you
> read the material exactly once and use no other tools except writing your answers — no
> re-reading, no grep, no searching, no other files, no Bash, no subagents. Concretely: (1) use the
> Read tool on `<repo>/v3/test-input/bundle-single.md` (twenty-four retellings followed by the
> questions; about 1,400 lines). The Read tool returns large files in parts: when it tells you where
> it stopped, continue reading the SAME file from that offset until you reach the end —
> continuation reads count as your single read; never read it again afterwards. (2) After reading,
> answer every question in the questions section following its instructions exactly. Section A
> asks you to reconstruct each of the EIGHT original stories with no further cues — decide the
> eight-story partition yourself; then who, what happened, when, the quantities that matter, and the
> documents that bear on each, within the stated word range per story. For the rest: section by
> section, in order, using the question numbering; where sources conflict, resolve and say how;
> where the sources cannot settle a question, say "cannot be determined from the sources"; numeric
> answers in the requested format; show working for the math. (3) Save the answer sheet in THREE
> Write calls: `<run>/answers-part1.md` (Section A, stories 1–4), `<run>/answers-part2.md`
> (Section A, stories 5–8, and Section B), `<run>/answers-part3.md` (Sections C–G). None of these
> files exists yet. Your final reply to me must be one line: the three paths written and the number
> of questions answered.

### sequential — one document per read, in order

> You are taking a reading-comprehension and reasoning test delivered in parts. Rules that are part
> of the test: the material arrives as twenty-four separate documents that you read one at a time,
> in order, each with exactly one Read tool call (never Bash/cat); after each one write one line
> acknowledging it; you may not re-read any document, grep, search, open any other file, or use any
> other tool; complete every numbered step — skipping one invalidates the run. Start by reading your
> instruction file `<run>/instructions.md` (one Read call), then follow its 26 numbered steps
> exactly: 24 retellings, the questions file, then the answers written in three parts from memory —
> you cannot go back. Your final reply to me must be one line: the three paths written and the
> number of questions answered.

`instructions.md` lists the 24 retelling paths in order, then the questions file, then the three
answer-file paths. A copy is in every `runs/<model>/sequential/` directory.

### noisy — distractors interleaved, reader replaced twice

Three segments. Segment 1 and 2 end with the model writing retention notes; a **fresh instance**
starts the next segment from those notes alone. That handover is the compaction.

Segments 1 and 2:

> You are taking a reading-comprehension and reasoning test delivered in parts, with unrelated
> reading tasks mixed in. Rules that are part of the test: read each document exactly once with a
> single Read tool call (never Bash/cat), in the prescribed order, completing every numbered step —
> skipping one invalidates the run; never re-read, grep, search, open any other file, or use any
> other tool; after each retelling write one line acknowledging it; after each unrelated document
> answer its question in one sentence. Start by reading your instruction file
> `<run>/segment-N.md` (one Read call), then follow it exactly; its last step has you write
> retention notes with ONE Write call before your context is discarded — be exhaustive about
> everything in the retellings (not the unrelated documents). Your final reply to me must be one
> line: the notes path and an approximate word count (no tools for that).

Segment 3 (the final reader, who answers):

> You are finishing a reading-comprehension and reasoning test delivered in parts, with unrelated
> reading tasks mixed in. Previous readers read the first sixteen documents and left you notes;
> their context is gone. Rules that are part of the test: read each document exactly once with a
> single Read tool call (never Bash/cat), in the prescribed order, completing every numbered step —
> skipping one invalidates the run; never re-read, grep, search, open any other file, or use any
> other tool; after each retelling write one line acknowledging it; after each unrelated document
> answer its question in one sentence. Start by reading your instruction file `<run>/segment-3.md`
> (one Read call), then follow it exactly (its first step is the previous readers' notes; its later
> steps include the questions file and then the answers). Answer every question following the
> questions file's instructions exactly — Section A: decide the eight-story partition yourself —
> from the notes and what you read; you cannot go back. Save the answer sheet in THREE Write calls
> exactly as the instruction file names them. Your final reply to me must be one line: the three
> paths written and the number of questions answered.

The segment files follow `distractors/ORDER.md`: retelling, distractor with its one-line surface
question, retelling, distractor … with notes written after r08 and r16.

---

## Long variant

### read once, answer from notes — the ingest reader (every segment)

> You are the next reader in a chain ingesting a large body of material for a reading-comprehension
> and reasoning test; the previous reader left notes, and later readers will answer questions from
> the notes you leave.
>
> Your instruction file `<run>/ingest/segment-N.md` contains a numbered list of steps. Perform ALL
> of them, in order, none skipped — earlier attempts in this chain failed by skipping a step, which
> invalidates the whole run.
>
> ABSOLUTE RULES:
> - Use ONLY the Read tool for reading, with exactly the `offset` and `limit` each numbered step gives.
> - NEVER use Bash (no `sed`, `cat`, `head`, `tail`, `wc`) and never open a file the instructions do not name.
> - Never re-read a chunk and never skip one. Before each Read, state "step N of <total>" so you can see your own place.
> - The most common failure is stopping one read short of the end. Before the final Write step, state the number of the last read you performed and confirm it equals the last numbered read in the file. If it does not, go back and do the missing read first.
> - If a Read fails because the slice is too large, do NOT move on: retry the SAME span split in half (same file, same start, half the limit), then the second half, and keep halving until each part returns. Skipping a failed read loses that material permanently.
> - If a Read fails for any other reason, note it in one line and continue; never substitute another tool.
>
> Read the instruction file first (that Read is not one of the numbered steps), count the steps,
> then work through them all. After a retelling chunk write one line acknowledging it; after an
> unrelated document (period papers, stories, proofs, specifications, chatter, nonsense) answer its
> question in one sentence — fake proofs and code specifications are noise like any other; read
> them and answer.
>
> The final step tells you to write your retention notes: use ONE Write call — carry forward
> EVERYTHING from the previous notes (drop nothing) and add everything from the retellings you read
> (NOT the unrelated documents): every name and relationship, date, quantity, place, object, every
> document quoted (quote it), every conflict or oddity between or within sources. Exhaustive; no
> length limit; the next reader has no other memory.
>
> Your final reply to me must be one line: the notes path, steps completed out of the total, and an
> approximate word count (no tools for that).

Segment files are produced by `harness/plan_segments.py` (one per reader, cut at a token budget:
110,000 for Sonnet/Opus/Fable, 70,000 for Haiku, which could not complete larger ones) and
`harness/split_big_reads.py` (no single read over 300 lines or 40,000 bytes). Each segment's first
steps read the previous reader's notes.

### read once, answer from notes — the batch reader

> You are finishing a reading-comprehension and reasoning test. Earlier readers worked through a
> very large body of source material and left you their retention notes; their context is gone and
> you cannot see the sources themselves. You answer from the notes alone.
>
> Rules that are part of the test: use ONLY the Read tool, exactly twice — never Bash/cat, never
> grep or search, never open any other file:
> 1. Read `<run>/ingest/notes-<final>.md` — the previous readers' notes (it is long; continuation
>    Reads of that same file to finish it are fine and count as the same step).
> 2. Read `<repo>/v3/test-input/batches/batch-N.md` — your questions.
>
> Then answer every question, following that file's instructions exactly, from the notes alone —
> you cannot go back to the sources. Write the answer sheet with ONE Write call to
> `<run>/batch-N/answers.md`.
>
> Your final reply to me must be one line: the path written and the number of questions answered.

### re-read with the questions in hand — every segment

Identical to the ingest reader, with this inserted before the instruction file:

> FIRST, before anything else, read `<repo>/v3/test-input/batches/batch-N.md` — these are the
> questions this whole chain exists to answer. Keep them in mind for every document you read
> afterward: retain what bears on them, in detail, and let the rest go.

and the notes instruction softened to "carry forward everything in the previous notes that bears
on the questions, and add what you found." The final segment's reader is told to ignore the
notes-writing step and instead answer the batch and write `<run>/batch-N/answers.md`.

### one continuous session, own compaction

> You are taking a reading-comprehension and reasoning test. You will read a very large body of
> material in one sitting, and then answer questions about it. You cannot go back once you have
> moved on, and you may not write notes to a file during the reading — everything you carry forward
> must be carried in your own head.
>
> Your reading schedule is `<run>/schedule.md` — read it first (that Read is not one of the
> numbered steps), then perform ALL 533 numbered steps, in order, none skipped.
>
> RULES: Use ONLY the Read tool, with exactly the offset and limit each step gives. NEVER use Bash
> and never open a file the schedule does not name. Never re-read a chunk and never skip one.
> Before each Read, state "step N of 533" and nothing more. Keep every remark between steps to a
> single short line. If a Read fails because the slice is too large, retry the SAME span split in
> half, then the second half, until each part returns. Never skip it.
>
> The material is a mixture. Some documents are retellings of events in and around the Larrow
> Valley — that is what the questions will be about, so read those closely. Many others are
> unrelated: county papers, short stories, mathematical write-ups, software specifications,
> overheard conversation, and stretches of prose that carry no meaning. Where a step asks a
> question about one of those, answer it in one sentence and move on.
>
> AFTER the final numbered step, and only then: read `<repo>/v3/test-input/batches/batch-1.md` and
> answer every question in it, following that file's instructions exactly, from what you have read.
> Write your answers with ONE Write call to `<run>/round-0-answers.md`.

The 533-step schedule is the whole corpus in ingest order with no notes handover, produced by
`plan_segments.py --budget 100000000` and split as above. The session compacts on its own when it
fills; the raw transcript records each compaction.

---

## The judge

> You are scoring one run of a synthesis test against a fixed answer key. You are not the system
> being tested and must not be lenient with it.
>
> Read the answer key at `<repo>/v3/answer-key/answers-and-scoring.md` and the run's answers at
> `<run>/answers.md` (both may need more than one Read call; read them completely).
>
> Score every item in the answer key against the run's answers. Rules:
> - Sections marked exact-match (typically C and E) must match the key's stated answer or tolerance exactly; do not award credit for a plausible-sounding but different number, date, or fraction.
> - Checklist sections score each listed item 1 point if satisfied, 0 if not. No partial credit on any single item.
> - Where the key marks an item as an abstention item (the correct answer is that something is not determinable from the sources), award the point only if the run's answer abstains accordingly; do not award it for a confident answer that happens to be unfalsifiable, and do not penalize honest hedging as though it were an error.
> - Section A is credited wherever the content appears inside the run's eight reconstructions — the run chose its own partition of the stories, so look for each keyed fact anywhere in Section A, not only under the story number the key uses. Never credit Section A from material the run wrote in Sections B–G.
> - Apply the key's corruption deductions: subtract for every planted error the run asserts as fact, per the key's list and any general deduction rule it states. A hedged mention of an error ("one source wrongly claims...") is not a deduction.
> - Sum each section to its own total, then sum sections minus deductions to the grand total. Floor each section at 0 if the key says to.
>
> Write your scoring to `<run>/score.json` as strict JSON and nothing else — no prose, no markdown
> fence. The shape, using the key's own section labels as the keys of "sections":
> `{"sections": {"A": {"items": [{"id": "A1.1", "points": 0, "max": 1, "note": "why"}], "total": 0}, ...}, "deductions": [{"reason": "why", "points": -1}], "total": 0}`
>
> Then write a short human-readable companion to `<run>/score.md`: the per-section totals, the
> grand total, and a few lines on what the run got wrong.
>
> Your final reply to me must be one line: the grand total and the per-section totals.

For a batch of the long variant, the judge is additionally told which key items belong to that
batch (`answer-key/batches.md`) and to score only those. The second grader receives the identical
prompt with `score-2.json` / `score-2.md` as its outputs.

---

## What is deliberately absent from every prompt

- Any mention of the answer key, `canon.md`, or `corruption-map.md`.
- Any statement of how many documents are noise, or which.
- Any hint that the long documents contain something hidden.
- Any coaching on how to answer well (except the one warning about stopping a read early, which
  was added to every model's prompt after one model kept doing it).
