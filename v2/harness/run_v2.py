#!/usr/bin/env python3
"""Run one cell (model x mode) of the synthesis test and write the evidence files.

Modes:
  single      One request: every retelling, then the questions, in one user message.
  sequential  One turn per retelling (12), each acknowledged, then one questions turn.
  noisy       Retelling turn + noise-document turn per retelling, with a simulated
              compaction (notes written by the model, then history replaced by those
              notes) after retellings 4, 8 and 12, then the questions turn.

`--dry-run` never calls messages.create; it only counts inputs and estimates or counts
tokens per file. Without credentials (no ANTHROPIC_API_KEY, directly or via ../../.env),
the process always exits 2 after printing that preview, whether or not --dry-run was given,
since there is no way to do a real run either way.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from common import (
    CHARS_PER_TOKEN_ESTIMATE,
    REQUEST_TIMEOUT_S,
    call_with_retries,
    cost_usd,
    count_tokens_for_text,
    extract_text,
    load_dotenv,
    load_prices,
    read_text_files_sorted,
    repo_root_from,
    sum_usage,
    usage_to_dict,
)
from prompts import (
    COMPACTION_ACK,
    COMPACTION_MESSAGE,
    SYSTEM_PROMPT,
    compacted_notes_message,
    noise_message,
    questions_message,
    sequential_retelling_message,
    single_user_message,
)

HARNESS_DIR = Path(__file__).resolve().parent
V2_DIR = HARNESS_DIR.parent
COMPACTION_POINTS = {4, 8, 12}


@dataclass
class Inputs:
    retellings: list[tuple[str, str]]
    questions_text: str
    noise_docs: list[tuple[str, str]] = field(default_factory=list)
    noise_questions: dict[str, str] = field(default_factory=dict)  # noise filename -> its question


@dataclass
class RunOutcome:
    entries: list[dict]
    final_answer: str
    num_compactions: int


# --------------------------------------------------------------------------- input loading

NOISE_DOC_GLOB = "n[0-9]*.md"  # n01-....md .. n12-....md; excludes questions.md and any SOURCES.md
_NOISE_HEADER_RE = re.compile(r"^##\s+(?P<filename>\S+\.md)\s*$", re.MULTILINE)


def parse_noise_questions(text: str, noise_filenames: list[str]) -> dict[str, str]:
    """Map of {noise filename: its question}.

    Primary format: one "## <filename>" heading per noise doc, followed by a "**Q:** ..." line (an
    "**A:** ..." line may follow it too, for hand-checking the noise task; it is not read here).
    Falls back to pairing one non-empty, non-heading line per noise file, in order, for any other
    format, so an unrecognized questions.md still yields something rather than nothing.
    """
    questions: dict[str, str] = {}
    headers = list(_NOISE_HEADER_RE.finditer(text))
    if headers:
        for i, match in enumerate(headers):
            filename = match.group("filename")
            start = match.end()
            end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
            q_match = re.search(r"\*\*Q:\*\*\s*(.+)", text[start:end])
            if q_match:
                questions[filename] = q_match.group(1).strip()
        return questions

    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        line = re.sub(r"^(?:\d+[\.\)]|[-*])\s*", "", line)
        if line:
            lines.append(line)
    return dict(zip(noise_filenames, lines))


def load_inputs(retellings_dir: Path, questions_path: Path, noise_dir: Path, noise_questions_path: Path, mode: str) -> Inputs:
    retellings = read_text_files_sorted(retellings_dir, "*.md")
    questions_text = questions_path.read_text(encoding="utf-8") if questions_path.is_file() else ""

    noise_docs: list[tuple[str, str]] = []
    noise_questions: dict[str, str] = {}
    if mode == "noisy":
        noise_docs = read_text_files_sorted(noise_dir, NOISE_DOC_GLOB)
        if noise_questions_path.is_file():
            noise_filenames = [name for name, _ in noise_docs]
            noise_questions = parse_noise_questions(noise_questions_path.read_text(encoding="utf-8"), noise_filenames)

    return Inputs(retellings=retellings, questions_text=questions_text, noise_docs=noise_docs, noise_questions=noise_questions)


# --------------------------------------------------------------------------- one turn

def run_turn(
    client,
    model: str,
    system: str,
    history: list[dict],
    user_text: str,
    label: str,
    max_tokens: int,
    prices: dict,
    sleep=time.sleep,
) -> tuple[str, dict, list[dict]]:
    """Send one turn (full history + the new user message), log it, and return the new history."""
    messages = history + [{"role": "user", "content": user_text}]
    response, latency_s = call_with_retries(
        client, model=model, system=system, messages=messages, max_tokens=max_tokens, sleep=sleep
    )
    text = extract_text(response)
    usage = usage_to_dict(getattr(response, "usage", None))
    entry = {
        "turn": label,
        "request": {"system": system, "messages": messages},
        "response_text": text,
        "usage": usage,
        "cost_usd": cost_usd(usage, model, prices),
        "latency_s": latency_s,
    }
    new_history = messages + [{"role": "assistant", "content": text}]
    return text, entry, new_history


# --------------------------------------------------------------------------- modes

def run_single(client, model: str, inputs: Inputs, max_tokens: int, prices: dict, sleep=time.sleep) -> RunOutcome:
    user_text = single_user_message(inputs.retellings, inputs.questions_text)
    text, entry, _history = run_turn(client, model, SYSTEM_PROMPT, [], user_text, "single", max_tokens, prices, sleep)
    return RunOutcome(entries=[entry], final_answer=text, num_compactions=0)


def run_sequential(client, model: str, inputs: Inputs, max_tokens: int, prices: dict, sleep=time.sleep) -> RunOutcome:
    history: list[dict] = []
    entries: list[dict] = []
    total = len(inputs.retellings)

    for index, (_filename, text) in enumerate(inputs.retellings, start=1):
        msg = sequential_retelling_message(index, total, text)
        _, entry, history = run_turn(
            client, model, SYSTEM_PROMPT, history, msg, f"retelling-{index:02d}", max_tokens, prices, sleep
        )
        entries.append(entry)

    q_msg = questions_message(inputs.questions_text)
    final_text, entry, history = run_turn(client, model, SYSTEM_PROMPT, history, q_msg, "questions", max_tokens, prices, sleep)
    entries.append(entry)

    return RunOutcome(entries=entries, final_answer=final_text, num_compactions=0)


def run_noisy(client, model: str, inputs: Inputs, max_tokens: int, prices: dict, sleep=time.sleep) -> RunOutcome:
    history: list[dict] = []
    entries: list[dict] = []
    num_compactions = 0
    total = len(inputs.retellings)

    for index, (_filename, text) in enumerate(inputs.retellings, start=1):
        r_msg = sequential_retelling_message(index, total, text)
        _, entry, history = run_turn(
            client, model, SYSTEM_PROMPT, history, r_msg, f"retelling-{index:02d}", max_tokens, prices, sleep
        )
        entries.append(entry)

        if index - 1 < len(inputs.noise_docs):
            noise_name, noise_text = inputs.noise_docs[index - 1]
            question = inputs.noise_questions.get(noise_name, "What is this document about?")
            n_msg = noise_message(noise_text, question)
            _, entry, history = run_turn(
                client, model, SYSTEM_PROMPT, history, n_msg, f"noise-{index:02d}", max_tokens, prices, sleep
            )
            entries.append(entry)

        if index in COMPACTION_POINTS:
            notes_text, entry, history = run_turn(
                client, model, SYSTEM_PROMPT, history, COMPACTION_MESSAGE, f"compaction-{index:02d}",
                max_tokens, prices, sleep,
            )
            entries.append(entry)
            num_compactions += 1
            history = [
                {"role": "user", "content": compacted_notes_message(notes_text)},
                {"role": "assistant", "content": COMPACTION_ACK},
            ]

    q_msg = questions_message(inputs.questions_text)
    final_text, entry, history = run_turn(client, model, SYSTEM_PROMPT, history, q_msg, "questions", max_tokens, prices, sleep)
    entries.append(entry)

    return RunOutcome(entries=entries, final_answer=final_text, num_compactions=num_compactions)


MODE_RUNNERS = {"single": run_single, "sequential": run_sequential, "noisy": run_noisy}


# --------------------------------------------------------------------------- dry-run preview

def print_dry_run_report(inputs: Inputs, mode: str, client, model: str, has_credentials: bool) -> None:
    print(f"mode: {mode}")
    print(f"retellings: {len(inputs.retellings)}")
    if mode == "noisy":
        print(f"noise docs: {len(inputs.noise_docs)}")
        print(f"noise questions: {len(inputs.noise_questions)}")
    print(f"questions file: {'present' if inputs.questions_text else 'MISSING or empty'}")
    print()
    print(f"tokens per file (method; api requires credentials, else {CHARS_PER_TOKEN_ESTIMATE}-chars-per-token estimate):")

    counting_client = client if has_credentials else None
    files: list[tuple[str, str]] = list(inputs.retellings)
    if mode == "noisy":
        files += inputs.noise_docs
    files.append(("questions.md", inputs.questions_text))

    for filename, text in files:
        n, method = count_tokens_for_text(counting_client, model, text, has_credentials)
        print(f"  {filename}: {n} tokens ({method})")


# --------------------------------------------------------------------------- output writing

def write_outputs(
    out_dir: Path,
    outcome: RunOutcome,
    model: str,
    mode: str,
    started_at: datetime,
    finished_at: datetime,
    wall_clock_s: float,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = out_dir / "transcript.jsonl"
    with transcript_path.open("w", encoding="utf-8") as fh:
        for entry in outcome.entries:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    (out_dir / "answers.md").write_text(outcome.final_answer, encoding="utf-8")

    totals_usage = sum_usage([entry["usage"] for entry in outcome.entries])
    total_cost = sum(entry["cost_usd"] for entry in outcome.entries if entry["cost_usd"] is not None)

    run_info = {
        "model": model,
        "mode": mode,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "wall_clock_s": wall_clock_s,
        "num_requests": len(outcome.entries),
        "num_compactions": outcome.num_compactions,
        "totals": {**totals_usage, "cost_usd": total_cost},
    }
    (out_dir / "run.json").write_text(json.dumps(run_info, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- CLI

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one model x mode cell of the synthesis test.")
    parser.add_argument("--model", required=True, help="Model id to test.")
    parser.add_argument("--mode", required=True, choices=sorted(MODE_RUNNERS))
    parser.add_argument("--out", required=True, help="Directory to write transcript.jsonl, answers.md, run.json into.")
    parser.add_argument("--dry-run", action="store_true", help="Preview input counts and token estimates; make no real calls.")
    parser.add_argument("--max-tokens", type=int, default=16000)
    parser.add_argument("--prices", default=str(HARNESS_DIR / "prices.json"))
    parser.add_argument("--retellings-dir", default=str(V2_DIR / "test-input" / "retellings"))
    parser.add_argument("--questions", default=str(V2_DIR / "test-input" / "questions.md"))
    parser.add_argument("--noise-dir", default=str(V2_DIR / "noise"))
    parser.add_argument("--noise-questions", default=str(V2_DIR / "noise" / "questions.md"))
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    load_dotenv(repo_root_from(__file__) / ".env")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    has_credentials = bool(api_key)

    inputs = load_inputs(
        Path(args.retellings_dir), Path(args.questions), Path(args.noise_dir), Path(args.noise_questions), args.mode
    )
    prices = load_prices(Path(args.prices))

    client = None
    if has_credentials:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key, max_retries=0, timeout=REQUEST_TIMEOUT_S)

    print_dry_run_report(inputs, args.mode, client, args.model, has_credentials)

    if not has_credentials:
        print(
            "\nNo credentials found: set ANTHROPIC_API_KEY in the environment or in "
            f"{repo_root_from(__file__) / '.env'} to run for real.",
            file=sys.stderr,
        )
        return 2

    if args.dry_run:
        return 0

    started_at = datetime.now(timezone.utc)
    t0 = time.monotonic()
    try:
        outcome = MODE_RUNNERS[args.mode](client, args.model, inputs, args.max_tokens, prices)
    except RuntimeError as exc:
        print(f"run failed: {exc}", file=sys.stderr)
        return 1
    wall_clock_s = time.monotonic() - t0
    finished_at = datetime.now(timezone.utc)

    write_outputs(Path(args.out), outcome, args.model, args.mode, started_at, finished_at, wall_clock_s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
