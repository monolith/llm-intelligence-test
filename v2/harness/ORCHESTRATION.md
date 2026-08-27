# Orchestrated administration (no API key required)

The controller session runs each (model × mode) cell by dispatching subagents as the system under test. Same inputs, same order, every time.

**No tools.** The system under test is told to use no tools of any kind; retellings, noise documents and questions are delivered inline in the messages, never as file paths. After each cell the transcript is scanned for `tool_use` blocks; a run that used a tool is marked invalid and repeated. (Validation solves that had file tools scored 94–96: retrieval, not reading, was doing the work.)

**Delivery mechanism.** The harness caps Bash output at ~2 KB, so material is delivered through the Read tool (one prescribed Read per document; the single-mode bundle is 838 lines and returns whole). The transcript verifier's allowed list is the sequence of file paths.

**Inputs the system under test may see:** `v2/test-input/retellings/r01…r12.md`, `v2/test-input/questions.md`, and in `noisy` mode `v2/noise/n01…n12.md` + `v2/noise/questions.md`. Nothing under `v2/answer-key/` or `v2/originals/` — the subagent prompt forbids reading them and the transcript is checked afterwards for any such path.

**Cell output:** `v2/runs/<model>/<mode>/` — `answers.md` (written by the subagent itself), `transcript.jsonl` (reduced from the session's task-output JSONL by `capture_transcript.py`), `notes-after-r04.md` / `notes-after-r08.md` (noisy only), `score.json` + `score.md` (judge).

## Modes
- **single** — one dispatch: system-under-test instructions, then the twelve retellings and the questions inline; the answer sheet is returned as the reply (the controller writes it to `answers.md`).
- **sequential** — one dispatch with r01 and the instruction "acknowledge in one line; more retellings follow"; r02…r12 arrive as follow-up messages to the same subagent; then the questions message. No file reading of retellings: each retelling's text is inside the message.
- **noisy** — as sequential, but after each retelling a noise message follows: one public-domain excerpt (text inline) plus its one-line question. After r04 and after r08 the subagent is asked to write `notes-after-rNN.md` — "the notes you would need to answer detailed questions later about everything read so far except the unrelated documents" — and a **fresh subagent** of the same model is started whose first message is those notes verbatim followed by the next retelling. The final segment answers the questions.

## Judge
An opus subagent gets `v2/answer-key/answers-and-scoring.md` and one cell's `answers.md`, scores every item (exact match for C and E, yes/no per checklist item, abstention rule, corruption deductions) and writes `score.json` (strict schema) and `score.md`. Each cell is judged twice by independent judge subagents; the max difference is reported. Two cells are hand-scored by the controller for Cohen's κ.

## Repeatability caveats
Subagent sampling is not deterministic; the same cell can vary between runs. Report n per cell. Subagent contexts have no compaction of their own within a segment; the fresh-subagent handoff IS the compaction.

**Two more delivery facts (2026-08-27):** the Read tool returns very large files in parts — a continuation Read of the same file with an offset is one delivery, and the verifier collapses it. The Write tool refuses to overwrite a file the subagent has not read, so every cell directory must be EMPTY before dispatch (a stale `answers.md` makes the final Write fail silently while the model reports success).
