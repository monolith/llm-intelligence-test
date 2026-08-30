"""read_coverage must credit every read in a parallel batch, and only those.

A reader may issue several Reads in one turn; their results come back in order.
Pairing one call to one result at a time drops all but the last of each batch and
reports material as unread that was read — which is how this checker first
accused fable of skipping 200 lines it had in fact read.
"""
import json
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
SCRIPT = HARNESS / "read_coverage.py"
DOC = "/tmp/doc.md"


def build(tmp_path, model, seg, steps, events):
    d = tmp_path / "runs" / model / "long-notes" / "ingest"
    d.mkdir(parents=True)
    (d / f"segment-{seg}.md").write_text("\n".join(
        f"{i}. Read `{DOC}` lines {a}–{a+n-1} (offset {a}, limit {n}) — acknowledge."
        for i, (a, n) in enumerate(steps, 1)) + "\n")
    with open(d / f"transcript-seg{seg}.jsonl", "w") as fh:
        for role, text in events:
            fh.write(json.dumps({"role": role, "text": text}) + "\n")
    return d


def call(off, lim):
    return ("assistant",
            '[tool_use Read: {"file_path": "%s", "offset": %d, "limit": %d}]' % (DOC, off, lim))


def result(text="1\tcontent"):
    return ("user", f"[tool_result: {text}]")


def run(tmp_path, model):
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--model", model, "--only-gaps"],
        capture_output=True, text=True, check=True)
    return out.stdout.strip()


def test_parallel_batch_is_fully_credited(tmp_path):
    """Two calls in one turn, then two results: both spans count as read."""
    build(tmp_path, "m", 1, [(1, 200), (201, 300)],
          [call(1, 200), call(201, 300), result(), result()])
    assert run(tmp_path, "m") == ""


def test_gap_is_still_reported(tmp_path):
    build(tmp_path, "m", 1, [(1, 200), (201, 300)],
          [call(1, 200), result()])
    out = run(tmp_path, "m")
    assert "missing 300 lines" in out and "(201, 500)" in out


def test_cap_failure_is_not_credited(tmp_path):
    """A read whose result is the token-cap refusal did not deliver its span."""
    build(tmp_path, "m", 1, [(1, 200), (201, 300)],
          [call(1, 200), call(201, 300), result(),
           result("File content (30086 tokens) exceeds maximum allowed tokens (25000).")])
    out = run(tmp_path, "m")
    assert "missing 300 lines" in out


def test_retry_in_halves_closes_the_gap(tmp_path):
    """The recovery we now instruct readers to perform must read as complete."""
    build(tmp_path, "m", 1, [(1, 400)],
          [call(1, 400), result("exceeds maximum allowed tokens (25000)"),
           call(1, 200), result(), call(201, 200), result()])
    assert run(tmp_path, "m") == ""
