"""Shared plumbing for the hidden test suite.

The suite never lives inside the repository it grades.  Point it at a working
copy with the ``LEDGERKIT_REPO`` environment variable:

    LEDGERKIT_REPO=/path/to/working-copy python3 -m pytest hidden-tests/ -q

Every test runs the command line as a subprocess, from a scratch directory, with
``PYTHONPATH`` set to the working copy.  No test imports the package into the
pytest process, so a broken working copy cannot take the suite down with it.
"""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ENV_VAR = "LEDGERKIT_REPO"


def _resolve_repo() -> Path:
    raw = os.environ.get(ENV_VAR, "").strip()
    if not raw:
        raise RuntimeError(
            f"{ENV_VAR} is not set. Run the suite as: "
            f"{ENV_VAR}=<path to working copy> python3 -m pytest hidden-tests/ -q"
        )
    path = Path(raw).expanduser().resolve()
    if not (path / "ledgerkit").is_dir():
        raise RuntimeError(f"{ENV_VAR}={path} does not look like a ledgerkit working copy")
    return path


REPO = _resolve_repo()
SAMPLES = REPO / "samples"
SAMPLE_FILES: tuple[Path, ...] = (
    SAMPLES / "system_a_export.csv",
    SAMPLES / "system_b_export.csv",
    SAMPLES / "system_c_export.csv",
)


def run_cli(
    args: list[str],
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    """Run ``python -m ledgerkit`` against the working copy under test."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    env.pop("LEDGERKIT_CONFIG", None)
    env.pop("LEDGERKIT_LOG_LEVEL", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "ledgerkit", *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


@dataclass
class IngestRun:
    """One ``ingest`` of the three sample exports, and what came out of it."""

    work: Path
    proc: subprocess.CompletedProcess[str]
    records_path: Path
    rows: list[dict[str, str]] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)

    def by_id(self, record_id: str) -> dict[str, str]:
        for row in self.rows:
            if row.get("record_id") == record_id:
                return row
        raise AssertionError(f"no record {record_id!r} in {self.records_path}")


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO


@pytest.fixture(scope="session")
def cli():
    return run_cli


@pytest.fixture(scope="session")
def ingested(tmp_path_factory: pytest.TempPathFactory) -> IngestRun:
    """Ingest the three sample exports once and share the result."""
    work = tmp_path_factory.mktemp("ledgerkit-ingest")
    proc = run_cli(["ingest", *[str(p) for p in SAMPLE_FILES]], cwd=work)
    records_path = work / "out" / "records.csv"
    run = IngestRun(work=work, proc=proc, records_path=records_path)
    if records_path.is_file():
        text = records_path.read_text(encoding="utf-8")
        run.raw_lines = text.splitlines()
        run.rows = list(csv.DictReader(text.splitlines()))
    return run
