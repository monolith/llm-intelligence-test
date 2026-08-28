"""Tests for v3/harness/gen_long_noise.py.

Run with:
    v2/harness/.venv/bin/pytest v3/harness/tests/test_gen_long_noise.py -v

Covers the properties called out in the generator's spec:
  * determinism (same seed -> identical bytes)
  * word count within 2% of target
  * the collision list (built from v3/answer-key/canon.md) is respected,
    including a forced-collision unit test that proves the filtering
    mechanism works rather than relying on "unlikely by chance"
  * ledger totals actually add up
  * --question prints a question/answer pair that is exactly correct for
    the file that was actually generated
  * a 200,000-word generation completes in under 60 seconds
"""

from __future__ import annotations

import random
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parents[1]
V3_DIR = HARNESS_DIR.parent
SCRIPT = HARNESS_DIR / "gen_long_noise.py"
CANON = V3_DIR / "answer-key" / "canon.md"

sys.path.insert(0, str(HARNESS_DIR))
import gen_long_noise as gln  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def run_cli(args, cwd=None):
    cmd = [sys.executable, str(SCRIPT)] + args
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return result


def generate_file(tmp_path, kind, words, seed, name="out.md", collisions=None, question=False):
    out = tmp_path / name
    args = ["--kind", kind, "--words", str(words), "--seed", str(seed), "--out", str(out)]
    if collisions:
        args += ["--collisions", str(collisions)]
    if question:
        args.append("--question")
    result = run_cli(args)
    return out, result


def extract_numbers(text: str) -> set:
    clean = gln._clean_markdown(text)
    found = set()
    for m in re.finditer(r"\$\s?\d[\d,]*(?:\.\d+)?", clean):
        found.add(gln._norm_number(m.group(0)))
    for m in re.finditer(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b", clean):
        found.add(gln._norm_number(m.group(0)))
    for m in re.finditer(r"\b\d+\.\d+\b", clean):
        found.add(gln._norm_number(m.group(0)))
    return found


def extract_phrases(text: str) -> set:
    clean = gln._clean_markdown(text)
    word = r"[A-Z][A-Za-z']*"
    pattern = re.compile(rf"\b{word}(?:-{word})*(?:\s+(?:&\s+)?{word}(?:-{word})*){{0,4}}\b")
    found = set()
    for m in pattern.finditer(clean):
        phrase = " ".join(m.group(0).split())
        words = phrase.split()
        if len(words) == 1 and words[0].lower() in gln._STOPLIST:
            continue
        if len(phrase) < 3:
            continue
        found.add(phrase.lower())
    return found


LEDGER_LINE_RE = re.compile(
    r"^- \*\*(?P<date>\d{4}-\d{2}-\d{2})\*\* — of (?P<rest>.+); "
    r"day total \$(?P<day_total>\d+\.\d{2}); running total \$(?P<running>\d+\.\d{2})\.$"
)
SUBTOTAL_RE = re.compile(r"\(\$(?P<sub>\d+\.\d{2})\)")

ERROR_ROW_RE = re.compile(r"^\| `(?P<name>[A-Za-z]+)` \| (?P<code>\d+) \| .+ \|$")


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["ledger", "transcript", "gibberish", "codespec", "mixed"])
def test_determinism_same_seed_identical_bytes(tmp_path, kind):
    out1, _ = generate_file(tmp_path, kind, 2000, seed=42, name="a.md")
    out2, _ = generate_file(tmp_path, kind, 2000, seed=42, name="b.md")
    assert out1.read_bytes() == out2.read_bytes()


def test_determinism_different_seeds_diverge(tmp_path):
    out1, _ = generate_file(tmp_path, "mixed", 2000, seed=1, name="a.md")
    out2, _ = generate_file(tmp_path, "mixed", 2000, seed=2, name="b.md")
    assert out1.read_bytes() != out2.read_bytes()


# ---------------------------------------------------------------------------
# word count
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["ledger", "transcript", "gibberish", "codespec", "mixed"])
@pytest.mark.parametrize("target", [3000, 12000])
def test_word_count_within_two_percent(tmp_path, kind, target):
    out, _ = generate_file(tmp_path, kind, target, seed=5, name=f"{kind}_{target}.md")
    actual = len(out.read_text(encoding="utf-8").split())
    tolerance = target * 0.02
    assert abs(actual - target) <= tolerance, f"{kind} words={actual} target={target}"


