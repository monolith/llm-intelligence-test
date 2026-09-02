"""The repeat-run aggregator must compute what it claims and refuse what it cannot."""
import json, math, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import stats_short as S


def cell(tmp, tree, model, mode, s1, s2, turns=5):
    d = tmp / tree / model / mode
    d.mkdir(parents=True)
    (d / "score.json").write_text(json.dumps({"total": s1}))
    (d / "score-2.json").write_text(json.dumps({"total": s2}))
    rows = [{"role": "assistant", "text": "[tool_use Read: {}]",
             "usage": {"input_tokens": 1000, "output_tokens": 100}} for _ in range(turns)]
    (d / "transcript.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")


PRICES = {S.IDS[m]: {"input_per_M": 1.0, "cached_input_per_M": 0.1,
                     "cache_write_per_M": 1.25, "output_per_M": 5.0} for m in S.MODELS}


def test_judge_average_is_the_unit(tmp_path):
    cell(tmp_path, "r1", "opus", "single", 80, 76)
    c = S.collect([str(tmp_path / "r1")], PRICES)
    assert c[("opus", "single")][0]["score"] == 78.0


def test_summary_and_t_interval_n3():
    s = S.summarize([70, 80, 90])
    assert s["n"] == 3 and s["mean"] == 80 and abs(s["sd"] - 10) < 1e-9
    half = 4.303 * 10 / math.sqrt(3)
    assert abs(s["lo"] - (80 - half)) < 1e-6 and abs(s["hi"] - (80 + half)) < 1e-6


def test_n1_has_no_interval():
    s = S.summarize([45])
    assert s["n"] == 1 and math.isnan(s["sd"]) and math.isnan(s["lo"])
    assert S.fmt_ci(s) == "45.0 (n=1)"


def test_paired_uses_only_matching_mode_and_repeat(tmp_path):
    cell(tmp_path, "r1", "opus", "single", 80, 80)
    cell(tmp_path, "r1", "sonnet", "single", 60, 60)
    cell(tmp_path, "r2", "opus", "single", 70, 70)
    cell(tmp_path, "r2", "sonnet", "single", 65, 65)
    cell(tmp_path, "r2", "sonnet", "noisy", 50, 50)        # unpaired: opus has no r2 noisy
    c = S.collect([str(tmp_path / "r1"), str(tmp_path / "r2")], PRICES)
    p = S.paired(c, "opus", "sonnet")
    assert p["n"] == 2 and p["mean"] == 12.5 and p["wins"] == 2 and p["ties"] == 0


def test_incomplete_cells_are_skipped_not_zeroed(tmp_path):
    d = tmp_path / "r1" / "haiku" / "single"
    d.mkdir(parents=True)
    (d / "score.json").write_text(json.dumps({"total": 40}))      # no transcript -> not a run
    c = S.collect([str(tmp_path / "r1")], PRICES)
    assert ("haiku", "single") not in c


def test_render_marks_not_run(tmp_path):
    cell(tmp_path, "r1", "fable", "single", 84, 82)
    text = S.render(S.collect([str(tmp_path / "r1")], PRICES))
    assert "| haiku | single | 0 | not run" in text
    assert "| fable | single | 1 | 83.0 (n=1)" in text
