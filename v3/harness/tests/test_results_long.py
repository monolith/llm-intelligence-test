"""Tests for results_long.py: a fake v3 long-variant runs tree with one complete long-notes
cell (haiku), one long-reread cell missing batch 3 (opus), and a fake batches.md (33/33/34).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS_DIR))
import results_long as rl  # noqa: E402


PRICES = {
    "claude-haiku-4-5": {"input_per_M": 1.0, "cached_input_per_M": 0.1, "cache_write_per_M": 1.25, "output_per_M": 5.0},
    "claude-sonnet-5": {"input_per_M": 2.0, "cached_input_per_M": 0.2, "cache_write_per_M": 2.5, "output_per_M": 10.0},
    "claude-opus-5": {"input_per_M": 5.0, "cached_input_per_M": 0.5, "cache_write_per_M": 6.25, "output_per_M": 25.0},
    "claude-fable-5": {"input_per_M": 10.0, "cached_input_per_M": 1.0, "cache_write_per_M": 12.5, "output_per_M": 50.0},
}

BATCHES_MD = """# Batch key, v3 (fake)

## Batch 1

- A1 item
- A2 item

Total: 33 points

## Batch 2

- B1 item

Total: 33 points

## Batch 3

- C1 item

Total: 34 points
"""


# --------------------------------------------------------------------------- fixture helpers


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, data):
    write_text(path, json.dumps(data))


def write_jsonl(path, rows):
    write_text(path, "\n".join(json.dumps(r) for r in rows) + "\n")


def usage_row(role, ts, usage=None):
    return {"segment": 1, "role": role, "text": "", "model": "m", "usage": usage, "timestamp": ts}


def assistant_row(input_tokens=0, output_tokens=0, cache_read=0, cache_write=0, ts="2026-08-27T00:00:00.000Z"):
    return usage_row(
        "assistant",
        ts,
        {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_read_input_tokens": cache_read,
            "cache_creation_input_tokens": cache_write,
        },
    )


def make_score(sections, deductions, total):
    return {"sections": {s: {"total": t} for s, t in sections.items()}, "deductions": deductions, "total": total}


def write_batches_md(tmp_path):
    path = tmp_path / "batches.md"
    write_text(path, BATCHES_MD)
    return path


def build_tree(tmp_path):
    """haiku/long-notes is fully finished (4 ingest segments, 3 scored batches).
    opus/long-reread has batch-1 and batch-2 finished but batch-3 entirely missing.
    Every other cell (sonnet/*, fable/*) is left entirely pending.
    """
    runs_dir = tmp_path / "runs"

    # --- haiku/long-notes: ingest, input-only usage so costs are exact ---
    hn = runs_dir / "haiku" / "long-notes"
    ingest_inputs = {1: 100000, 2: 200000, 3: 150000, 4: 50000}  # sum 500000 -> cost 0.5000
    ingest_note_words = {1: 3, 2: 5, 3: 4, 4: 6}
    for i in range(1, 5):
        write_jsonl(hn / "ingest" / f"transcript-seg{i}.jsonl", [usage_row("user", "2026-08-27T00:00:00.000Z"), assistant_row(input_tokens=ingest_inputs[i])])
        write_text(hn / "ingest" / f"notes-{i}.md", " ".join(f"w{n}" for n in range(ingest_note_words[i])))

    # batch-1: cost 0.10, score 20/33 vs 22 (differ) -> abstains x2
    write_jsonl(hn / "batch-1" / "transcript.jsonl", [assistant_row(input_tokens=100000)])
    write_text(hn / "batch-1" / "answers.md", "Cannot be determined. Also CANNOT BE DETERMINED here.")
    write_json(hn / "batch-1" / "score.json", make_score({"A": 12, "B": 8}, [{"id": "d1", "points": -2}], 20))
    write_json(hn / "batch-1" / "score-2.json", make_score({"A": 14, "B": 8}, [], 22))

    # batch-2: cost 0.06, score 30/33 both judges agree -> abstains x1
    write_jsonl(hn / "batch-2" / "transcript.jsonl", [assistant_row(input_tokens=60000)])
    write_text(hn / "batch-2" / "answers.md", "cannot be determined once here.")
    write_json(hn / "batch-2" / "score.json", make_score({"A": 20, "B": 10}, [], 30))
    write_json(hn / "batch-2" / "score-2.json", make_score({"A": 20, "B": 10}, [], 30))

    # batch-3: cost 0.017, full score 34/34 both judges agree -> no abstentions
    write_jsonl(hn / "batch-3" / "transcript.jsonl", [assistant_row(input_tokens=17000)])
    write_text(hn / "batch-3" / "answers.md", "42.")
    write_json(hn / "batch-3" / "score.json", make_score({"C": 34}, [], 34))
    write_json(hn / "batch-3" / "score-2.json", make_score({"C": 34}, [], 34))

    # --- opus/long-reread: no ingest dir (structural), batch-3 entirely missing ---
    orr = runs_dir / "opus" / "long-reread"

    # batch-1: cost 0.04, score 15/33 both judges agree -> abstains x1
    write_jsonl(orr / "batch-1" / "transcript.jsonl", [assistant_row(input_tokens=8000)])
    write_text(orr / "batch-1" / "answers.md", "cannot be determined.")
    write_json(orr / "batch-1" / "score.json", make_score({"A": 15}, [], 15))
    write_json(orr / "batch-1" / "score-2.json", make_score({"A": 15}, [], 15))

    # batch-2: cost 0.02, score 25/33 vs 27 (differ) -> no abstentions
    write_jsonl(orr / "batch-2" / "transcript.jsonl", [assistant_row(input_tokens=4000)])
    write_text(orr / "batch-2" / "answers.md", "no abstention markers here.")
    write_json(orr / "batch-2" / "score.json", make_score({"B": 25}, [], 25))
    write_json(orr / "batch-2" / "score-2.json", make_score({"B": 27}, [], 27))

    # batch-3: nothing written at all -> entirely pending

    return runs_dir


# --------------------------------------------------------------------------- parse_batch_maxes


def test_parse_batch_maxes_explicit_total_line(tmp_path):
    path = write_batches_md(tmp_path)
    assert rl.parse_batch_maxes(path) == {1: 33, 2: 33, 3: 34}


def test_parse_batch_maxes_heading_points(tmp_path):
    text = "## Batch 1 (10 points)\nsome item\n\n## Batch 2 (20 points)\nsome item\n"
    path = tmp_path / "b.md"
    path.write_text(text, encoding="utf-8")
    assert rl.parse_batch_maxes(path) == {1: 10, 2: 20}


def test_parse_batch_maxes_sums_item_points_when_no_total(tmp_path):
    text = "## Batch 1\n- A1 (3 points)\n- A2 (4 points)\n\n## Batch 2\n- B1 (7 points)\n"
    path = tmp_path / "b.md"
    path.write_text(text, encoding="utf-8")
    assert rl.parse_batch_maxes(path) == {1: 7, 2: 7}


# --------------------------------------------------------------------------- unit-level math


def test_token_totals_and_cost_usd_hand_computed():
    rows = [assistant_row(input_tokens=100000, output_tokens=0)]
    totals = rl.token_totals(rows)
    assert totals["raw_input"] == 100000
    assert totals["total_tokens"] == 100000
    cost = rl.cost_usd(totals, "claude-haiku-4-5", PRICES)
    assert cost == pytest.approx(0.10)


def test_count_abstentions_is_case_insensitive():
    text = "cannot be determined here, CANNOT BE DETERMINED there, and Cannot Be Determined again."
    assert rl.count_abstentions(text) == 3
    assert rl.count_abstentions("no matches here") == 0


def test_section_totals_sums_deductions_and_keeps_total():
    score = {"sections": {"A": {"total": 20}, "B": {"total": 10}}, "deductions": [{"points": -2}, {"points": -1}], "total": 27}
    sections, deductions_total = rl.section_totals(score)
    assert sections == {"A": 20, "B": 10}
    assert deductions_total == -3


# --------------------------------------------------------------------------- full report render


def test_render_report_cost_curve_hand_computed(tmp_path):
    runs_dir = build_tree(tmp_path)
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    assert "# Story test v3 -- long variant" in text
    assert "Generated: 2026-08-27" in text

    # haiku/long-notes: ingest 0.5000 (500000 tokens), batches 0.1000/0.0600/0.0170, total 0.6770
    assert "| haiku | long-notes | 0.5000 (500000) | 0.1000 | 0.0600 | 0.0170 | 0.6770 |" in text

    # opus/long-reread: no ingest phase -> dash; batch-3 missing -> pending cascades to Total
    assert "| opus | long-reread | — | 0.0400 | 0.0200 | pending | pending |" in text

    # sonnet/* and fable/*: entirely pending, long-reread ingest is dash even with zero data
    assert "| sonnet | long-notes | pending | pending | pending | pending | pending |" in text
    assert "| sonnet | long-reread | — | pending | pending | pending | pending |" in text
    assert "| fable | long-reread | — | pending | pending | pending | pending |" in text


def test_render_report_scores_table(tmp_path):
    runs_dir = build_tree(tmp_path)
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    # haiku/long-notes: 20/33 (22) differ, 30/33 agree, 34/34 agree -> sum 84/100 (86) differ
    assert "| haiku | long-notes | 20/33 (22) | 30/33 | 34/34 | 84/100 (86) |" in text

    # opus/long-reread: 15/33 agree, 25/33 (27) differ, batch-3 missing -> sum pending
    assert "| opus | long-reread | 15/33 | 25/33 (27) | pending | pending |" in text


def test_render_report_section_profile_table(tmp_path):
    runs_dir = build_tree(tmp_path)
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    assert "| haiku | long-notes | batch-1 | A 12 · B 8 | -2 |" in text
    assert "| haiku | long-notes | batch-2 | A 20 · B 10 | 0 |" in text
    assert "| haiku | long-notes | batch-3 | C 34 | 0 |" in text
    assert "| opus | long-reread | batch-1 | A 15 | 0 |" in text
    assert "| opus | long-reread | batch-3 | pending | pending |" in text


def test_render_report_cost_per_point_hand_computed(tmp_path):
    runs_dir = build_tree(tmp_path)
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    # haiku/long-notes: 0.10/20=0.0050, 0.06/30=0.0020, 0.017/34=0.0005
    # cumulative = (ingest 0.5 + 0.10+0.06+0.017) / (20+30+34) = 0.677/84 = 0.0081
    assert "| haiku | long-notes | 0.0050 | 0.0020 | 0.0005 | 0.0081 |" in text

    # opus/long-reread: 0.04/15=0.0027, 0.02/25=0.0008, batch-3 pending
    # cumulative (no ingest phase) = (0.04+0.02)/(15+25) = 0.06/40 = 0.0015
    assert "| opus | long-reread | 0.0027 | 0.0008 | pending | 0.0015 |" in text

    # sonnet/long-notes: nothing at all -> every column pending
    assert "| sonnet | long-notes | pending | pending | pending | pending |" in text


def test_render_report_judge_stability(tmp_path):
    runs_dir = build_tree(tmp_path)
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    assert "haiku/long-notes/batch-1: |total - total2| = 2" in text
    assert "haiku/long-notes/batch-2: |total - total2| = 0" in text
    assert "haiku/long-notes/batch-3: |total - total2| = 0" in text
    assert "opus/long-reread/batch-1: |total - total2| = 0" in text
    assert "opus/long-reread/batch-2: |total - total2| = 2" in text
    # opus/long-reread/batch-3 has neither score file -> not listed
    assert "opus/long-reread/batch-3:" not in text
    assert "Max across all judged batches: 2" in text


def test_render_report_notes_section(tmp_path):
    runs_dir = build_tree(tmp_path)
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    # Ingest notes word counts: haiku/long-notes has 3,5,4,6; every long-reread row is dash
    assert "| haiku | long-notes | 3 · 5 · 4 · 6 |" in text
    assert "| opus | long-reread | — |" in text
    assert "| sonnet | long-notes | pending | pending | pending | pending |" in text

    # Abstentions: haiku/long-notes batches have 2, 1, 0; opus/long-reread has 1, 0, pending
    assert "| haiku | long-notes | 2 | 1 | 0 |" in text
    assert "| opus | long-reread | 1 | 0 | pending |" in text
    assert "| sonnet | long-notes | pending | pending | pending |" in text

    # Fixed caveat paragraph
    assert "Opus subagent" in text
    assert "n = 1" in text
    assert "v3.1" in text
    assert "cached rate" in text
    assert "named `kb`" in text


def test_render_report_handles_completely_empty_runs_dir(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))

    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")

    assert "# Story test v3 -- long variant" in text
    for model in rl.MODEL_ROWS:
        assert f"| {model} | long-notes | pending | pending | pending | pending | pending |" in text
        assert f"| {model} | long-reread | — | pending | pending | pending | pending |" in text
    assert "No batch has both score.json and score-2.json yet." in text


def test_render_report_handles_nonexistent_runs_dir(tmp_path):
    runs_dir = tmp_path / "does-not-exist"
    batch_maxes = rl.parse_batch_maxes(write_batches_md(tmp_path))
    text = rl.render_report(runs_dir, PRICES, batch_maxes, "2026-08-27")
    assert "# Story test v3 -- long variant" in text
    assert "| haiku | long-notes | pending | pending | pending | pending | pending |" in text


# --------------------------------------------------------------------------- CLI wiring


def test_main_writes_report_file_on_empty_tree(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    prices_path = tmp_path / "prices.json"
    prices_path.write_text(json.dumps(PRICES), encoding="utf-8")
    batches_path = write_batches_md(tmp_path)
    out_path = tmp_path / "results-long.md"

    rc = rl.main(
        [
            "--runs", str(runs_dir),
            "--out", str(out_path),
            "--prices", str(prices_path),
            "--batches", str(batches_path),
            "--date", "2026-08-27",
        ]
    )

    assert rc == 0
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert "# Story test v3 -- long variant" in text
    assert "Generated: 2026-08-27" in text


def test_main_accepts_real_v2_prices_file(tmp_path):
    """CLI usage per the spec always passes `--prices v2/harness/prices.json` explicitly."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    batches_path = write_batches_md(tmp_path)
    out_path = tmp_path / "results-long.md"
    real_prices_path = HARNESS_DIR.parent.parent / "v2" / "harness" / "prices.json"

    rc = rl.main(
        [
            "--runs", str(runs_dir),
            "--out", str(out_path),
            "--prices", str(real_prices_path),
            "--batches", str(batches_path),
            "--date", "2026-08-27",
        ]
    )

    assert rc == 0
    assert out_path.is_file()
