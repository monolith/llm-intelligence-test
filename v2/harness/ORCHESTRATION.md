# Orchestrated administration (no API key required)

The controller session runs each (model × mode) cell by dispatching subagents as the system under test. Same inputs, same order, every time.

**Inputs the system under test may see:** `v2/test-input/retellings/r01…r12.md`, `v2/test-input/questions.md`, and in `noisy` mode `v2/noise/n01…n12.md` + `v2/noise/questions.md`. Nothing under `v2/answer-key/` or `v2/originals/` — the subagent prompt forbids reading them and the transcript is checked afterwards for any such path.

**Cell output:** `v2/runs/<model>/<mode>/` — `answers.md` (written by the subagent itself), `transcript.jsonl` (reduced from the session's task-output JSONL by `capture_transcript.py`), `notes-after-r04.md` / `notes-after-r08.md` (noisy only), `score.json` + `score.md` (judge).

## Modes
- **single** — one dispatch: system-under-test instructions, then "read the twelve retelling files and the questions file, answer in `answers.md`".
- **sequential** — one dispatch with r01 and the instruction "acknowledge in one line; more retellings follow"; r02…r12 arrive as follow-up messages to the same subagent; then the questions message. No file reading of retellings: each retelling's text is inside the message.
- **noisy** — as sequential, but after each retelling a noise message follows: one public-domain excerpt (text inline) plus its one-line question. After r04 and after r08 the subagent is asked to write `notes-after-rNN.md` — "the notes you would need to answer detailed questions later about everything read so far except the unrelated documents" — and a **fresh subagent** of the same model is started whose first message is those notes verbatim followed by the next retelling. The final segment answers the questions.

## Judge
An opus subagent gets `v2/answer-key/answers-and-scoring.md` and one cell's `answers.md`, scores every item (exact match for C and E, yes/no per checklist item, abstention rule, corruption deductions) and writes `score.json` (strict schema) and `score.md`. Each cell is judged twice by independent judge subagents; the max difference is reported. Two cells are hand-scored by the controller for Cohen's κ.

## Repeatability caveats
Subagent sampling is not deterministic; the same cell can vary between runs. Report n per cell. Subagent contexts have no compaction of their own within a segment; the fresh-subagent handoff IS the compaction.
