"""Tests for results_orchestrated.py: a fake orchestrated-runs tree with two finished cells
(one noisy, three segments) and one pending cell, plus an empty-tree smoke test.
"""
from __future__ import annotations

import json

import pytest

import results_orchestrated as ro

PRICES = {
    "claude-haiku-4-5": {"input_per_M": 1.0, "cached_input_per_M": 0.1, "cache_write_per_M": 1.25, "output_per_M": 5.0},
    "claude-sonnet-5": {"input_per_M": 2.0, "cached_input_per_M": 0.2, "cache_write_per_M": 2.5, "output_per_M": 10.0},
    "claude-opus-5": {"input_per_M": 5.0, "cached_input_per_M": 0.5, "cache_write_per_M": 6.25, "output_per_M": 25.0},
    "claude-fable-5": {"input_per_M": 10.0, "cached_input_per_M": 1.0, "cache_write_per_M": 12.5, "output_per_M": 50.0},
}


# --------------------------------------------------------------------------- fixture helpers


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path, data):
    write_text(path, json.dumps(data))


def write_jsonl(path, rows):
    write_text(path, "\n".join(json.dumps(r) for r in rows) + "\n")


def usage_row(role, timestamp, usage=None):
    return {"segment": 1, "role": role, "text": "", "model": "m", "usage": usage, "timestamp": timestamp}


def make_score(section_totals, deductions, total):
    sections = {s: {"items": [], "total": t, "max": t + 5} for s, t in section_totals.items()}
    return {"sections": sections, "deductions": deductions, "total": total}


HAIKU_SECTIONS = {"A": 24, "B": 8, "C": 12, "D": 9, "E": 6, "F": 7, "G": 4}  # sums to 70
OPUS_SECTIONS = {"A": 20, "B": 9, "C": 10, "D": 8, "E": 5, "F": 6, "G": 3}  # sums to 61


def build_tree(tmp_path):
    """haiku/single and opus/noisy are finished; sonnet/sequential is left entirely pending."""
    runs_dir = tmp_path / "runs"

    # --- haiku/single: finished, one segment, judgings differ (67 vs 69) ---
    hs = runs_dir / "haiku" / "single"
    write_text(
        hs / "answers.md",
        "A1: cannot be determined from the sources.\nA2: 42.\nA3: CANNOT BE DETERMINED here either.\n",
    )
    write_json(hs / "score.json", make_score(HAIKU_SECTIONS, [{"id": "d1", "points": -3, "note": "x"}], 67))
    write_json(hs / "score-2.json", make_score(HAIKU_SECTIONS, [{"id": "d1", "points": -1, "note": "y"}], 69))
    write_jsonl(
        hs / "transcript.jsonl",
        [
            usage_row("user", "2026-08-27T22:00:00.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T22:00:10.000Z",
                {
                    "input_tokens": 10000,
                    "cache_creation_input_tokens": 5000,
                    "cache_read_input_tokens": 2000,
                    "output_tokens": 20000,
                    "output_tokens_details": {"thinking_tokens": 3000},
                },
            ),
            usage_row(
                "assistant",
                "2026-08-27T22:00:20.000Z",
                {"input_tokens": 1000, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 500, "output_tokens": 1500},
            ),
            usage_row("user", "2026-08-27T22:00:25.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T22:05:00.000Z",
                {"input_tokens": 500, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 5000},
            ),
        ],
    )

    # --- opus/noisy: finished, three segments, judgings agree (60 == 60) ---
    on = runs_dir / "opus" / "noisy"
    write_text(on / "answers.md", "B1: cannot be determined from the sources.\nB2: 7.\n")
    write_json(on / "score.json", make_score(OPUS_SECTIONS, [{"id": "d1", "points": -1, "note": "x"}], 60))
    write_json(on / "score-2.json", make_score(OPUS_SECTIONS, [{"id": "d1", "points": -1, "note": "x"}], 60))
    write_jsonl(
        on / "transcript-seg1.jsonl",
        [
            usage_row("user", "2026-08-27T23:00:00.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T23:00:30.000Z",
                {
                    "input_tokens": 2000,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 1000,
                    "output_tokens": 3000,
                    "output_tokens_details": {"thinking_tokens": 500},
                },
            ),
        ],
    )
    write_jsonl(
        on / "transcript-seg2.jsonl",
        [
            usage_row("user", "2026-08-27T23:05:00.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T23:06:00.000Z",
                {"input_tokens": 1500, "cache_creation_input_tokens": 200, "cache_read_input_tokens": 300, "output_tokens": 2500},
            ),
        ],
    )
    write_jsonl(
        on / "transcript-seg3.jsonl",
        [
            usage_row("user", "2026-08-27T23:10:00.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T23:10:45.000Z",
                {
                    "input_tokens": 1000,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "output_tokens": 1000,
                    "output_tokens_details": {"thinking_tokens": 100},
                },
            ),
        ],
    )
    write_text(on / "notes-after-r04.md", "one two three four five six seven eight nine ten")
    write_text(on / "notes-after-r08.md", "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen")

    # --- sonnet/sequential: left entirely pending (no files at all) ---

    return runs_dir


