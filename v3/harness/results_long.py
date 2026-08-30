#!/usr/bin/env python3
"""Build the results report for the v3 long-variant runs (bare models; see PROTOCOL-LONG.md).

Reads `<runs>/<model>/<mode>/` for model in {haiku, sonnet, opus, fable} and mode in
{long-notes, long-reread}.

Layout per cell:
  - long-notes only: `ingest/transcript-seg1.jsonl` .. `seg4.jsonl` (the ingest reader's
    per-segment transcripts, reduced by `capture_transcript.py`) and `ingest/notes-1.md` ..
    `notes-4.md` (the retention notes written at each segment boundary; notes-4 is what a
    long-notes batch reader actually sees). long-reread has no ingest phase at all -- its
    "ingest" cost is folded into each batch's own re-read, so there is nothing to load here.
  - both modes: `batch-1/`, `batch-2/`, `batch-3/`, each with `transcript.jsonl` (that batch's
    reader, already concatenated across whatever raw segments produced it), `answers.md`,
    `score.json` and `score-2.json` (schema `{"sections": {...}, "deductions": [...], "total": n}`,
    two independent judgings of that batch against its slice of the key).

A batch's maximum is looked up from `answer-key/batches.md`, which lists item ids and points per
batch. This module does not prescribe one exact markdown dialect for that file (it does not exist
yet at the time of writing); `parse_batch_maxes` accepts, per "## Batch N" section discovered in
the file:
  1. a per-batch point count stated on the heading line itself, e.g. "## Batch 1 (33 points)";
  2. failing that, an explicit "Total: N points" line anywhere in the section body;
  3. failing that, the sum of every "(N points)" parenthetical found in the section body.
Whichever matches first for a given batch wins, so a heading total is never double-counted
against item-level totals underneath it.

Every piece of the report that depends on a missing file renders "pending" for that cell instead
of failing -- cells fill in over time while this report may be run against the tree. A long-reread
cell has no ingest phase at all: that is not "missing", so its ingest column renders "-" (an em
dash), never "pending".
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

MODEL_ROWS = ["haiku", "sonnet", "opus", "fable"]
MODE_COLS = ["long-notes", "long-reread"]
MODEL_IDS = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-5",
    "opus": "claude-opus-5",
    "fable": "claude-fable-5",
}
BATCH_NUMS = [1, 2, 3]
INGEST_SEGMENTS = [1, 2, 3, 4]  # fallback when no ingest dir exists; real segments are discovered by glob


def discover_segments(ingest_dir):
    """Segment indices present under an ingest dir (transcript-seg<i>.jsonl or notes-<i>.md), sorted."""
    import re as _re
    found = set()
    if ingest_dir.exists():
        for f in ingest_dir.iterdir():
            m = _re.match(r"(?:transcript-seg|notes-)(\d+)\.(?:jsonl|md)$", f.name)
            if m:
                found.add(int(m.group(1)))
    return sorted(found) or list(INGEST_SEGMENTS)
TOTAL_POINTS = 100

PENDING = "pending"
DASH = "—"  # long-reread has no ingest phase -- structurally absent, not missing data
NA = "n/a"  # a model with no row in prices.json
INF = "∞"  # cost-per-point at zero score

CAVEAT_PARAGRAPH = (
    "The judge is an Opus subagent, the same model family as the systems under test, which is a "
    "potential source of bias in scoring. Each cell reflects a single run (n = 1), not an average "
    "over repeats. All results in this report are for material version v3.1. Costs are list "
    "price, with cache reads billed at the cached rate. A knowledge-base system run elsewhere "
    "under the same protocol is not one of these cells -- its ingest and per-batch numbers can be "
    "appended to this report by hand as a row named `kb`."
)

_ABSTENTION_RE = re.compile(r"cannot be determined", re.IGNORECASE)
_BATCH_HEADING_RE = re.compile(r"^(#{1,6})\s*Batch\s+(\d+)\b([^\n]*)$", re.IGNORECASE | re.MULTILINE)
_POINTS_RE = re.compile(r"\(\s*(\d+)\s*points?\s*\)", re.IGNORECASE)
_TOTAL_LINE_RE = re.compile(r"(?i)\btotal\b[^\n]{0,40}?(\d+)\s*points?")
# a heading may state its total without parentheses: "## Batch 1 - 34 points"
_HEADING_POINTS_RE = re.compile(r"(\d+)\s*points?\b", re.IGNORECASE)


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


def load_jsonl_rows(path: Path) -> list[dict] | None:
    if not path.is_file():
        return None
    rows = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        return None
    return rows


def load_jsonl_rows_concat(paths: list[Path]) -> list[dict] | None:
    """All rows across all `paths`, in order, or None if any file is missing/unreadable."""
    if not all(p.is_file() for p in paths):
        return None
    rows: list[dict] = []
    for p in paths:
        r = load_jsonl_rows(p)
        if r is None:
            return None
        rows.extend(r)
    return rows


def load_prices(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_batch_maxes(path: Path) -> dict[int, int]:
    """Batch number -> max points, from `answer-key/batches.md`. See module docstring for the
    three formats accepted, tried in order per "## Batch N" section discovered."""
    text = Path(path).read_text(encoding="utf-8")
    headings = list(_BATCH_HEADING_RE.finditer(text))
    maxes: dict[int, int] = {}
    for i, m in enumerate(headings):
        batch_num = int(m.group(2))
        heading_rest = m.group(3) or ""
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]

        heading_points = _POINTS_RE.findall(heading_rest)
        if heading_points:
            maxes[batch_num] = sum(int(p) for p in heading_points)
            continue
        bare = _HEADING_POINTS_RE.findall(heading_rest)
        if bare:
            maxes[batch_num] = sum(int(p) for p in bare)
            continue
        total_match = _TOTAL_LINE_RE.search(body)
        if total_match:
            maxes[batch_num] = int(total_match.group(1))
            continue
        maxes[batch_num] = sum(int(p) for p in _POINTS_RE.findall(body))
    return maxes


def load_cell(runs_dir: Path, model: str, mode: str) -> dict:
    cell_dir = runs_dir / model / mode
    if mode == "long-notes":
        ingest_dir = cell_dir / "ingest"
        segs = discover_segments(ingest_dir)
        ingest_rows = load_jsonl_rows_concat([ingest_dir / f"transcript-seg{i}.jsonl" for i in segs])
        ingest_notes = {i: load_text_or_none(ingest_dir / f"notes-{i}.md") for i in segs}
    else:
        ingest_rows = None
        ingest_notes = None

    batches = {}
    for b in BATCH_NUMS:
        bdir = cell_dir / f"batch-{b}"
        batches[b] = {
            "rows": load_jsonl_rows(bdir / "transcript.jsonl"),
            "answers": load_text_or_none(bdir / "answers.md"),
            "score": load_json_or_none(bdir / "score.json"),
            "score2": load_json_or_none(bdir / "score-2.json"),
        }

    return {"dir": cell_dir, "ingest_rows": ingest_rows, "ingest_notes": ingest_notes, "batches": batches}


def all_cells(runs_dir: Path) -> dict[tuple[str, str], dict]:
    return {(model, mode): load_cell(runs_dir, model, mode) for model in MODEL_ROWS for mode in MODE_COLS}


# --------------------------------------------------------------------------- usage / cost math


def _num(value, default=0):
    return value if isinstance(value, (int, float)) else default


def usage_field(usage: dict | None, key: str) -> float:
    if not usage:
        return 0
    return _num(usage.get(key))


def effort_totals(rows: list[dict]) -> dict:
    """Assistant turns and tool calls in a captured transcript.

    On a subscription plan the dollar figures are notional; turns and calls are what the
    run actually spends, and they are what a rate limit is denominated in. A "turn" is one
    assistant message; a "call" is one tool use inside those messages.
    """
    turns = calls = 0
    for row in rows:
        if row.get("role") != "assistant":
            continue
        turns += 1
        if "[tool_use " in (row.get("text") or ""):
            calls += 1
    return {"turns": turns, "calls": calls}


def token_totals(rows: list[dict]) -> dict:
    raw_input = cache_read = cache_write = output = 0.0
    for row in rows:
        if row.get("role") != "assistant":
            continue
        usage = row.get("usage") or {}
        raw_input += usage_field(usage, "input_tokens")
        cache_read += usage_field(usage, "cache_read_input_tokens")
        cache_write += usage_field(usage, "cache_creation_input_tokens")
        output += usage_field(usage, "output_tokens")
    return {
        "raw_input": raw_input,
        "cache_read": cache_read,
        "cache_write": cache_write,
        "output": output,
        "total_tokens": raw_input + cache_read + cache_write + output,
    }


def cost_usd(totals: dict, model_id: str, prices: dict) -> float | None:
    """List-price cost of one transcript's usage, or None if `model_id` has no row in `prices`."""
    p = prices.get(model_id)
    if p is None:
        return None
    per = 1_000_000
    return (
        totals["raw_input"] * p["input_per_M"] / per
        + totals["cache_read"] * p["cached_input_per_M"] / per
        + totals["cache_write"] * p["cache_write_per_M"] / per
        + totals["output"] * p["output_per_M"] / per
    )


