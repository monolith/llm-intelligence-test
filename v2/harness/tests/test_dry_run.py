"""--dry-run without credentials: prints counts, exits 2, never touches --out."""
from __future__ import annotations

from pathlib import Path

import run_v2


def test_dry_run_exits_2_without_credentials(sample_inputs_dir, monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Point .env loading at an empty scratch dir so a real repo .env can never leak into this test.
    monkeypatch.setattr(run_v2, "repo_root_from", lambda _file: tmp_path / "no-such-repo")

    out_dir = tmp_path / "out"
    argv = [
        "--model", "fake-model",
        "--mode", "single",
        "--out", str(out_dir),
        "--dry-run",
        "--retellings-dir", str(sample_inputs_dir["retellings_dir"]),
        "--questions", str(sample_inputs_dir["questions_path"]),
        "--noise-dir", str(sample_inputs_dir["noise_dir"]),
        "--noise-questions", str(sample_inputs_dir["noise_questions_path"]),
        "--prices", str(Path(__file__).resolve().parents[1] / "prices.json"),
    ]

    exit_code = run_v2.main(argv)
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "retellings: 3" in captured.out
    assert "questions file: present" in captured.out
    assert "tokens per file" in captured.out
    assert "No credentials" in captured.err
    assert not out_dir.exists()


def test_dry_run_reports_noise_counts_in_noisy_mode(sample_inputs_dir, monkeypatch, capsys, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(run_v2, "repo_root_from", lambda _file: tmp_path / "no-such-repo")

    argv = [
        "--model", "fake-model",
        "--mode", "noisy",
        "--out", str(tmp_path / "out"),
        "--dry-run",
        "--retellings-dir", str(sample_inputs_dir["retellings_dir"]),
        "--questions", str(sample_inputs_dir["questions_path"]),
        "--noise-dir", str(sample_inputs_dir["noise_dir"]),
        "--noise-questions", str(sample_inputs_dir["noise_questions_path"]),
        "--prices", str(Path(__file__).resolve().parents[1] / "prices.json"),
    ]

    exit_code = run_v2.main(argv)
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "noise docs: 2" in captured.out
    assert "noise questions: 2" in captured.out