# --------------------------------------------------------------------------- unit-level math


def test_compute_cell_stats_single_segment_hand_computed():
    segments = [
        [
            usage_row("user", "2026-08-27T22:00:00.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T22:00:10.000Z",
                {
                    "input_tokens": 10000,
                    "cache_creation_input_tokens": 5000,
                    "cache_read_input_tokens": 2000,
                    "output_tokens": 20000,
                    "output_tokens_details": {"thinking_tokens": 3000},
                },
            ),
            usage_row(
                "assistant",
                "2026-08-27T22:00:20.000Z",
                {"input_tokens": 1000, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 500, "output_tokens": 1500},
            ),
            usage_row("user", "2026-08-27T22:00:25.000Z"),
            usage_row(
                "assistant",
                "2026-08-27T22:05:00.000Z",
                {"input_tokens": 500, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0, "output_tokens": 5000},
            ),
        ]
    ]
    stats = ro.compute_cell_stats(segments)
    assert stats["assistant_turns"] == 3
    assert stats["raw_input_tokens"] == 11500
    assert stats["cache_read_tokens"] == 2500
    assert stats["cache_write_tokens"] == 5000
    assert stats["input_tokens_total"] == 19000
    assert stats["output_tokens"] == 26500
    assert stats["thinking_tokens"] == 3000
    assert stats["segments"] == 1
    assert stats["wall_clock_s"] == pytest.approx(300.0)

    cost = ro.cost_usd(stats, "claude-haiku-4-5", PRICES)
    assert cost == pytest.approx(0.1505)


def test_compute_cell_stats_sums_wall_clock_across_noisy_segments():
    segments = [
        [usage_row("user", "2026-08-27T23:00:00.000Z"), usage_row("assistant", "2026-08-27T23:00:30.000Z", {"input_tokens": 1, "output_tokens": 1})],
        [usage_row("user", "2026-08-27T23:05:00.000Z"), usage_row("assistant", "2026-08-27T23:06:00.000Z", {"input_tokens": 1, "output_tokens": 1})],
        [usage_row("user", "2026-08-27T23:10:00.000Z"), usage_row("assistant", "2026-08-27T23:10:45.000Z", {"input_tokens": 1, "output_tokens": 1})],
    ]
    stats = ro.compute_cell_stats(segments)
    assert stats["segments"] == 3
    # 30s + 60s + 45s, NOT (last of seg3 - first of seg1)
    assert stats["wall_clock_s"] == pytest.approx(135.0)


def test_cost_usd_returns_none_for_unpriced_model():
    stats = {"raw_input_tokens": 100, "cache_read_tokens": 0, "cache_write_tokens": 0, "output_tokens": 100}
    assert ro.cost_usd(stats, "claude-mythos-5", PRICES) is None


def test_count_abstentions_is_case_insensitive():
    text = "cannot be determined here, CANNOT BE DETERMINED there, and Cannot Be Determined again."
    assert ro.count_abstentions(text) == 3
    assert ro.count_abstentions("no matches here") == 0


def test_section_totals_sums_deductions_and_keeps_total():
    score = {
        "sections": {"A": {"total": 24}, "B": {"total": 8}},
        "deductions": [{"points": -3}, {"points": -1}],
        "total": 28,
    }
    totals = ro.section_totals(score)
    assert totals == {"A": 24, "B": 8, "deductions": -4, "total": 28}


# --------------------------------------------------------------------------- full report render


def test_render_report_totals_table(tmp_path):
    runs_dir = build_tree(tmp_path)
    text = ro.render_report(runs_dir, PRICES, "2026-08-27")

    assert "# Story test v2.1 -- orchestrated runs" in text
    assert "Generated: 2026-08-27" in text

    # haiku/single: score.json=67, score-2.json=69, differ -> parenthesized
    assert "| haiku | 67 (69) | pending | pending |" in text
    # opus/noisy: both judgings agree at 60 -> no parenthetical
    assert "| opus | pending | pending | 60 |" in text
    # sonnet/sequential and the whole fable row: entirely pending
    assert "| sonnet | pending | pending | pending |" in text
    assert "| fable | pending | pending | pending |" in text


def test_render_report_section_profile_table(tmp_path):
    runs_dir = build_tree(tmp_path)
    text = ro.render_report(runs_dir, PRICES, "2026-08-27")

    assert "| haiku | single | A 24 · B 8 · C 12 · D 9 · E 6 · F 7 · G 4 | -3 |" in text
    assert "| opus | noisy | A 20 · B 9 · C 10 · D 8 · E 5 · F 6 · G 3 | -1 |" in text
    assert "| sonnet | sequential | pending | pending |" in text


