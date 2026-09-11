"""Smoke tests for the parts of the command line that exist."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=REPO,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_version_runs() -> None:
    result = run("version")
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0].startswith("ledgerkit ")


def test_cli_inspect_reports_system_and_line_count() -> None:
    result = run("inspect", str(SAMPLES / "system_a_export.csv"))
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    assert "system=A" in lines
    assert "data_lines=42" in lines
