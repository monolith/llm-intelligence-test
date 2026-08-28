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