def count_abstentions(text: str) -> int:
    return len(_ABSTENTION_RE.findall(text))


def section_totals(score: dict) -> tuple[dict[str, float], float]:
    sections: dict[str, float] = {}
    for sec, body in (score.get("sections") or {}).items():
        sections[sec] = _num((body or {}).get("total", 0))
    deductions_total = sum(_num((d or {}).get("points", 0)) for d in (score.get("deductions") or []))
    return sections, deductions_total


# --------------------------------------------------------------------------- cost-cell helpers
#
# Every cost figure is computed as a (kind, value) pair:
#   "ok"      -- value is a known float
#   "pending" -- the underlying transcript is missing
#   "na"      -- the transcript is there but the model has no row in prices.json
#   "dash"    -- structurally absent (long-reread has no ingest phase); counts as 0 in sums


def _cost_cell(rows: list[dict] | None, model_id: str, prices: dict) -> tuple[str, float | None]:
    if rows is None:
        return ("pending", None)
    cost = cost_usd(token_totals(rows), model_id, prices)
    if cost is None:
        return ("na", None)
    return ("ok", cost)


def _combine_costs(kinds_values: list[tuple[str, float | None]]) -> tuple[str, float | None]:
    total = 0.0
    saw_na = False
    for kind, value in kinds_values:
        if kind == "pending":
            return ("pending", None)
        if kind == "na":
            saw_na = True
            continue
        if kind == "dash":
            continue
        total += value
    if saw_na:
        return ("na", None)
    return ("ok", total)