# ---------------------------------------------------------------------------
# collision list respected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["ledger", "transcript", "gibberish", "codespec", "mixed"])
def test_collision_list_respected_against_real_canon(tmp_path, kind):
    assert CANON.exists(), f"expected canon fact sheet at {CANON}"
    out, _ = generate_file(tmp_path, kind, 15000, seed=17, name=f"{kind}.md", collisions=CANON)
    text = out.read_text(encoding="utf-8")

    collisions = gln.load_collisions(str(CANON))
    assert collisions["phrases"], "collision extraction found no proper-noun phrases in canon.md"
    assert collisions["numbers"], "collision extraction found no distinctive numbers in canon.md"

    num_hits = extract_numbers(text) & collisions["numbers"]
    phrase_hits = extract_phrases(text) & collisions["phrases"]
    assert not num_hits, f"{kind}: generated distinctive canon numbers: {num_hits}"
    assert not phrase_hits, f"{kind}: generated canon proper-noun phrases: {phrase_hits}"


def test_collision_list_respected_across_many_seeds(tmp_path):
    """Heavier sweep: several seeds x a larger word count, to catch rare
    collisions that a single small sample could miss by luck."""
    collisions = gln.load_collisions(str(CANON))
    for seed in range(5):
        buf_path = tmp_path / f"sweep_{seed}.md"
        gln.generate("mixed", 30000, seed, buf_path, str(CANON))
        text = buf_path.read_text(encoding="utf-8")
        num_hits = extract_numbers(text) & collisions["numbers"]
        phrase_hits = extract_phrases(text) & collisions["phrases"]
        assert not num_hits, f"seed={seed}: {num_hits}"
        assert not phrase_hits, f"seed={seed}: {phrase_hits}"


def test_forced_collision_is_actually_avoided(tmp_path):
    """Prove the filtering mechanism is load-bearing: build a fake collision
    file that blocks all but one of our own last names, then confirm
    safe_full_name() never returns a blocked surname across many draws."""
    blocked_name = gln.LAST_NAMES[3]
    fake_collisions_file = tmp_path / "fake_canon.md"
    fake_collisions_file.write_text(
        f"# Fake canon\n\n**{blocked_name}** is a name that must never appear.\n",
        encoding="utf-8",
    )
    collisions = gln.load_collisions(str(fake_collisions_file))
    assert blocked_name.lower() in collisions["phrases"]

    rng = random.Random(0)
    for _ in range(500):
        full = gln.safe_full_name(rng, gln.FIRST_NAMES, gln.LAST_NAMES, collisions)
        assert blocked_name.lower() not in full.lower().split()


def test_forced_collision_amount_is_avoided():
    """Same proof for safe_amount(): block a value inside the draw range
    and confirm it is never returned."""
    collisions = gln.empty_collisions()
    collisions["numbers"] = {1.50}
    rng = random.Random(0)
    for _ in range(2000):
        v = gln.safe_amount(rng, 1.0, 2.0, collisions, decimals=2)
        assert v != 1.50


def test_own_word_lists_do_not_exactly_match_canon_phrases():
    """Static safety net: none of the generator's own curated vocabulary
    is itself an exact (case-insensitive) canon proper noun."""
    collisions = gln.load_collisions(str(CANON))
    list_names = [
        "FIRST_NAMES", "LAST_NAMES", "PLACE_NAMES", "OBJECTS", "COLORS",
        "G_NOUNS", "G_NOUNS2", "BUSINESS_KINDS", "VENUE_KINDS",
    ]
    hits = []
    for lname in list_names:
        for value in getattr(gln, lname):
            if value.lower() in collisions["phrases"]:
                hits.append((lname, value))
    assert not hits, f"word list entries exactly match canon proper nouns: {hits}"


# ---------------------------------------------------------------------------
# ledger totals add up
# ---------------------------------------------------------------------------