def test_render_report_cost_table_hand_computed(tmp_path):
    runs_dir = build_tree(tmp_path)
    text = ro.render_report(runs_dir, PRICES, "2026-08-27")

    # haiku/single: 3 assistant turns, 19000 in / 26500 out / 3000 thinking, 1 segment, 300.0s, $0.1505
    assert "| haiku | single | 3 | 19000 | 26500 | 3000 | 1 | 300.0 | 0.1505 |" in text
    # opus/noisy: 3 assistant turns (1 per segment), 6000 in / 6500 out / 600 thinking, 3 segments, 135.0s, $0.1869
    assert "| opus | noisy | 3 | 6000 | 6500 | 600 | 3 | 135.0 | 0.1869 |" in text
    # sonnet/sequential: no transcript at all -> every volume/cost column is pending
    assert "| sonnet | sequential | pending | pending | pending | pending | pending | pending | pending |" in text


def test_render_report_cost_is_na_when_model_missing_from_prices(tmp_path):
    runs_dir = tmp_path / "runs"
    fs = runs_dir / "fable" / "single"
    write_jsonl(
        fs / "transcript.jsonl",
        [
            usage_row("user", "2026-08-27T00:00:00.000Z"),
            usage_row("assistant", "2026-08-27T00:01:00.000Z", {"input_tokens": 10, "output_tokens": 10}),
        ],
    )
    prices_without_fable = {k: v for k, v in PRICES.items() if k != "claude-fable-5"}
    text = ro.render_report(runs_dir, prices_without_fable, "2026-08-27")
    assert "| fable | single | 1 | 10 | 10 | 0 | 1 | 60.0 | n/a |" in text


def test_render_report_judge_stability(tmp_path):
    runs_dir = build_tree(tmp_path)
    text = ro.render_report(runs_dir, PRICES, "2026-08-27")

    assert "haiku/single: |total - total2| = 2" in text
    assert "opus/noisy: |total - total2| = 0" in text
    assert "Max across all judged cells: 2" in text
    # sonnet/sequential has neither score file -> not listed as a judged cell
    assert "sonnet/sequential:" not in text


def test_render_report_notes_section(tmp_path):
    runs_dir = build_tree(tmp_path)
    text = ro.render_report(runs_dir, PRICES, "2026-08-27")

    # Abstentions: haiku/single has 2, opus/noisy has 1, sonnet/sequential is pending (no answers.md)
    assert "| haiku | single | 2 |" in text
    assert "| opus | noisy | 1 |" in text
    assert "| sonnet | sequential | pending |" in text

    # Noisy-mode notes word counts: opus has both files (10 and 15 words); haiku/sonnet/fable noisy cells are pending
    assert "| opus | 10 | 15 |" in text
    assert "| haiku | pending | pending |" in text
    assert "| sonnet | pending | pending |" in text
    assert "| fable | pending | pending |" in text

    # Fixed caveat paragraph
    assert "Opus subagent" in text
    assert "n = 1" in text
    assert "v2.1" in text
    assert "not deterministic" in text


def test_render_report_handles_completely_empty_runs_dir(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    text = ro.render_report(runs_dir, PRICES, "2026-08-27")

    assert "# Story test v2.1 -- orchestrated runs" in text
    assert "| haiku | pending | pending | pending |" in text
    assert "| sonnet | pending | pending | pending |" in text
    assert "| opus | pending | pending | pending |" in text
    assert "| fable | pending | pending | pending |" in text
    assert "No cell has both score.json and score-2.json yet." in text


def test_render_report_handles_nonexistent_runs_dir(tmp_path):
    runs_dir = tmp_path / "does-not-exist"
    text = ro.render_report(runs_dir, PRICES, "2026-08-27")
    assert "# Story test v2.1 -- orchestrated runs" in text
    assert "| haiku | pending | pending | pending |" in text


# --------------------------------------------------------------------------- CLI wiring


def test_main_writes_report_file_on_empty_tree(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    prices_path = tmp_path / "prices.json"
    prices_path.write_text(json.dumps(PRICES), encoding="utf-8")
    out_path = tmp_path / "results.md"

    rc = ro.main(["--runs", str(runs_dir), "--out", str(out_path), "--prices", str(prices_path), "--date", "2026-08-27"])

    assert rc == 0
    assert out_path.is_file()
    text = out_path.read_text(encoding="utf-8")
    assert "# Story test v2.1 -- orchestrated runs" in text
    assert "Generated: 2026-08-27" in text


def test_main_defaults_prices_to_file_next_to_script(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    out_path = tmp_path / "results.md"

    # No --prices given: should fall back to the real v2/harness/prices.json without raising.
    rc = ro.main(["--runs", str(runs_dir), "--out", str(out_path)])

    assert rc == 0
    assert out_path.is_file()
