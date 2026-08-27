#!/usr/bin/env python3
"""Build the results report for the orchestrated (subagent-dispatched) v2.1 runs.

Reads `<runs>/<model>/<mode>/` for model in {haiku, sonnet, opus, fable} and mode in
{single, sequential, noisy}, as produced by the orchestration path documented in
`ORCHESTRATION.md` (not the direct-API `run_v2.py` path, which uses a different score.json
shape). Each finished cell has `answers.md`, two independent judgings (`score.json`,
`score-2.json`, schema `{"sections": {...}, "deductions": [...], "total": n}`), and either
`transcript.jsonl` (single/sequential) or `transcript-seg1.jsonl` .. `transcript-seg3.jsonl`
(noisy) written by `capture_transcript.py`; noisy cells also have `notes-after-r04.md` /
`notes-after-r08.md`. Cells not yet finished are missing some or all of these files -- every
piece of the report that depends on a missing file renders "pending" for that cell instead of
failing, since the 12 cells fill in over time while this report may be run against the tree.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

MODEL_ROWS = ["haiku", "sonnet", "opus", "fable"]
MODE_COLS = ["single", "sequential", "noisy"]
MODEL_IDS = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
    "fable": "claude-fable-5",
}
SECTIONS = list("ABCDEFG")
PENDING = "pending"
NA = "n/a"

CAVEAT_PARAGRAPH = (
    "The judge is an Opus subagent, the same model family as the systems under test, which is a "
    "potential source of bias in scoring. Sampling is not deterministic: each cell reflects a "
    "single run (n = 1), not an average over repeats. All results in this report are for version "
    "{label} of the story test material."
)

_ABSTENTION_RE = re.compile(r"cannot be determined", re.IGNORECASE)


# --------------------------------------------------------------------------- loading


def load_json_or_none(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_text_or_none(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def transcript_paths(cell_dir: Path, mode: str) -> list[Path]:
    if mode == "noisy":
        return [cell_dir / f"transcript-seg{i}.jsonl" for i in (1, 2, 3)]
    return [cell_dir / "transcript.jsonl"]


def load_transcript_segments(cell_dir: Path, mode: str) -> list[list[dict]] | None:
    """One row-list per segment, in order, or None if any required file is missing/unreadable."""
    paths = transcript_paths(cell_dir, mode)
    if not all(p.is_file() for p in paths):
        return None
    segments: list[list[dict]] = []
    for p in paths:
        rows = []
        try:
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            return None
        segments.append(rows)
    return segments


def load_cell(runs_dir: Path, model: str, mode: str) -> dict:
    cell_dir = runs_dir / model / mode
    return {
        "dir": cell_dir,
        "answers": load_text_or_none(cell_dir / "answers.md"),
        "score": load_json_or_none(cell_dir / "score.json"),
        "score2": load_json_or_none(cell_dir / "score-2.json"),
        "segments": load_transcript_segments(cell_dir, mode),
        "notes_r04": load_text_or_none(cell_dir / "notes-after-r04.md") if mode == "noisy" else None,
        "notes_r08": load_text_or_none(cell_dir / "notes-after-r08.md") if mode == "noisy" else None,
    }


def all_cells(runs_dir: Path) -> dict[tuple[str, str], dict]:
    return {(model, mode): load_cell(runs_dir, model, mode) for model in MODEL_ROWS for mode in MODE_COLS}


def load_prices(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- score math


def section_totals(score: dict) -> dict[str, float]:
    totals: dict[str, float] = {}
    for section, body in (score.get("sections") or {}).items():
        totals[section] = (body or {}).get("total", 0)
    totals["deductions"] = sum((d or {}).get("points", 0) for d in (score.get("deductions") or []))
    totals["total"] = score.get("total", 0)
    return totals


# --------------------------------------------------------------------------- transcript math


def _num(value, default=0):
    return value if isinstance(value, (int, float)) else default


def usage_field(usage: dict | None, key: str) -> float:
    if not usage:
        return 0
    return _num(usage.get(key))


def thinking_tokens_of(usage: dict | None) -> float:
    if not usage:
        return 0
    details = usage.get("output_tokens_details")
    if not isinstance(details, dict):
        return 0
    return _num(details.get("thinking_tokens"))


def parse_timestamp(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def compute_cell_stats(segments: list[list[dict]]) -> dict:
    """Aggregate assistant-row usage and wall-clock (summed per segment) across all segments."""
    assistant_turns = 0
    raw_input_tokens = 0.0
    cache_read_tokens = 0.0
    cache_write_tokens = 0.0
    output_tokens = 0.0
    thinking_tokens = 0.0
    wall_clock_s = 0.0

    for rows in segments:
        timestamps = []
        for row in rows:
            ts = row.get("timestamp")
            if ts:
                try:
                    timestamps.append(parse_timestamp(ts))
                except ValueError:
                    pass
            if row.get("role") == "assistant":
                assistant_turns += 1
                usage = row.get("usage") or {}
                raw_input_tokens += usage_field(usage, "input_tokens")
                cache_read_tokens += usage_field(usage, "cache_read_input_tokens")
                cache_write_tokens += usage_field(usage, "cache_creation_input_tokens")
                output_tokens += usage_field(usage, "output_tokens")
                thinking_tokens += thinking_tokens_of(usage)
        if timestamps:
            wall_clock_s += (max(timestamps) - min(timestamps)).total_seconds()

    return {
        "assistant_turns": assistant_turns,
        "raw_input_tokens": raw_input_tokens,
        "cache_read_tokens": cache_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "input_tokens_total": raw_input_tokens + cache_read_tokens + cache_write_tokens,
        "output_tokens": output_tokens,
        "thinking_tokens": thinking_tokens,
        "segments": len(segments),
        "wall_clock_s": wall_clock_s,
    }


def cost_usd(stats: dict, model_id: str, prices: dict) -> float | None:
    """List-price cost of one cell, or None if `model_id` has no row in `prices`."""
    p = prices.get(model_id)
    if p is None:
        return None
    per = 1_000_000
    return (
        stats["raw_input_tokens"] * p["input_per_M"] / per
        + stats["cache_read_tokens"] * p["cached_input_per_M"] / per
        + stats["cache_write_tokens"] * p["cache_write_per_M"] / per
        + stats["output_tokens"] * p["output_per_M"] / per
    )


def count_abstentions(text: str) -> int:
    return len(_ABSTENTION_RE.findall(text))


# --------------------------------------------------------------------------- rendering helpers


def _fmt_num(value) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"
    return str(value)


def _fmt_seconds(value: float) -> str:
    return f"{value:.1f}"


def _fmt_cost(value: float) -> str:
    return f"{value:.4f}"


# --------------------------------------------------------------------------- table renders


def render_totals_table(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Table 1 -- totals (score.json, with score-2.json in parentheses when it differs)", ""]
    lines.append("| Model | " + " | ".join(MODE_COLS) + " |")
    lines.append("|---|" + "---|" * len(MODE_COLS))
    for model in MODEL_ROWS:
        row = [model]
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            score = cell["score"]
            if score is None:
                row.append(PENDING)
                continue
            total = score.get("total", 0)
            score2 = cell["score2"]
            if score2 is not None:
                total2 = score2.get("total", 0)
                if total2 != total:
                    row.append(f"{_fmt_num(total)} ({_fmt_num(total2)})")
                else:
                    row.append(_fmt_num(total))
            else:
                row.append(_fmt_num(total))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_section_profile_table(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Table 2 -- section profile per cell", ""]
    lines.append("| Model | Mode | Sections | Deductions |")
    lines.append("|---|---|---|---|")
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            score = cell["score"]
            if score is None:
                lines.append(f"| {model} | {mode} | {PENDING} | {PENDING} |")
                continue
            totals = section_totals(score)
            profile = " · ".join(f"{s} {_fmt_num(totals.get(s, 0))}" for s in SECTIONS)
            lines.append(f"| {model} | {mode} | {profile} | {_fmt_num(totals['deductions'])} |")
    return "\n".join(lines)


def render_cost_table(cells: dict[tuple[str, str], dict], prices: dict) -> str:
    headers = ["Model", "Mode", "Assistant turns", "Input tokens", "Output tokens", "Thinking tokens", "Segments", "Wall-clock (s)", "Cost (USD)"]
    lines = ["## Table 3 -- cost and volume per cell", "", "| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            segments = cell["segments"]
            if segments is None:
                lines.append("| " + " | ".join([model, mode] + [PENDING] * (len(headers) - 2)) + " |")
                continue
            stats = compute_cell_stats(segments)
            model_id = MODEL_IDS[model]
            cost = cost_usd(stats, model_id, prices)
            cost_str = _fmt_cost(cost) if cost is not None else NA
            row = [
                model,
                mode,
                _fmt_num(stats["assistant_turns"]),
                _fmt_num(stats["input_tokens_total"]),
                _fmt_num(stats["output_tokens"]),
                _fmt_num(stats["thinking_tokens"]),
                _fmt_num(stats["segments"]),
                _fmt_seconds(stats["wall_clock_s"]),
                cost_str,
            ]
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_judge_stability(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Judge stability", ""]
    diffs = []
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            score, score2 = cell["score"], cell["score2"]
            if score is None or score2 is None:
                continue
            diff = abs(score.get("total", 0) - score2.get("total", 0))
            diffs.append(diff)
            lines.append(f"- {model}/{mode}: |total - total2| = {_fmt_num(diff)}")
    if not diffs:
        lines.append("- No cell has both score.json and score-2.json yet.")
    else:
        lines.append("")
        lines.append(f"Max across all judged cells: {_fmt_num(max(diffs))}")
    return "\n".join(lines)


def render_notes_section(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Notes", ""]

    lines.append('### Abstentions ("cannot be determined")')
    lines.append("")
    lines.append("| Model | Mode | Count |")
    lines.append("|---|---|---|")
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            answers = cells[(model, mode)]["answers"]
            count = PENDING if answers is None else str(count_abstentions(answers))
            lines.append(f"| {model} | {mode} | {count} |")

    lines.append("")
    lines.append("### Noisy-mode notes word counts")
    lines.append("")
    lines.append("| Model | notes-after-r04.md | notes-after-r08.md |")
    lines.append("|---|---|---|")
    for model in MODEL_ROWS:
        cell = cells[(model, "noisy")]
        r04 = cell["notes_r04"]
        r08 = cell["notes_r08"]
        r04_count = PENDING if r04 is None else str(len(r04.split()))
        r08_count = PENDING if r08 is None else str(len(r08.split()))
        lines.append(f"| {model} | {r04_count} | {r08_count} |")

    lines.append("")
    lines.append("### Caveats")
    lines.append("")
    lines.append(CAVEAT_PARAGRAPH)

    return "\n".join(lines)


def render_report(runs_dir: Path, prices: dict, date_str: str, label: str = "2.1") -> str:
    cells = all_cells(runs_dir)
    parts = [
        f"# Story test {label} -- orchestrated runs",
        "",
        f"Generated: {date_str}",
        "",
        render_totals_table(cells),
        "",
        render_section_profile_table(cells),
        "",
        render_cost_table(cells, prices),
        "",
        render_judge_stability(cells),
        "",
        render_notes_section(cells),
        "",
    ]
    return "\n".join(parts)


# --------------------------------------------------------------------------- CLI


def default_prices_path() -> Path:
    return Path(__file__).resolve().parent / "prices.json"


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the orchestrated-run results report.")
    parser.add_argument("--runs", required=True, help="Directory containing <model>/<mode>/ run directories.")
    parser.add_argument("--out", required=True, help="Markdown file to write.")
    parser.add_argument("--prices", default=None, help="Path to prices.json (default: prices.json next to this script).")
    parser.add_argument("--date", default=None, help="Generation date to print (default: today, ISO format).")
    parser.add_argument("--label", default="2.1", help="Material version shown in the title and caveat (e.g. 2.1, 3.0).")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    runs_dir = Path(args.runs)
    prices_path = Path(args.prices) if args.prices else default_prices_path()
    prices = load_prices(prices_path)
    date_str = args.date or date.today().isoformat()

    report_text = render_report(runs_dir, prices, date_str, args.label)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text, encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
