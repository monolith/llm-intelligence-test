"""The splitter must respect BOTH caps: line count and bytes.

Byte awareness is not decorative — a 276-line notes file was 30,086 tokens and
its prescribed read failed, costing that reader its entire carried memory.
"""
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
SCRIPT = HARNESS / "split_big_reads.py"

STEP = "{n}. Read `{p}` lines {a}–{b} (offset {a}, limit {lim}) — acknowledge."


def run(tmp_path, target, off, lim, *extra):
    seg = tmp_path / "segment-1.md"
    seg.write_text(STEP.format(n=1, p=target, a=off, b=off + lim - 1, lim=lim) + "\n")
    out = subprocess.run([sys.executable, str(SCRIPT), str(seg), *extra],
                         capture_output=True, text=True, check=True).stdout
    return seg.read_text().strip().split("\n"), out


def parse(lines):
    got = []
    for line in lines:
        if not line.strip():
            continue
        off = int(line.split("(offset ")[1].split(",")[0])
        lim = int(line.split("limit ")[1].split(")")[0])
        got.append((off, lim))
    return got


def test_long_lines_split_by_bytes(tmp_path):
    """Few lines, each enormous: the line cap alone would let this through."""
    f = tmp_path / "notes.md"
    f.write_text("".join("x" * 999 + "\n" for _ in range(100)))   # 100 lines, ~100 KB
    lines, _ = run(tmp_path, f, 1, 100, "--max-bytes", "40000")
    got = parse(lines)
    assert len(got) > 1
    for _off, lim in got:
        assert lim * 1000 <= 40000 + 1000


def test_many_short_lines_split_by_lines(tmp_path):
    """Many tiny lines: the byte cap alone would let this through."""
    f = tmp_path / "noise.md"
    f.write_text("".join("a\n" for _ in range(900)))
    lines, _ = run(tmp_path, f, 1, 900, "--max-lines", "300")
    got = parse(lines)
    assert [lim for _o, lim in got] == [300, 300, 300]


def test_split_is_contiguous_and_total_preserving(tmp_path):
    f = tmp_path / "notes.md"
    f.write_text("".join("y" * 500 + "\n" for _ in range(200)))
    lines, _ = run(tmp_path, f, 11, 190, "--max-bytes", "40000")
    got = parse(lines)
    assert got[0][0] == 11
    assert sum(lim for _o, lim in got) == 190
    for (o1, l1), (o2, _l2) in zip(got, got[1:]):
        assert o1 + l1 == o2                      # no gap, no overlap


def test_small_read_is_left_alone(tmp_path):
    f = tmp_path / "small.md"
    f.write_text("".join("short line\n" for _ in range(50)))
    lines, _ = run(tmp_path, f, 1, 50)
    assert parse(lines) == [(1, 50)]


def test_missing_file_falls_back_to_line_cap(tmp_path):
    """A read of a file we cannot measure still gets the line cap, not a crash."""
    lines, _ = run(tmp_path, tmp_path / "absent.md", 1, 700, "--max-lines", "300")
    assert parse(lines) == [(1, 300), (301, 300), (601, 100)]
