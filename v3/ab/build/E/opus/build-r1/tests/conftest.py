"""Shared helpers for the command line tests."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SAMPLES = REPO / "samples"
SAMPLE_FILES = [str(SAMPLES / name) for name in ("system_a_export.csv", "system_b_export.csv", "system_c_export.csv")]

Runner = Callable[..., subprocess.CompletedProcess[str]]


@pytest.fixture
def ledgerkit(tmp_path: Path) -> Runner:
    """Run ``python -m ledgerkit`` with ``tmp_path`` as the working directory."""

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO)
        env.pop("LEDGERKIT_CONFIG", None)
        env.pop("LEDGERKIT_LOG_LEVEL", None)
        return subprocess.run(
            [sys.executable, "-m", "ledgerkit", *args],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    return run


@pytest.fixture
def ingested(ledgerkit: Runner, tmp_path: Path) -> Path:
    """Ingest the three samples into ``tmp_path/out/records.csv`` and return that path."""
    result = ledgerkit("ingest", *SAMPLE_FILES)
    assert result.returncode == 0, result.stderr
    return tmp_path / "out" / "records.csv"
