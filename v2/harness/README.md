# v2 test harness — direct API runner

Runs one (model x mode) cell of the v2 synthesis test as real Anthropic API calls from a single
Python process — no subagents. (A separate, complementary subagent-orchestrated administration
path is documented in `ORCHESTRATION.md`, next to this file; use whichever a given task calls for.)

## Setup

This host's system Python has no `ensurepip`, so the venv is created without pip and pip is
bootstrapped into it separately:

    python3 -m venv --without-pip .venv && curl -sSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3 - && .venv/bin/pip install anthropic pytest

If your Python already has a working `venv`+`ensurepip`, the plain form works too:

    python -m venv .venv && .venv/bin/pip install anthropic pytest

## Credentials

Put `ANTHROPIC_API_KEY=sk-...` in a `.env` file at the repo root (`llm-intelligence-test/.env`,
`KEY=value` lines, gitignored). `run_v2.py` and `judge.py` load it automatically. Without it:
`--dry-run` still prints the input counts and per-file token estimate, then the process exits 2 —
there is no credential-free way to do a real run, dry or not.

## Running the 12 cells

One cell:

    .venv/bin/python run_v2.py --model claude-sonnet-5 --mode single --out ../runs/claude-sonnet-5/single

All 12 (4 models x single/sequential/noisy):

    for m in claude-haiku-4-5 claude-sonnet-5 claude-opus-5 claude-fable-5; do for mode in single sequential noisy; do .venv/bin/python run_v2.py --model "$m" --mode "$mode" --out "../runs/$m/$mode"; done; done

Preview only (no calls made, regardless of credentials):

    .venv/bin/python run_v2.py --model claude-sonnet-5 --mode noisy --out /tmp/preview --dry-run

Each cell writes `transcript.jsonl` (one line per request: turn label, full request messages,
response text, usage, list-price cost, latency), `answers.md` (the final answer text), and
`run.json` (totals: tokens, cost, wall-clock, request and compaction counts).

**Compaction is simulated on a fixed schedule.** In `noisy` mode, after retellings 4, 8 and 12 the
harness sends a message asking the model to write the retention notes it would need later, then
throws away the real conversation history and replaces it with just those notes (as a user message)
plus a fixed acknowledgment. This stands in for a real context-window compaction event; it is not one.

## Judging

    .venv/bin/python judge.py --run ../runs/claude-sonnet-5/single --key ../answer-key/answers-and-scoring.md

Judges `answers.md` against the key twice (`--times`, default 2) at temperature 0, using
`claude-opus-5` by default (`--model` to override). Writes `score.json` (every judging, the first as
canonical, and the max absolute difference in total between judgings) and `score.md` (a table, one
column per judging).

## Building the report

    .venv/bin/python report.py --runs ../runs --out ../results.md

Reads every `<runs>/<model>/<mode>/{run.json,score.json}` it can find (model order: haiku, sonnet,
opus, fable; mode order: single, sequential, noisy) and writes one Markdown file with three tables
(total/100, section profile, tokens/cost/wall-clock/requests), a judge-stability line per judged run,
and a "Hand-scoring κ" section that reads `<runs>/kappa.json` if present, or a placeholder if not.
Cells with no run yet, or no score yet, render as `—` rather than failing.

## Tests

    .venv/bin/pytest -q

Everything is tested against a fake client — no network access and no credentials are ever needed
to run the suite.