def ingest_cost_cell(cell: dict, mode: str, model_id: str, prices: dict) -> tuple[str, float | None]:
    if mode != "long-notes":
        return ("dash", None)
    return _cost_cell(cell["ingest_rows"], model_id, prices)


def batch_cost_cell(cell: dict, batch: int, model_id: str, prices: dict) -> tuple[str, float | None]:
    return _cost_cell(cell["batches"][batch]["rows"], model_id, prices)


# --------------------------------------------------------------------------- formatting


def _fmt_num(value) -> str:
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.1f}"
    return str(value)


def _fmt_cost(value: float) -> str:
    return f"{value:.4f}"


def _kind_str(kind: str, value: float | None) -> str:
    if kind == "pending":
        return PENDING
    if kind == "dash":
        return DASH
    if kind == "na":
        return NA
    return _fmt_cost(value)


# --------------------------------------------------------------------------- table renders


def render_cost_curve_table(cells: dict[tuple[str, str], dict], prices: dict) -> str:
    lines = ["## Cost curve", "", "| Model | Mode | Ingest cost (USD, tokens) | Batch 1 | Batch 2 | Batch 3 | Total |", "|---|---|---|---|---|---|---|"]
    for model in MODEL_ROWS:
        model_id = MODEL_IDS[model]
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            ingest_kv = ingest_cost_cell(cell, mode, model_id, prices)
            batch_kvs = [batch_cost_cell(cell, b, model_id, prices) for b in BATCH_NUMS]
            total_kv = _combine_costs([ingest_kv] + batch_kvs)

            if ingest_kv[0] == "dash":
                ingest_str = DASH
            elif ingest_kv[0] == "pending":
                ingest_str = PENDING
            else:
                tokens = _fmt_num(token_totals(cell["ingest_rows"])["total_tokens"])
                ingest_str = f"{_kind_str(*ingest_kv)} ({tokens})"

            row = [model, mode, ingest_str] + [_kind_str(*kv) for kv in batch_kvs] + [_kind_str(*total_kv)]
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_scores_table(cells: dict[tuple[str, str], dict], batch_maxes: dict[int, int]) -> str:
    lines = ["## Scores", "", "| Model | Mode | Batch 1 | Batch 2 | Batch 3 | Sum (/100) |", "|---|---|---|---|---|---|"]
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            batch_strs = []
            totals1 = []
            totals2 = []
            any_missing = False
            any_missing2 = False
            for b in BATCH_NUMS:
                score = cell["batches"][b]["score"]
                score2 = cell["batches"][b]["score2"]
                if score is None:
                    batch_strs.append(PENDING)
                    any_missing = True
                    any_missing2 = True
                    continue
                total1 = score.get("total", 0)
                totals1.append(total1)
                max_b = batch_maxes.get(b)
                max_s = str(max_b) if max_b is not None else "?"
                base = f"{_fmt_num(total1)}/{max_s}"
                if score2 is not None:
                    total2 = score2.get("total", 0)
                    totals2.append(total2)
                    if total2 != total1:
                        base += f" ({_fmt_num(total2)})"
                else:
                    any_missing2 = True
                batch_strs.append(base)

            if any_missing:
                sum_str = PENDING
            else:
                sum1 = sum(totals1)
                sum_str = f"{_fmt_num(sum1)}/{TOTAL_POINTS}"
                if not any_missing2:
                    sum2 = sum(totals2)
                    if sum2 != sum1:
                        sum_str += f" ({_fmt_num(sum2)})"

            row = [model, mode] + batch_strs + [sum_str]
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_section_profile_table(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Section profile", "", "| Model | Mode | Batch | Sections | Deductions |", "|---|---|---|---|---|"]
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            for b in BATCH_NUMS:
                score = cell["batches"][b]["score"]
                label = f"batch-{b}"
                if score is None:
                    lines.append(f"| {model} | {mode} | {label} | {PENDING} | {PENDING} |")
                    continue
                sections, deductions_total = section_totals(score)
                profile = " · ".join(f"{k} {_fmt_num(v)}" for k, v in sorted(sections.items())) if sections else DASH
                lines.append(f"| {model} | {mode} | {label} | {profile} | {_fmt_num(deductions_total)} |")
    return "\n".join(lines)


def render_cost_per_point_table(cells: dict[tuple[str, str], dict], prices: dict) -> str:
    lines = ["## Cost per point", "", "| Model | Mode | Batch 1 $/pt | Batch 2 $/pt | Batch 3 $/pt | Cumulative $/pt |", "|---|---|---|---|---|---|"]
    for model in MODEL_ROWS:
        model_id = MODEL_IDS[model]
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            ingest_kv = ingest_cost_cell(cell, mode, model_id, prices)

            per_batch_strs = []
            usable = []  # (cost, score_total) pairs usable for the cumulative figure
            for b in BATCH_NUMS:
                cost_kv = batch_cost_cell(cell, b, model_id, prices)
                score = cell["batches"][b]["score"]
                if cost_kv[0] == "pending" or score is None:
                    per_batch_strs.append(PENDING)
                    continue
                if cost_kv[0] == "na":
                    per_batch_strs.append(NA)
                    continue
                total = score.get("total", 0)
                cost = cost_kv[1]
                if total == 0:
                    per_batch_strs.append(INF)
                else:
                    per_batch_strs.append(_fmt_cost(cost / total))
                usable.append((cost, total))

            if not usable:
                cumulative_str = PENDING
            else:
                ingest_component = ingest_kv[1] if ingest_kv[0] == "ok" else 0.0
                total_cost = ingest_component + sum(c for c, _ in usable)
                total_score = sum(s for _, s in usable)
                cumulative_str = INF if total_score == 0 else _fmt_cost(total_cost / total_score)

            row = [model, mode] + per_batch_strs + [cumulative_str]
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_judge_stability(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Judge stability", ""]
    diffs = []
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            for b in BATCH_NUMS:
                score = cell["batches"][b]["score"]
                score2 = cell["batches"][b]["score2"]
                if score is None or score2 is None:
                    continue
                diff = abs(score.get("total", 0) - score2.get("total", 0))
                diffs.append(diff)
                lines.append(f"- {model}/{mode}/batch-{b}: |total - total2| = {_fmt_num(diff)}")
    if not diffs:
        lines.append("- No batch has both score.json and score-2.json yet.")
    else:
        lines.append("")
        lines.append(f"Max across all judged batches: {_fmt_num(max(diffs))}")
    return "\n".join(lines)


def render_notes_section(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Notes", ""]

    lines.append("### Ingest notes word counts")
    lines.append("")
    lines.append("| Model | Mode | ingest notes (words per segment, in order) |")
    lines.append("|---|---|---|")
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            if mode != "long-notes" or not cell.get("ingest_notes"):
                lines.append(f"| {model} | {mode} | {DASH} |")
                continue
            parts = []
            for i in sorted(cell["ingest_notes"]):
                txt = cell["ingest_notes"][i]
                parts.append(DASH if txt is None else f"{len(txt.split()):,}")
            lines.append(f"| {model} | {mode} | {' · '.join(parts)} |")

    lines.append("")
    lines.append('### Abstentions ("cannot be determined")')
    lines.append("")
    lines.append("| Model | Mode | Batch 1 | Batch 2 | Batch 3 |")
    lines.append("|---|---|---|---|---|")
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            counts = []
            for b in BATCH_NUMS:
                answers = cell["batches"][b]["answers"]
                counts.append(PENDING if answers is None else str(count_abstentions(answers)))
            lines.append(f"| {model} | {mode} | " + " | ".join(counts) + " |")

    lines.append("")
    lines.append("### Caveats")
    lines.append("")
    lines.append(CAVEAT_PARAGRAPH)

    return "\n".join(lines)



def render_effort_table(cells: dict[tuple[str, str], dict]) -> str:
    """Turns, tool calls and tokens per cell -- the subscription-plan currency."""
    lines = ["## Effort (turns, tool calls, tokens)", "",
             "Dollars are notional on a subscription plan; these are what a run actually spends.",
             "",
             "| Model | Mode | Phase | Assistant turns | Tool calls | Input tokens | Output tokens |",
             "|---|---|---|---|---|---|---|"]
    for model in MODEL_ROWS:
        for mode in MODE_COLS:
            cell = cells[(model, mode)]
            phases = [("ingest", cell.get("ingest_rows") or [])]
            for b in BATCH_NUMS:
                phases.append((f"batch-{b}", (cell.get("batches") or {}).get(b, {}).get("rows") or []))
            for phase, rows in phases:
                if not rows:
                    label = DASH if (phase == "ingest" and mode == "long-reread") else PENDING
                    lines.append(f"| {model} | {mode} | {phase} | {label} | {label} | {label} | {label} |")
                    continue
                e = effort_totals(rows)
                t = token_totals(rows)
                inp = t["raw_input"] + t["cache_read"] + t["cache_write"]
                lines.append(f"| {model} | {mode} | {phase} | {e['turns']} | {e['calls']} | "
                             f"{_fmt_num(inp)} | {_fmt_num(t['output'])} |")
    return "\n".join(lines)


def render_report(runs_dir: Path, prices: dict, batch_maxes: dict[int, int], date_str: str) -> str:
    cells = all_cells(runs_dir)
    parts = [
        "# Story test v3 -- long variant",
        "",
        f"Generated: {date_str}",
        "",
        render_cost_curve_table(cells, prices),
        "",
        render_effort_table(cells),
        "",
        render_scores_table(cells, batch_maxes),
        "",
        render_section_profile_table(cells),
        "",
        render_cost_per_point_table(cells, prices),
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
    parser = argparse.ArgumentParser(description="Build the v3 long-variant results report.")
    parser.add_argument("--runs", required=True, help="Directory containing <model>/<mode>/ run directories.")
    parser.add_argument("--out", required=True, help="Markdown file to write.")
    parser.add_argument("--prices", default=None, help="Path to prices.json (default: prices.json next to this script).")
    parser.add_argument("--batches", required=True, help="Path to answer-key/batches.md (item ids and points per batch).")
    parser.add_argument("--date", default=None, help="Generation date to print (default: today, ISO format).")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    runs_dir = Path(args.runs)
    prices_path = Path(args.prices) if args.prices else default_prices_path()
    prices = load_prices(prices_path)
    batch_maxes = parse_batch_maxes(Path(args.batches))
    date_str = args.date or date.today().isoformat()

    report_text = render_report(runs_dir, prices, batch_maxes, date_str)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text, encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
