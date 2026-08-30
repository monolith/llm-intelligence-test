# v3 long variant — administration protocol (bare models; the knowledge base is run elsewhere under the same protocol)

## Material
- Scored core: the 24 retellings (`v3/test-input/retellings/`, byte-identical to the short variant).
- Wrapped retellings: r03, r06, r09, r12, r15, r18, r21, r24 are each embedded as one chapter of a 50–100k-token assembled document (`v3/test-input/long/rNN-long.md`, built by `make_wrapper.py` from `gen_long_noise.py` filler; the needle position is recorded in `v3/test-input/long/MANIFEST.json`). The other 16 retellings are delivered as-is.
- Short noise: the 24 slots of `v3/distractors/ORDER.md`, one after each retelling, each with its surface question.
- Long noise: four generated documents of 200–300k tokens (`v3/distractors/long/L1..L4.md`, kinds ledger / transcript / gibberish / mixed), delivered after r06, r12, r18, r24, each with one surface question.
- Questions: three batches (`v3/test-input/batches/batch-1.md`, `-2`, `-3`; key split in `v3/answer-key/batches.md`).

## Delivery
Read-tool delivery, one prescribed Read per document (continuation reads of the same file count as one); no other tools; the transcript verifier checks the sequence. A fresh reader (real compaction) starts at every segment boundary; the previous reader writes retention notes first. Segment boundaries are planned by `plan_segments.py` from a token budget (default 110,000 tokens per reader including the carried notes), in the fixed ingest order r01 → slot 1 → r02 → … with L1–L4 after r06, r12, r18, r24. Documents longer than the remaining budget are split at line boundaries across readers (the Read tool's `offset`/`limit`), so a reader can end mid-document and the next one continues — compaction while reading. The plan is written per model to `v3/runs/<model>/long-notes/ingest/plan.json` and is identical for every model except for the measured size of each reader's own notes. The final notes file is the ingest notes.

## Two long modes
- **long-notes** — after ingest, each batch is answered by a fresh reader given ONLY the ingest notes (notes-4) and the batch's questions. Measures answering "later" from what was kept. Cost per batch ≈ notes + questions + answer.
- **long-reread** — each batch is answered by a fresh reader that reads ALL material again (the full segment schedule, no noise questions, no notes) and then the batch. Measures the bare model at full strength and full cost per batch.
A knowledge-base system run elsewhere should be measured the same way: ingest once (phase 1 cost), then three batches (per-batch cost and score), same files in the same order, same key, two independent judgings per batch.

## Scoring
Each batch is judged against its slice of the key (`answer-key/batches.md`), twice, by opus subagents; per-batch totals sum to the 100-point sheet. Reported per cell: ingest cost, per-batch cost, per-batch score, section profile, tool-use verification, judge spread.

## Cells
Four models × two long modes = 8 cells; batch-level results give 24 scored points per mode. n = 1 unless a specific difference needs confirming.

## Coverage note (2026-08-28)
Fable's monthly spend limit was reached during the run. Its completed cells are the short-variant `single` and `sequential`; `noisy` and the long variant were **not run** (not "failed to score"). Its long-variant ingest is banked through segment 2 and resumes from segment 3 whenever the limit is raised — the notes and verified transcripts are on disk. Every table must mark those cells "not run", never blank or zero.

## Ruling — long-reread is one pass per model, not three (2026-08-28)
The spec's per-batch re-read would run the full material three times per model. The re-read is the dominant cost of the whole suite, and repeating it buys no additional signal about the model: the same fresh reader reads the same bytes in the same order each time. So `long-reread` is administered as ONE chain per model, and the final reader answers all three batches in sequence, each batch written to its own answer file and judged separately against its slice of the key.

Cost is reported as: shared re-read cost (attributed once, and shown divided three ways where a per-batch number is needed, marked "shared"), plus each batch's own answer cost. Per-batch re-read costs are therefore correlated rather than independent — per-batch variance is understated, totals are exact. Every table carrying a per-batch re-read cost must carry that note.

## Defect and repair — the impossible read (2026-08-28)
`split_big_reads.py` split a prescribed Read by line count only. The Read tool refuses any slice over ~25k tokens, and a reader's own retention notes are few lines of enormous length: sonnet's `notes-11.md` was 276 lines and 30,086 tokens, so the prescribed read of it could never succeed. The reader was told to note an error and continue, so it continued — with no memory of segments 1–11. The transcript verifier passed the segment, because it checks which files were opened, not whether the read returned.

Found by scanning every captured transcript for the cap message. Damage, from `read_coverage.py` (new: compares each segment's prescribed line spans against the spans actually returned):

- **haiku seg11** — lost 700 of 800 lines of `notes-10.md`; the chain's notes fell from 12,384 words to 2,456 and never recovered.
- **sonnet seg12** — lost all of `notes-11.md`.
- Noise gaps in haiku seg3–7, seg11 and sonnet seg5 (L1/L2 documents, several thousand lines): the reader retried most and skipped some.
- **No scored content was lost in any live chain.** Every gap inside a wrapped document (`r09`, `r12`, `r15`) fell in filler; checked against the needle line span computed from `MANIFEST.jsonl`. `fable` seg2 did lose needle lines of `r06-long.md`, and fable's long variant is not run.

Repairs:
1. `split_big_reads.py` splits on measured **bytes** as well as lines (`--max-bytes 40000`, ≈15k tokens at the densest ratio observed); five tests in `tests/test_split_big_reads.py` cover long-line, many-line, contiguity, no-op, and unmeasurable-file cases.
2. `ingest_step.sh` now greps each captured transcript for the cap message, runs `read_coverage.py` for that segment, and prints a loud line if either fires. It also splits the next segment itself, so a rendered segment can no longer reach a reader unsplit.
3. Reader prompts now say: a read that fails because the slice is too large must be retried in halves until every part returns — never skipped. Same instruction to every model.
4. Invalidated segments were quarantined, not deleted, in `runs/<model>/long-notes/ingest/void-token-cap-notes-loss/`: sonnet from seg12, haiku from seg11 (13 segments of haiku work discarded). Both chains restart from the last segment whose carried notes were read in full.

The noise-document gaps in haiku's seg3–7 are left as they are and reported: they cost haiku some distraction load, which if anything helped it, and re-running them would discard sound scored content to fix an unscored one.

### Follow-up: the checker's own bug (2026-08-28)
`read_coverage.py` paired one Read call to one result at a time. A reader that issues several Reads in one turn gets its results back in order, so that pairing credited only the last call of each batch and reported material as unread that had been read — it accused fable's redone segment 2 of skipping 200 lines it had in fact read. Fixed to queue calls and pair them FIFO, with tests covering a parallel batch, a genuine gap, a cap refusal, and the retry-in-halves recovery.

Re-scanned with the fix, the remaining gaps across all chains are noise only: haiku seg3–7 and sonnet seg5 in `L1-ledger.md`, sonnet seg6 in `r09-long.md` filler, sonnet seg11 in `r15-long.md` filler. Every one checked against the needle line span; **no scored content is missing from any chain that will be scored.**

## Protocol compliance by model — an asymmetry to report, not to hide (2026-08-28)
The long ingest asks a reader to perform every numbered step, in order, and then write its notes. Compliance is not uniform across models, and the gap is large enough to be a result in its own right.

`haiku` has failed the protocol repeatedly in ways no other model has: paging a file with Bash instead of the Read tool; opening a side file the instructions never named; stopping short of the last prescribed read. The clearest instance is long segment 17, caught by `read_coverage.py`: it performed steps 1–21, skipped step 22 (`r15-long.md` lines 3501–3728), went straight to the final Write, and reported "22 of 22 steps completed". That skipped span contains the r15 needle — the only case in any live chain where a model's own behavior lost scored content — and its notes fell from 12,476 words to 1,573 in the same step. Re-run; the failed attempt is kept in `void-protocol-failures/`.

Because of these failures haiku has received procedural scaffolding the other models never needed: a smaller per-reader budget (70,000 tokens against 110,000), an explicit ban on Bash, an instruction to announce "step N of <total>" before each read, and now an instruction to confirm the last read before writing. From this point the reinforced prompt goes to every model, so later segments are administered identically; the earlier segments of the other chains ran under the plain prompt and needed nothing more.

Report this as measured: haiku required N re-runs to complete its chain, and the scaffolding that got it through is itself a cost of using the cheap model — someone running it unattended would have shipped the truncated notes without noticing.

## Fable's long chain is blocked at segment 8 (2026-08-30)
After the spend limit lifted, fable's long ingest resumed and ran cleanly through segment 7 (notes carried: 26,193 words, the largest of any chain). Every attempt at segment 8 dies with the same API error:

> Fable 5's safeguards flagged this message … Details: `[reasoning_extraction]`

Five attempts, failing at steps 4, 5, 1, 11 and 1 of the segment — so not a single offending document, and not one stochastic flag. What every attempt has in common is the read of fable's own carried notes. Two things in those notes are unlike anything the other three models wrote:

- **§0 "Where each retelling sat in the files"** and **§12 "Reading log"** enumerate the harness itself — file paths, generator seeds, "generated noise", chunk offsets, and the exact line ranges where the hidden retellings sit ("Retelling 12 at lines 4872–4941").
- The failing turns also show fable reasoning aloud about the conflict between the session's tool-policy reminder and this test's Read-only rule.

Either would plausibly read to a reasoning-extraction classifier as a model cataloguing the scaffolding it is running inside. Things tried, all failing: plain retry ×2; an instruction to keep between-step commentary to one line; delivery in 51 small reads instead of 22; delivering the notes truncated before §12.

**Status: fable long-variant = blocked, not "failed to score" and not "not run".** Its three short-variant cells are complete and scored (single 84/82, sequential 83/81, noisy 81/81). Segments 1–7 of the long ingest are on disk and verified; the chain resumes from segment 8 if the blocker clears.

The untried option is to rebuild the carried notes without the two harness-structure sections and restart from segment 8. That edits the system under test's own output, so it is not a call to make silently — it is recorded here as the open question, not taken.

### Correction to the fable diagnosis (2026-08-30)
The section above attributed fable's `reasoning_extraction` blocker to the harness-structure sections in its own carried notes. That was wrong, and the evidence that overturned it arrived immediately: fable's `long-reread` chain, which starts fresh with no carried notes at all, failed the same way — twice, at exactly step 5 of segment 1.

Step 5 was the first 800-line read of `r03-long.md`. The re-read chains were seeded by copying each model's `segment-1.md` from the original ingest, which had been rendered **before** the byte-aware splitter existed, so it still prescribed reads no single Read call can return. The likely mechanism is therefore: an impossible read fails → the model reasons at length about the tool error and how to recover → that reasoning trips the classifier. Fable is simply the model whose deliberation is long enough and self-referential enough to fire it.

That also explains the original segment-8 failures: they clustered around the reads of a 26,193-word notes file and the recovery attempts around them, not around any particular passage of content.

All four seeded `segment-1.md` files have been re-split (fable and opus went from 22 to 42 steps, sonnet likewise, haiku from 12 to 26). Whether fable's chain now runs is an open question at the time of writing; the earlier claim about its notes should not be relied on.

### Fable, final state: blocked in both long modes; trigger not isolated (2026-08-30)
Nine attempts across two chain types. `long-notes` died at segment 8 (steps 4, 5, 1, 11, 1); `long-reread` died at segment 1 (step 5, four times). Always the same API error, `[reasoning_extraction]`. What has been ruled out:

- **Its carried notes.** The re-read chain starts with no notes at all and fails identically.
- **Oversized reads.** Re-splitting the seeded segments (22 → 42 steps) changed nothing.
- **Long deliberation.** Instructing it to keep between-step remarks to one line changed nothing.
- **Reasoning about provenance.** Instructing it not to analyze how the documents were made or why they are in the set changed nothing.
- **The material itself.** A one-shot probe — fable reading the exact chunk it dies on (`r03-long.md` lines 1–300), nothing else in context — succeeded in six seconds. Its answer: "synthetic filler text … clearly built as test input for long-context LLM evaluation."

So the trigger needs the chain: the batch questions, a long list of prescribed reads, and this material together. The last probe suggests why — fable recognizes the corpus as an evaluation harness, and that recognition inside a long instruction-following context appears to be what fires. That is a hypothesis, not a finding; the trigger was not isolated further and further attempts were stopped on cost.

**Reported status: fable long-variant = blocked, both modes.** Its short variant is complete and scored (single 84/82, sequential 83/81, noisy 81/81). Long-notes segments 1–7 are verified on disk. No fable long number should be inferred from the other models.