def test_ledger_totals_add_up(tmp_path):
    out, _ = generate_file(tmp_path, "ledger", 20000, seed=9, name="ledger.md", collisions=CANON)
    text = out.read_text(encoding="utf-8")

    entry_lines = [line for line in text.splitlines() if LEDGER_LINE_RE.match(line)]
    assert len(entry_lines) >= 20, "expected a reasonable number of parsed ledger entries"

    running = 0.0
    for line in entry_lines:
        m = LEDGER_LINE_RE.match(line)
        rest = m.group("rest")
        day_total = float(m.group("day_total"))
        running_stated = float(m.group("running"))

        subtotals = [float(s) for s in SUBTOTAL_RE.findall(rest)]
        assert subtotals, f"no item subtotals parsed from: {line}"
        assert round(sum(subtotals), 2) == pytest.approx(day_total, abs=0.005), (
            f"item subtotals {subtotals} do not sum to day total {day_total} in: {line}"
        )

        running = round(running + day_total, 2)
        assert running == pytest.approx(running_stated, abs=0.005), (
            f"running total mismatch: computed {running} vs stated {running_stated} in: {line}"
        )


def test_ledger_dates_strictly_increase(tmp_path):
    out, _ = generate_file(tmp_path, "ledger", 8000, seed=9, name="ledger.md")
    text = out.read_text(encoding="utf-8")
    dates = [m.group("date") for line in text.splitlines() if (m := LEDGER_LINE_RE.match(line))]
    assert dates == sorted(dates)
    assert len(dates) == len(set(dates)), "ledger dates must be unique for the --question mode to be unambiguous"


# ---------------------------------------------------------------------------
# --question mode
# ---------------------------------------------------------------------------

def test_question_mode_appends_nothing_to_file(tmp_path):
    out_a, _ = generate_file(tmp_path, "gibberish", 2000, seed=3, name="a.md", question=False)
    out_b, result = generate_file(tmp_path, "gibberish", 2000, seed=3, name="b.md", question=True)
    assert out_a.read_bytes() == out_b.read_bytes()
    assert "Q:" in result.stdout and "A:" in result.stdout


def test_question_answer_correct_ledger(tmp_path):
    out, result = generate_file(tmp_path, "ledger", 4000, seed=11, name="ledger.md", question=True)
    text = out.read_text(encoding="utf-8")
    q_match = re.search(r"Q: What is the total on the ledger line dated (\S+)\?", result.stdout)
    a_match = re.search(r"A: \$(\S+)", result.stdout)
    assert q_match and a_match
    date, answer = q_match.group(1), a_match.group(1)

    matches = [line for line in text.splitlines() if LEDGER_LINE_RE.match(line) and f"**{date}**" in line]
    assert len(matches) == 1, f"expected exactly one ledger line dated {date}"
    m = LEDGER_LINE_RE.match(matches[0])
    assert m.group("running") == answer


def test_question_answer_correct_transcript(tmp_path):
    out, result = generate_file(tmp_path, "transcript", 4000, seed=11, name="transcript.md", question=True)
    text = out.read_text(encoding="utf-8")
    q_match = re.search(r"Q: Which speaker mentions (.+) first\?", result.stdout)
    a_match = re.search(r"A: (.+)", result.stdout)
    assert q_match and a_match
    obj, speaker = q_match.group(1), a_match.group(1)

    turn_re = re.compile(r"^\*\*(?P<speaker>[^:]+):\*\* (?P<body>.+)$")
    first_speaker = None
    for line in text.splitlines():
        m = turn_re.match(line)
        if m and obj in m.group("body"):
            first_speaker = m.group("speaker")
            break
    assert first_speaker == speaker


def test_question_answer_correct_gibberish(tmp_path):
    out, result = generate_file(tmp_path, "gibberish", 4000, seed=11, name="gibberish.md", question=True)
    text = out.read_text(encoding="utf-8")
    q_match = re.search(r"Q: What color is named in paragraph (\d+)\?", result.stdout)
    a_match = re.search(r"A: (\w+)", result.stdout)
    assert q_match and a_match
    pnum, color = q_match.group(1), a_match.group(1)

    para_re = re.compile(rf"^¶{pnum}\. (.+)$", re.M)
    m = para_re.search(text)
    assert m, f"paragraph marker ¶{pnum}. not found"
    para_text = m.group(1)
    colors_in_para = [c for c in gln.COLORS if c in para_text]
    assert colors_in_para == [color], f"expected exactly [{color!r}], found {colors_in_para}"


