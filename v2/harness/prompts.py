"""Every prompt string used by the harness, in one place.

Nothing here names a model, a product, or an agent. Templates are plain functions/strings so
run_v2.py and judge.py just fill them in and send them.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- system under test

SYSTEM_PROMPT = (
    "You are being tested on synthesis from partial, conflicting sources. You will be given a set "
    "of documents written by different narrators about related events. The narrators do not agree "
    "with each other on every point, and some of what any one of them says is wrong. Read everything "
    "you are given. When you are asked questions, answer only from the material provided, resolve "
    "conflicts where you can and say how you resolved them, say plainly when something cannot be "
    "determined from the sources, and show your work for any calculation."
)

# --------------------------------------------------------------------------- single mode

def single_user_message(retellings: list[tuple[str, str]], questions_text: str) -> str:
    """One message carrying every retelling, in order, followed by the questions."""
    blocks = []
    total = len(retellings)
    for index, (_filename, text) in enumerate(retellings, start=1):
        blocks.append(f"Retelling r{index:02d} of {total}.\n\n{text}")
    retellings_block = "\n\n---\n\n".join(blocks)
    return (
        f"You have been given {total} retellings of the same underlying events. Read all of them, "
        f"then answer the questions that follow.\n\n{retellings_block}\n\n---\n\n{questions_message(questions_text)}"
    )

# --------------------------------------------------------------------------- sequential mode

def sequential_retelling_message(index: int, total: int, text: str) -> str:
    """Per-retelling turn used by both sequential and noisy modes. `index` is 1-based."""
    return (
        f"Retelling r{index:02d} of {total} follows. Read it carefully; questions come after all "
        f"twelve. Reply with one line acknowledging receipt.\n\n{text}"
    )

# --------------------------------------------------------------------------- noisy mode

NOISE_INSTRUCTION = (
    "Unrelated task: read the following document and answer the question at the end in one sentence."
)


def noise_message(document_text: str, question_text: str) -> str:
    return f"{NOISE_INSTRUCTION}\n\n{document_text}\n\nQuestion: {question_text}"


COMPACTION_MESSAGE = (
    "Your context will be replaced. Write the notes you would need to answer detailed questions "
    "later about everything you have read in this conversation that is NOT the unrelated documents. "
    "Be exhaustive about names, dates, quantities, documents quoted, and conflicts between sources."
)


def compacted_notes_message(notes_text: str) -> str:
    """The single user message that replaces conversation history after a compaction turn."""
    return f"Notes from your earlier reading:\n{notes_text}"


COMPACTION_ACK = "Understood. I will rely on these notes for the rest of this conversation."

# --------------------------------------------------------------------------- questions

def questions_message(questions_text: str) -> str:
    return (
        "You have now been given all of the source material. Answer the following questions, in "
        f"order.\n\n{questions_text}"
    )

# --------------------------------------------------------------------------- judge

JUDGE_PROMPT_TEMPLATE = """You are scoring one run of a synthesis test against a fixed answer key. \
You are not the system being tested and must not be lenient with it.

Score every item in the answer key below against the run's answers, which follow it. Rules:
- Sections marked exact-match (typically C and E) must match the key's stated answer or tolerance \
exactly; do not award credit for a plausible-sounding but different number, date, or fraction.
- Checklist sections score each listed item 1 point if satisfied, 0 if not. No partial credit on any \
single item.
- Where the key marks an item as an abstention item (the correct answer is that something is not \
determinable from the sources), award the point only if the run's answer abstains accordingly; do \
not award it for a confident answer that happens to be unfalsifiable, and do not penalize honest \
hedging as though it were an error.
- Apply the key's corruption deductions: subtract for every planted error the run asserts as fact, \
per the key's list and any general deduction rule it states. A hedged mention of an error ("one \
source wrongly claims...") is not a deduction.
- Sum each section to its own total, then sum sections minus deductions to the grand total. Floor \
each section at 0 if the key says to.

ANSWER KEY:
{answer_key}

RUN'S ANSWERS:
{answers}

Respond with strict JSON and nothing else — no prose before or after, no markdown fence. The shape, \
using the key's own section labels as the keys of "sections":

{{"sections": {{"A": {{"items": [{{"id": "A1", "points": 0, "note": "why"}}], "total": 0}}, "...": \
{{"items": [], "total": 0}}}}, "deductions": [{{"reason": "why", "points": -1}}], "total": 0}}
"""


def judge_prompt(answer_key_text: str, answers_text: str) -> str:
    return JUDGE_PROMPT_TEMPLATE.format(answer_key=answer_key_text, answers=answers_text)
