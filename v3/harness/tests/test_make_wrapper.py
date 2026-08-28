"""Tests for make_wrapper.py -- the long-variant wrapper-splice tool.

Covers: determinism, byte-identical single-occurrence embedding of the
retelling, the "never first or last chapter" placement guarantee, chapter
word-count balance, collision-checked title generation, --verify, and a
performance bound on a 150,000-word filler.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

import make_wrapper as mw

CHAPTER_RE = re.compile(r"^## Chapter (\d+) — (.*)$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Fixture helpers -- self-contained synthetic inputs, shaped like the real
# thing but independent of any repo content so the tests don't drift if the
# real retellings or generator change.
# ---------------------------------------------------------------------------
def make_retelling_text(number: int = 1, title: str = "A Made-Up Witness, recorded 1979") -> str:
    heading = f"# Retelling {number:02d} — {title}"
    note = "*Framing note: transcribed from a tape, kept in the speaker's own words.*"
    paragraphs = [
        f"This is paragraph {i} of the scored retelling body, with enough ordinary "
        f"words in it to make a believable paragraph of prose about a small "
        f"disputed matter from long ago, paragraph number {i} of the set."
        for i in range(1, 21)
    ]
    return "\n\n".join([heading, note, *paragraphs]) + "\n"


def make_filler_text(num_paragraphs: int, words_per_paragraph: int = 50) -> str:
    """Plain markdown paragraphs, deliberately free of any '## Chapter' lines
    of its own, so tests can parse the assembled output's headings
    unambiguously.
    """
    paragraphs = []
    for i in range(num_paragraphs):
        words = " ".join(f"filler{(i * words_per_paragraph + j) % 900}" for j in range(words_per_paragraph))
        paragraphs.append(f"Paragraph {i}: {words}.")
    return "\n\n".join(paragraphs) + "\n"


def extract_outer_chapters(document: str):
    """Split an assembled document into (num, title, body) using the outer
    '## Chapter N — Title' headings. Only valid when the filler used to build
    the document contains no '## Chapter' lines of its own.
    """
    matches = list(CHAPTER_RE.finditer(document))
    chapters = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(document) - len("*End of document.*")
        body = document[start:end].strip()
        chapters.append((int(m.group(1)), m.group(2), body))
    return chapters


@pytest.fixture
def retelling_file(tmp_path):
    path = tmp_path / "r01-a-made-up-witness.md"
    path.write_text(make_retelling_text(), encoding="utf-8")
    return path


@pytest.fixture
def filler_file(tmp_path):
    path = tmp_path / "filler.md"
    path.write_text(make_filler_text(num_paragraphs=60, words_per_paragraph=40), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_determinism_same_seed_same_bytes(tmp_path, retelling_file, filler_file):
    out1 = tmp_path / "out1.md"
    out2 = tmp_path / "out2.md"
    r1 = mw.build_wrapper(retelling_file, filler_file, out1, seed=42, chapter_words=300, title="Doc")
    r2 = mw.build_wrapper(retelling_file, filler_file, out2, seed=42, chapter_words=300, title="Doc")

    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")
    r1.pop("out")
    r2.pop("out")
    assert r1 == r2


def test_different_seed_can_change_layout(tmp_path, retelling_file, filler_file):
    out1 = tmp_path / "out1.md"
    out2 = tmp_path / "out2.md"
    r1 = mw.build_wrapper(retelling_file, filler_file, out1, seed=1, chapter_words=300, title="Doc")
    r2 = mw.build_wrapper(retelling_file, filler_file, out2, seed=2, chapter_words=300, title="Doc")
    # Not a strict guarantee for every possible seed pair, but true for this
    # fixture, and demonstrates the seed actually drives assembly.
    assert out1.read_text(encoding="utf-8") != out2.read_text(encoding="utf-8")
    assert r1["retelling_chapter"] != r2["retelling_chapter"]


# ---------------------------------------------------------------------------
# Byte-identical, exactly-once embedding
# ---------------------------------------------------------------------------
def test_retelling_embedded_byte_identical_exactly_once(tmp_path, retelling_file, filler_file):
    out = tmp_path / "out.md"
    mw.build_wrapper(retelling_file, filler_file, out, seed=7, chapter_words=250, title="Doc")

    document = out.read_text(encoding="utf-8")
    retelling_text = retelling_file.read_text(encoding="utf-8")
    assert document.count(retelling_text) == 1


def test_retelling_word_span_matches_embedded_text(tmp_path, retelling_file, filler_file):
    out = tmp_path / "out.md"
    result = mw.build_wrapper(retelling_file, filler_file, out, seed=13, chapter_words=250, title="Doc")

    document = out.read_text(encoding="utf-8")
    retelling_text = retelling_file.read_text(encoding="utf-8")
    start, end = result["retelling_word_span"]

    all_words = document.split()
    retelling_words = retelling_text.split()
    assert end - start == len(retelling_words)
    assert all_words[start:end] == retelling_words


# ---------------------------------------------------------------------------
# Never first or last chapter
# ---------------------------------------------------------------------------
def test_retelling_never_first_or_last_across_many_seeds(tmp_path, retelling_file, filler_file):
    for seed in range(60):
        out = tmp_path / f"out_{seed}.md"
        result = mw.build_wrapper(retelling_file, filler_file, out, seed=seed, chapter_words=300, title="Doc")
        assert result["retelling_chapter"] != 1
        assert result["retelling_chapter"] != result["chapters"]
        assert 1 < result["retelling_chapter"] < result["chapters"]


def test_retelling_never_first_or_last_with_minimal_two_chapter_filler(tmp_path, retelling_file):
    # Small enough that the filler can only be split into the minimum of two
    # chapters -- the retelling must land in the single strictly-interior slot.
    filler_path = tmp_path / "tiny_filler.md"
    filler_path.write_text(make_filler_text(num_paragraphs=2, words_per_paragraph=20), encoding="utf-8")
    out = tmp_path / "out.md"

    result = mw.build_wrapper(retelling_file, filler_path, out, seed=0, chapter_words=1000, title="Doc")

    assert result["chapters"] == 3
    assert result["retelling_chapter"] == 2


def test_single_paragraph_filler_raises_clear_error(tmp_path, retelling_file):
    filler_path = tmp_path / "one_paragraph.md"
    filler_path.write_text("Just one paragraph, nothing else here at all.", encoding="utf-8")
    out = tmp_path / "out.md"

    with pytest.raises(ValueError, match="too few paragraphs"):
        mw.build_wrapper(retelling_file, filler_path, out, seed=0, chapter_words=100, title="Doc")


# ---------------------------------------------------------------------------
# Chapter word-count balance
# ---------------------------------------------------------------------------
def test_filler_chapter_word_counts_within_25_percent_of_target(tmp_path, retelling_file, filler_file):
    chapter_words = 300
    out = tmp_path / "out.md"
    result = mw.build_wrapper(retelling_file, filler_file, out, seed=5, chapter_words=chapter_words, title="Doc")

    document = out.read_text(encoding="utf-8")
    chapters = extract_outer_chapters(document)
    assert len(chapters) == result["chapters"]

    lo, hi = chapter_words * 0.75, chapter_words * 1.25
    for num, _title, body in chapters:
        if num == result["retelling_chapter"]:
            continue
        word_count = len(body.split())
        assert lo <= word_count <= hi, f"chapter {num} has {word_count} words, target {chapter_words}"


def test_balanced_chapter_split_preserves_all_paragraphs_in_order():
    paragraphs = [f"para{i} " + "w" * (i % 5 + 1) for i in range(40)]
    chapters = mw.balanced_chapter_split(paragraphs, chapter_words=50, min_chapters=2)

    flattened = [p for group in chapters for p in group]
    assert flattened == paragraphs
    assert all(len(group) > 0 for group in chapters)
    assert len(chapters) >= 2


# ---------------------------------------------------------------------------
# Collision-checked titles
# ---------------------------------------------------------------------------
def test_generated_titles_avoid_collision_list(tmp_path):
    forbidden_words = ["quiet", "ledger", "steady"]
    assert set(forbidden_words) <= set(mw.TITLE_ADJECTIVES) | set(mw.TITLE_NOUNS)

    collisions_path = tmp_path / "collisions.txt"
    collisions_path.write_text("\n".join(forbidden_words), encoding="utf-8")
    forbidden_blob = mw.load_collisions(collisions_path)

    import random

    rng = random.Random(3)
    titles = [mw.generate_title(rng, forbidden_blob) for _ in range(200)]
    for title in titles:
        low = title.lower()
        for word in forbidden_words:
            assert re.search(rf"\b{word}\b", low) is None


def test_collision_check_is_load_bearing_not_incidental():
    """Same seed, same draws, but with no collisions file the forbidden
    words do turn up -- proving the check above actually filters something
    rather than never being triggered."""
    import random

    rng = random.Random(3)
    titles = [mw.generate_title(rng, "") for _ in range(200)]
    low_titles = [t.lower() for t in titles]
    assert any(re.search(r"\bquiet\b", t) for t in low_titles)


def test_collisions_applied_end_to_end_in_build(tmp_path, retelling_file, filler_file):
    collisions_path = tmp_path / "collisions.txt"
    collisions_path.write_text("quiet\nledger\nsteady\nbrief\nworn\n", encoding="utf-8")
    out = tmp_path / "out.md"

    mw.build_wrapper(
        retelling_file, filler_file, out, seed=9, chapter_words=300, title="Doc",
        collisions_path=collisions_path,
    )
    document = out.read_text(encoding="utf-8").lower()
    for heading_line in re.findall(r"^## chapter \d+ — .*$", document, re.MULTILINE):
        for word in ("quiet", "ledger", "steady", "brief", "worn"):
            assert re.search(rf"\b{word}\b", heading_line) is None


# ---------------------------------------------------------------------------
# Heading / title-line handling
# ---------------------------------------------------------------------------
def test_extract_retelling_heading_text():
    text = "# Retelling 03 — Someone Notable, recorded 2001\n\n*note*\n\nBody.\n"
    assert mw.extract_retelling_heading_text(text) == "Retelling 03 — Someone Notable, recorded 2001"


def test_retelling_chapter_heading_uses_retellings_own_title_and_keeps_body_intact(tmp_path, retelling_file, filler_file):
    out = tmp_path / "out.md"
    result = mw.build_wrapper(retelling_file, filler_file, out, seed=2, chapter_words=300, title="Doc")

    document = out.read_text(encoding="utf-8")
    chapters = extract_outer_chapters(document)
    retelling_chapter = next(c for c in chapters if c[0] == result["retelling_chapter"])
    _num, heading_title, body = retelling_chapter

    retelling_text = retelling_file.read_text(encoding="utf-8")
    expected_heading = mw.extract_retelling_heading_text(retelling_text)
    assert heading_title == expected_heading
    # The retelling's own '# Retelling ...' line and framing note stay inside the body.
    assert body.startswith("# Retelling 01 —")
    assert "*Framing note:" in body


# ---------------------------------------------------------------------------
# Document framing (header / footer)
# ---------------------------------------------------------------------------
def test_header_and_footer_present(tmp_path, retelling_file, filler_file):
    out = tmp_path / "out.md"
    result = mw.build_wrapper(retelling_file, filler_file, out, seed=4, chapter_words=300, title="My Title")

    document = out.read_text(encoding="utf-8")
    lines = document.splitlines()
    assert lines[0] == f"# My Title — assembled document ({result['words']} words; seed 4)"
    assert document.rstrip().endswith("*End of document.*")


# ---------------------------------------------------------------------------
# --verify
# ---------------------------------------------------------------------------
def test_verify_finds_retelling_and_reports_chapter(tmp_path, retelling_file, filler_file):
    out = tmp_path / "out.md"
    result = mw.build_wrapper(retelling_file, filler_file, out, seed=11, chapter_words=300, title="Doc")

    verify_result = mw.verify_wrapper(out, retelling_file)
    assert verify_result["verified"] is True
    assert verify_result["occurrences"] == 1
    assert verify_result["chapter"] == result["retelling_chapter"]


def test_verify_reports_not_verified_when_retelling_absent(tmp_path, filler_file, retelling_file):
    out = tmp_path / "out.md"
    out.write_text(mw.read_exact(filler_file), encoding="utf-8")

    verify_result = mw.verify_wrapper(out, retelling_file)
    assert verify_result["verified"] is False
    assert verify_result["occurrences"] == 0
    assert verify_result["chapter"] is None


def test_verify_reports_not_verified_when_retelling_duplicated(tmp_path, retelling_file, filler_file):
    out = tmp_path / "out.md"
    mw.build_wrapper(retelling_file, filler_file, out, seed=6, chapter_words=300, title="Doc")

    # Splice in a second, duplicate copy of the retelling.
    retelling_text = retelling_file.read_text(encoding="utf-8")
    document = out.read_text(encoding="utf-8")
    out.write_text(document + "\n\n" + retelling_text, encoding="utf-8")

    verify_result = mw.verify_wrapper(out, retelling_file)
    assert verify_result["verified"] is False
    assert verify_result["occurrences"] == 2


# ---------------------------------------------------------------------------
# CLI (main())
# ---------------------------------------------------------------------------
def test_cli_build_then_verify(tmp_path, retelling_file, filler_file, capsys):
    out = tmp_path / "out.md"
    exit_code = mw.main([
        "--retelling", str(retelling_file),
        "--filler", str(filler_file),
        "--out", str(out),
        "--seed", "21",
        "--chapter-words", "300",
        "--title", "CLI Doc",
    ])
    assert exit_code == 0
    build_stdout = capsys.readouterr().out
    build_json = json.loads(build_stdout)
    assert set(build_json) == {"out", "words", "chapters", "retelling_chapter", "retelling_word_span"}
    assert out.exists()

    exit_code = mw.main(["--verify", str(out), "--retelling", str(retelling_file)])
    assert exit_code == 0
    verify_stdout = capsys.readouterr().out
    verify_json = json.loads(verify_stdout)
    assert verify_json["verified"] is True
    assert verify_json["chapter"] == build_json["retelling_chapter"]


def test_cli_missing_required_args_exits_nonzero(capsys):
    with pytest.raises(SystemExit) as excinfo:
        mw.main(["--retelling", "x.md"])
    assert excinfo.value.code != 0


def test_cli_verify_without_retelling_exits_nonzero(tmp_path):
    out = tmp_path / "out.md"
    out.write_text("anything", encoding="utf-8")
    with pytest.raises(SystemExit) as excinfo:
        mw.main(["--verify", str(out)])
    assert excinfo.value.code != 0


def test_cli_chapter_words_default_is_2000():
    parser = mw.build_parser()
    args = parser.parse_args(["--retelling", "r.md", "--filler", "f.md", "--out", "o.md", "--seed", "1"])
    assert args.chapter_words == 2000


# ---------------------------------------------------------------------------
# Performance: 150,000-word filler wraps in < 10s
# ---------------------------------------------------------------------------
def test_150000_word_filler_wraps_quickly(tmp_path, retelling_file):
    words_per_paragraph = 40
    num_paragraphs = 150_000 // words_per_paragraph
    filler_path = tmp_path / "big_filler.md"
    filler_path.write_text(make_filler_text(num_paragraphs, words_per_paragraph), encoding="utf-8")

    out = tmp_path / "big_out.md"
    start = time.time()
    result = mw.build_wrapper(retelling_file, filler_path, out, seed=99, chapter_words=2000, title="Big Doc")
    elapsed = time.time() - start

    assert elapsed < 10.0, f"took {elapsed:.2f}s, expected < 10s"
    assert result["words"] >= 150_000
    assert 1 < result["retelling_chapter"] < result["chapters"]

    verify_result = mw.verify_wrapper(out, retelling_file)
    assert verify_result["verified"] is True


# ---------------------------------------------------------------------------
# Paragraph splitting
# ---------------------------------------------------------------------------
def test_split_paragraphs_basic():
    text = "First paragraph.\n\nSecond paragraph,\nstill second.\n\n\nThird."
    assert mw.split_paragraphs(text) == [
        "First paragraph.",
        "Second paragraph,\nstill second.",
        "Third.",
    ]


def test_split_paragraphs_handles_crlf():
    text = "First.\r\n\r\nSecond."
    assert mw.split_paragraphs(text) == ["First.", "Second."]


def test_split_paragraphs_empty_input():
    assert mw.split_paragraphs("") == []
    assert mw.split_paragraphs("   \n\n  ") == []
