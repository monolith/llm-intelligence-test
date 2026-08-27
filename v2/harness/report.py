#!/usr/bin/env python3
"""Build the 12-cell (model x mode) results table from a tree of run directories.

Expects `<runs>/<model>/<mode>/run.json` (written by run_v2.py) and, once judged,
`<runs>/<model>/<mode>/score.json` (written by judge.py). Missing cells render as "-"
rather than failing, since the 12 cells fill in over time.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from judge import section_totals

MODEL_ORDER = ["claude-haiku-4-5", "claude-sonnet-5", "claude-opus-5", "claude-fable-5"]
MODEL_LABELS = {
    "claude-haiku-4-5": "haiku",
    "claude-sonnet-5": "sonnet",
    "claude-opus-5": "opus",
    "claude-fable-5": "fable",
}
MODES = ["single", "sequential", "noisy"]
DEFAULT_SECTIONS = list("ABCDEFG")

DASH = "—"


def load_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def discover_cell(runs_dir: Path, model: str, mode: str) -> dict:
    cell_dir = runs_dir / model / mode
    return {
        "dir": cell_dir,
        "run": load_json(cell_dir / "run.json"),
        "score": load_json(cell_dir / "score.json"),
    }


def cells_for(runs_dir: Path) -> dict[tuple[str, str], dict]:
    return {(model, mode): discover_cell(runs_dir, model, mode) for model in MODEL_ORDER for mode in MODES}


def _fmt(value, digits: int | None = None) -> str:
    if value is None:
        return DASH
    if digits is not None and isinstance(value, (int, float)):
        return f"{value:.{digits}f}"
    return str(value)


def render_total_table(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Total (out of 100)", "", "| Model | " + " | ".join(MODES) + " |", "|---|" + "---|" * len(MODES)]
    for model in MODEL_ORDER:
        row = [MODEL_LABELS[model]]
        for mode in MODES:
            score = cells[(model, mode)]["score"]
            total = section_totals(score["canonical"])["total"] if score else None
            row.append(_fmt(total))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_section_profile_table(cells: dict[tuple[str, str], dict]) -> str:
    sections = sorted(
        {
            section
            for cell in cells.values()
            if cell["score"]
            for section in cell["score"]["canonical"].get("sections", {})
        }
    ) or DEFAULT_SECTIONS

    headers = ["Model", "Mode"] + sections + ["Deductions", "Total"]
    lines = [
        "## Section profile (A–G)",
        "",
        "| " + " | ".join(headers) + " |",
        "|" + "---|" * len(headers),
    ]
    for model in MODEL_ORDER:
        for mode in MODES:
            score = cells[(model, mode)]["score"]
            totals = section_totals(score["canonical"]) if score else {}
            row = [MODEL_LABELS[model], mode]
            row += [_fmt(totals.get(section)) for section in sections]
            row.append(_fmt(totals.get("deductions")))
            row.append(_fmt(totals.get("total")))
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_cost_table(cells: dict[tuple[str, str], dict]) -> str:
    headers = ["Model", "Mode", "Input tokens", "Output tokens", "Cache read", "Cache write", "Cost (USD)", "Wall-clock (s)", "Requests", "Compactions"]
    lines = ["## Tokens, cost, wall-clock, requests", "", "| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for model in MODEL_ORDER:
        for mode in MODES:
            run = cells[(model, mode)]["run"]
            totals = run.get("totals", {}) if run else {}
            row = [
                MODEL_LABELS[model],
                mode,
                _fmt(totals.get("input_tokens")),
                _fmt(totals.get("output_tokens")),
                _fmt(totals.get("cache_read_input_tokens")),
                _fmt(totals.get("cache_creation_input_tokens")),
                _fmt(totals.get("cost_usd"), digits=4) if run else DASH,
                _fmt(run.get("wall_clock_s"), digits=1) if run else DASH,
                _fmt(run.get("num_requests")) if run else DASH,
                _fmt(run.get("num_compactions")) if run else DASH,
            ]
            lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def render_judge_stability(cells: dict[tuple[str, str], dict]) -> str:
    lines = ["## Judge stability", ""]
    diffs = []
    any_scored = False
    for model in MODEL_ORDER:
        for mode in MODES:
            score = cells[(model, mode)]["score"]
            if not score:
                continue
            any_scored = True
            diff = score.get("max_abs_diff", 0.0)
            diffs.append(diff)
            lines.append(f"- {MODEL_LABELS[model]}/{mode}: max |Δtotal| across judgings = {diff}")
    if not any_scored:
        lines.append("- No runs judged yet.")
    else:
        lines.append("")
        lines.append(f"Max across all judged runs: {max(diffs)}")
    return "\n".join(lines)


def render_kappa_section(runs_dir: Path) -> str:
    lines = ["## Hand-scoring κ", ""]
    kappa_path = runs_dir / "kappa.json"
    kappa = load_json(kappa_path)
    if kappa is None:
        lines.append(
            "Not yet computed. Hand-score two runs, compute Cohen's κ per section against the "
            f"judge, and write the result to `{kappa_path}`."
        )
        return "\n".join(lines)

    if isinstance(kappa, dict) and isinstance(kappa.get("kappa"), dict):
        lines.append("| Section | κ |")
        lines.append("|---|---|")
        for section, value in kappa["kappa"].items():
            lines.append(f"| {section} | {_fmt(value, digits=2) if isinstance(value, (int, float)) else value} |")
        extra = {k: v for k, v in kappa.items() if k != "kappa"}
        if extra:
            lines.append("")
            for key, value in extra.items():
                lines.append(f"- {key}: {value}")
    else:
        lines.append("```json")
        lines.append(json.dumps(kappa, indent=2, ensure_ascii=False))
        lines.append("```")
    return "\n".join(lines)


def render_report(runs_dir: Path) -> str:
    cells = cells_for(runs_dir)
    parts = [
        "# Results",
        "",
        render_total_table(cells),
        "",
        render_section_profile_table(cells),
        "",
        render_cost_table(cells),
        "",
        render_judge_stability(cells),
        "",
        render_kappa_section(runs_dir),
        "",
    ]
    return "\n".join(parts)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the results table from a tree of run directories.")
    parser.add_argument("--runs", required=True, help="Directory containing <model>/<mode>/ run directories.")
    parser.add_argument("--out", required=True, help="Markdown file to write.")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    runs_dir = Path(args.runs)
    report_text = render_report(runs_dir)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text, encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