def test_question_answer_correct_codespec(tmp_path):
    out, result = generate_file(tmp_path, "codespec", 4000, seed=11, name="codespec.md", question=True)
    text = out.read_text(encoding="utf-8")
    q_match = re.search(r"Q: What HTTP status code is assigned to the `(\w+)` error in the spec\?", result.stdout)
    a_match = re.search(r"A: (\d+)", result.stdout)
    assert q_match and a_match
    name, code = q_match.group(1), a_match.group(1)

    rows = [m for line in text.splitlines() if (m := ERROR_ROW_RE.match(line)) and m.group("name") == name]
    assert len(rows) == 1
    assert rows[0].group("code") == code


def test_question_answer_correct_mixed(tmp_path):
    out, result = generate_file(tmp_path, "mixed", 6000, seed=21, name="mixed.md", question=True)
    assert "Q:" in result.stdout and "A:" in result.stdout
    # mixed just delegates to one of the four per-kind fact stores; a
    # non-empty, well-formed Q/A pair is the contract here.
    q_line = [l for l in result.stdout.splitlines() if l.startswith("Q:")][0]
    a_line = [l for l in result.stdout.splitlines() if l.startswith("A:")][0]
    assert len(q_line) > 5 and len(a_line) > 3


# ---------------------------------------------------------------------------
# no exact duplicate paragraphs / turns
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["transcript", "gibberish"])
def test_no_exact_duplicate_paragraphs(tmp_path, kind):
    out, _ = generate_file(tmp_path, kind, 15000, seed=13, name=f"{kind}.md")
    text = out.read_text(encoding="utf-8")
    paragraphs = [p for p in text.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    assert len(paragraphs) == len(set(paragraphs)), "found exact duplicate paragraphs"


# ---------------------------------------------------------------------------
# header format
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", ["ledger", "transcript", "gibberish", "codespec", "mixed"])
def test_header_marks_output_as_generated_noise(tmp_path, kind):
    out, _ = generate_file(tmp_path, kind, 1500, seed=1, name=f"{kind}.md")
    first_line = out.read_text(encoding="utf-8").splitlines()[0]
    pattern = rf"^# .+ — generated noise \({kind}, 1500 words, seed 1\)$"
    assert re.match(pattern, first_line), first_line


# ---------------------------------------------------------------------------
# CLI validation
# ---------------------------------------------------------------------------

def test_cli_rejects_bad_kind(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--kind", "nonsense", "--words", "100", "--seed", "1",
         "--out", str(tmp_path / "x.md")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_cli_rejects_zero_words(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--kind", "ledger", "--words", "0", "--seed", "1",
         "--out", str(tmp_path / "x.md")],
        capture_output=True, text=True,
    )
    assert result.returncode != 0


def test_works_without_collisions_argument(tmp_path):
    out, _ = generate_file(tmp_path, "gibberish", 1000, seed=1, name="nocoll.md", collisions=None)
    assert out.exists()
    assert len(out.read_text(encoding="utf-8").split()) > 0


# ---------------------------------------------------------------------------
# performance
# ---------------------------------------------------------------------------

def test_200k_words_completes_under_60_seconds(tmp_path):
    out = tmp_path / "big.md"
    start = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--kind", "mixed", "--words", "200000", "--seed", "42",
         "--out", str(out), "--collisions", str(CANON)],
        capture_output=True, text=True, timeout=60,
    )
    elapsed = time.perf_counter() - start
    assert result.returncode == 0, result.stderr
    assert elapsed < 60, f"200k-word generation took {elapsed:.2f}s"

    actual_words = len(out.read_text(encoding="utf-8").split())
    assert abs(actual_words - 200000) <= 200000 * 0.02

    print(f"\n200,000-word 'mixed' generation: {elapsed:.2f}s")
