"""Report rendering from two fake run directories, with the other ten cells left empty."""
from __future__ import annotations

import json

import report


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def make_run_json(model, mode, input_tokens, output_tokens, cost):
    return {
        "model": model,
        "mode": mode,
        "started_at": "2026-08-27T00:00:00+00:00",
        "finished_at": "2026-08-27T00:05:00+00:00",
        "wall_clock_s": 300.0,
        "num_requests": 1,
        "num_compactions": 0,
        "totals": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "cost_usd": cost,
        },
    }


def make_score_json(total, max_abs_diff):
    sections = {s: {"items": [], "total": 4} for s in "ABCDEFG"}
    canonical = {"sections": sections, "deductions": [{"reason": "x", "points": -2}], "total": total}
    return {"judgings": [canonical, canonical], "canonical": canonical, "max_abs_diff": max_abs_diff}


def test_render_report_from_two_run_dirs(tmp_path):
    runs_dir = tmp_path / "runs"

    write_json(runs_dir / "claude-haiku-4-5" / "single" / "run.json", make_run_json("claude-haiku-4-5", "single", 1000, 200, 0.01))
    write_json(runs_dir / "claude-haiku-4-5" / "single" / "score.json", make_score_json(70, 1))

    write_json(runs_dir / "claude-sonnet-5" / "sequential" / "run.json", make_run_json("claude-sonnet-5", "sequential", 5000, 900, 0.05))
    write_json(runs_dir / "claude-sonnet-5" / "sequential" / "score.json", make_score_json(65, 4))

    text = report.render_report(runs_dir)

    # Total table
    assert "haiku" in text
    assert "sonnet" in text
    assert "70" in text
    assert "65" in text

    # Missing cells render as a dash, not an error
    assert "—" in text

    # Section profile: haiku/single carries its per-section totals through
    assert "| haiku | single |" in text

    # Cost table: tokens for the two real cells show up
    assert "1000" in text
    assert "5000" in text

    # Judge stability line reports both max_abs_diff values and the overall max
    assert "haiku/single" in text
    assert "sonnet/sequential" in text
    assert "Max across all judged runs: 4" in text

    # No kappa.json yet -> placeholder, not a crash
    assert "Not yet computed" in text


def test_render_report_reads_kappa_json_when_present(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir(parents=True)
    write_json(runs_dir / "kappa.json", {"runs": ["claude-haiku-4-5/single", "claude-sonnet-5/single"], "kappa": {"A": 0.85, "B": 1.0}})

    text = report.render_report(runs_dir)

    assert "Hand-scoring" in text
    assert "0.85" in text or "0.8500" in text
    assert "Not yet computed" not in text


def test_render_report_handles_completely_empty_runs_dir(tmp_path):
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()

    text = report.render_report(runs_dir)

    assert "haiku" in text
    assert "fable" in text
    assert "Not yet computed" in text
