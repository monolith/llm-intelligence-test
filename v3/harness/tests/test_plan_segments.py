"""Tests for v3/harness/plan_segments.py.

Run with:
    v2/harness/.venv/bin/pytest v3/harness/tests/test_plan_segments.py -v

Covers:
  * a fake root with small files and a tiny (but notes-overhead-clean) budget:
    - documents are split at line boundaries, including across segment
      boundaries (the "compaction while reading" case)
    - no single read exceeds --max-lines
    - every segment's est_tokens estimate stays within --budget
    - every line of every ingest document is read exactly once, no gaps/overlap
  * notes chaining: a pre-existing notes-<k>.md is costed/read at its actual
    word count; a missing one falls back to the fixed 6,000-word assumption
  * --render prints an instruction list whose offsets/limits match the plan
  * --verify-allowed prints one basename per distinct file (collapsed) plus
    the notes file being written
  * a run over the REAL v3 tree at the default budget completes and reports
    a segment count
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parents[1]
V3_DIR = HARNESS_DIR.parent
REPO_ROOT = V3_DIR.parent
SCRIPT = HARNESS_DIR / "plan_segments.py"

sys.path.insert(0, str(HARNESS_DIR))
import plan_segments as ps  # noqa: E402

WORDS_PER_LINE = 5
LINE_TEXT = " ".join(f"w{i}" for i in range(WORDS_PER_LINE))


# ---------------------------------------------------------------------------
# fake-root fixture
# ---------------------------------------------------------------------------


def _write_lines(path: Path, n: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(LINE_TEXT for _ in range(n)) + "\n", encoding="utf-8")


# Non-default sizes (in lines) for a couple of documents, to force both
# ordinary max-lines chunking (small/medium docs) and a document big enough
# to blow past a whole segment's capacity by itself (r03, the oversized
# wrapped retelling -- guarantees at least one cross-segment-boundary split).
OVERSIZED_WRAPPED_LINES = 2000
MODEST_WRAPPED_LINES = 50
SHORT_RETELLING_LINES = 6
SHORT_NOISE_LINES = 4
LONG_NOISE_LINES = 100

MAX_LINES = 15
BUDGET = 10000  # > the fixed 6,000-word (8,100-token) notes fallback


def make_fake_root(root: Path) -> None:
    # 24 noise slots: n01.md .. n24.md, alternating two "kinds" (kind text is
    # never interpreted by the planner, just carried in ORDER.md/questions.md).
    order_rows = []
    q_entries = []
    for i in range(1, 25):
        fname = f"n{i:02d}.md"
        _write_lines(root / "distractors" / fname, SHORT_NOISE_LINES)
        kind = "alpha" if i % 2 else "beta"
        order_rows.append(f"| {i} | r{i:02d} | {fname} | {kind} |")
        q_entries.append(f"## {i}. {fname}\n**Q:** What is slot {i} about?\n**A:** slot-{i}-answer.\n")

    order_md = (
        "# fake order\n\n"
        "| slot | after | file | kind |\n"
        "|---|---|---|---|\n" + "\n".join(order_rows) + "\n"
    )
    (root / "distractors" / "ORDER.md").write_text(order_md, encoding="utf-8")
    (root / "distractors" / "questions.md").write_text(
        "# fake questions\n\n" + "\n".join(q_entries), encoding="utf-8"
    )

    wrapped = set(ps.WRAPPED_INDICES)
    for i in range(1, 25):
        ii = f"{i:02d}"
        if i in wrapped:
            n_lines = OVERSIZED_WRAPPED_LINES if i == 3 else MODEST_WRAPPED_LINES
            _write_lines(root / "test-input" / "long" / f"r{ii}-long.md", n_lines)
        else:
            _write_lines(root / "test-input" / "retellings" / f"r{ii}-fake.md", SHORT_RETELLING_LINES)

    long_kinds = {1: "ledger", 2: "transcript", 3: "gibberish", 4: "mixed"}
    for n, kindname in long_kinds.items():
        _write_lines(root / "distractors" / "long" / f"L{n}-{kindname}.md", LONG_NOISE_LINES)
        (root / "distractors" / "long" / f"L{n}-question.txt").write_text(
            f"Q: What is long-noise {n} about?\nA: L{n}-answer.\n", encoding="utf-8"
        )


@pytest.fixture()
def fake_root(tmp_path: Path) -> Path:
    root = tmp_path / "v3"
    make_fake_root(root)
    return root


# ---------------------------------------------------------------------------
# helpers for assertions
# ---------------------------------------------------------------------------


def all_reads(segments: list[dict]):
    for seg in segments:
        for r in seg["reads"]:
            yield seg, r


def coverage_by_file(segments: list[dict]) -> dict[str, list[tuple[int, int]]]:
    """file -> list of (offset, limit) for its non-notes reads, in plan order."""
    out: dict[str, list[tuple[int, int]]] = {}
    for _, r in all_reads(segments):
        if r["kind"] == "notes":
            continue
        out.setdefault(r["file"], []).append((r["offset"], r["limit"]))
    return out


# ---------------------------------------------------------------------------
# main coverage / constraint tests
# ---------------------------------------------------------------------------


def test_no_read_exceeds_max_lines(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    for _, r in all_reads(segments):
        assert r["limit"] <= MAX_LINES
        assert r["limit"] >= 1


def test_segment_token_estimates_within_budget(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    assert len(segments) >= 2, "fixture should force more than one segment"
    for seg in segments:
        assert seg["est_tokens"] <= BUDGET


def test_every_line_read_exactly_once(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    by_file = coverage_by_file(segments)

    # every ingest document that exists on disk under fake_root must appear
    docs = ps.build_docs(fake_root)
    assert len(docs) == len(by_file)

    for doc in docs:
        path = str(doc["file"])
        total = len(ps.line_word_counts(doc["file"]))
        covered = [False] * (total + 1)  # 1-indexed
        ranges = by_file[path]
        assert ranges, f"no reads recorded for {path}"
        for offset, limit in ranges:
            for ln in range(offset, offset + limit):
                assert not covered[ln], f"line {ln} of {path} read more than once"
                covered[ln] = True
        assert all(covered[1:]), f"not every line of {path} was read"


def test_cross_segment_document_split_happens(fake_root: Path):
    """The oversized wrapped retelling (r03) must be too big for one segment,
    proving 'compaction while reading': a document split across a segment
    boundary, with the next reader resuming exactly where the last left off.
    """
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    file_to_segment_indices: dict[str, set[int]] = {}
    for seg in segments:
        for r in seg["reads"]:
            if r["kind"] == "notes":
                continue
            file_to_segment_indices.setdefault(r["file"], set()).add(seg["index"])
    assert any(len(idxs) > 1 for idxs in file_to_segment_indices.values())

    # and for that split document, offsets are contiguous with no gap/overlap
    # across the segment boundary (already proven globally above, but check
    # explicitly here for the specific oversized document too)
    r03_doc = next(d for d in ps.build_docs(fake_root) if d["doc_id"] == "r03")
    ranges = sorted(coverage_by_file(segments)[str(r03_doc["file"])])
    expected_next = 1
    for offset, limit in ranges:
        assert offset == expected_next
        expected_next = offset + limit
    assert expected_next - 1 == OVERSIZED_WRAPPED_LINES


def test_question_only_on_final_chunk_of_noise_docs(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    by_doc_id_reads: dict[str, list[dict]] = {}
    for _, r in all_reads(segments):
        if r["kind"] == "notes":
            continue
        by_doc_id_reads.setdefault(r["file"], []).append(r)

    docs = ps.build_docs(fake_root)
    for doc in docs:
        reads = by_doc_id_reads[str(doc["file"])]
        if doc["kind"] in ("noise", "long-noise"):
            assert reads[-1]["question"] == doc["question"]
            assert reads[-1]["acknowledge"] is False
            for r in reads[:-1]:
                assert r["question"] is None
                assert r["acknowledge"] is True
        else:  # retelling / wrapped: never a question
            for r in reads:
                assert r["question"] is None
                assert r["acknowledge"] is True


def test_labels(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    by_doc_id_reads: dict[str, list[dict]] = {}
    for _, r in all_reads(segments):
        if r["kind"] == "notes":
            continue
        by_doc_id_reads.setdefault(r["file"], []).append(r)

    docs = ps.build_docs(fake_root)
    for doc in docs:
        reads = by_doc_id_reads[str(doc["file"])]
        if len(reads) == 1:
            assert reads[0]["label"] == doc["label_base"]
        else:
            for j, r in enumerate(reads, start=1):
                assert r["label"] == f"{doc['label_base']} part {j}/{len(reads)}"


# ---------------------------------------------------------------------------
# notes chaining
# ---------------------------------------------------------------------------


def test_notes_read_word_count_helper(tmp_path: Path):
    existing = tmp_path / "notes-1.md"
    existing.write_text("one two three four five six seven eight", encoding="utf-8")
    assert ps.notes_read_word_count(existing) == 8

    missing = tmp_path / "notes-99.md"
    assert ps.notes_read_word_count(missing) == ps.ASSUMED_NOTES_WORDS == 6000


def test_notes_chaining_actual_vs_assumed(fake_root: Path):
    model = "chain-model"
    notes_dir = fake_root / "runs" / model / "long-notes" / "ingest"

    # Case A: no notes-1.md yet -> fallback assumption, and (since we don't
    # know a real line count) the read is capped at --max-lines.
    segments_a = ps.build_plan(fake_root, model, BUDGET, MAX_LINES)
    assert len(segments_a) >= 2
    seg2_a = next(s for s in segments_a if s["index"] == 2)
    notes_read_a = seg2_a["reads"][0]
    assert notes_read_a["kind"] == "notes"
    assert notes_read_a["offset"] == 1
    assert notes_read_a["file"].endswith("notes-1.md")
    assert notes_read_a["limit"] == MAX_LINES

    # Case B: a real, tiny notes-1.md now exists -> actual word count/line
    # count drive the read, not the fallback.
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "notes-1.md").write_text("only one line of notes here", encoding="utf-8")
    segments_b = ps.build_plan(fake_root, model, BUDGET, MAX_LINES)
    seg2_b = next(s for s in segments_b if s["index"] == 2)
    notes_read_b = seg2_b["reads"][0]
    assert notes_read_b["kind"] == "notes"
    assert notes_read_b["limit"] == 1  # the real file only has 1 line


# ---------------------------------------------------------------------------
# render / verify-allowed
# ---------------------------------------------------------------------------


def test_render_names_offsets_correctly(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    seg = segments[0]
    notes_dir = ps.notes_dir_for(fake_root, "m")
    text = ps.render_segment(seg, notes_dir)

    read_lines = [
        line
        for line in text.splitlines()
        if re.search(r"\(offset \d+, limit \d+\)", line)
    ]
    assert len(read_lines) == len(seg["reads"])
    for r, line in zip(seg["reads"], read_lines):
        m = re.search(r"lines (\d+)\S(\d+) \(offset (\d+), limit (\d+)\)", line)
        assert m, line
        a, b, off, lim = (int(x) for x in m.groups())
        assert off == r["offset"] == a
        assert lim == r["limit"]
        assert b == off + lim - 1

    # the last numbered instruction is the notes-writing step
    assert seg["notes_out"] in text.splitlines()[-1]


def test_verify_allowed_collapses_and_appends_notes_file(fake_root: Path):
    segments = ps.build_plan(fake_root, "m", BUDGET, MAX_LINES)
    seg = next(s for s in segments if len(s["reads"]) >= 2)
    basenames = ps.verify_allowed_basenames(seg)

    # collapsed: no two consecutive entries equal, and it matches a manual
    # collapse of the segment's own reads
    manual = []
    prev = None
    for r in seg["reads"]:
        bn = Path(r["file"]).name
        if bn != prev:
            manual.append(bn)
            prev = bn
    manual.append(seg["notes_out"])
    assert basenames == manual
    assert basenames[-1] == seg["notes_out"]
    for a, b in zip(basenames, basenames[1:]):
        assert a != b


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_cli_writes_plan_json(fake_root: Path, tmp_path: Path):
    out_path = tmp_path / "plan.json"
    proc = run_cli(
        "--root", str(fake_root), "--model", "clim",
        "--budget", str(BUDGET), "--max-lines", str(MAX_LINES),
        "--out", str(out_path),
    )
    assert proc.returncode == 0, proc.stderr
    assert out_path.exists()
    plan = json.loads(out_path.read_text(encoding="utf-8"))
    assert isinstance(plan, list)
    assert len(plan) >= 2

    proc_render = run_cli(
        "--root", str(fake_root), "--model", "clim",
        "--budget", str(BUDGET), "--max-lines", str(MAX_LINES),
        "--out", str(out_path), "--render", "1",
    )
    assert proc_render.returncode == 0, proc_render.stderr
    assert "Segment 1 instructions" in proc_render.stdout

    proc_va = run_cli(
        "--root", str(fake_root), "--model", "clim",
        "--budget", str(BUDGET), "--max-lines", str(MAX_LINES),
        "--out", str(out_path), "--verify-allowed", "1",
    )
    assert proc_va.returncode == 0, proc_va.stderr
    assert "--allowed" in proc_va.stdout


# ---------------------------------------------------------------------------
# real v3 tree
# ---------------------------------------------------------------------------


def test_real_v3_tree_default_budget():
    real_root = V3_DIR
    segments = ps.build_plan(real_root, "planner-smoke-test", budget=110000, max_lines=800)
    assert len(segments) >= 1
    for seg in segments:
        for r in seg["reads"]:
            assert r["limit"] <= 800
    print(f"\nreal v3 tree: {len(segments)} segments at budget=110000, max_lines=800")
