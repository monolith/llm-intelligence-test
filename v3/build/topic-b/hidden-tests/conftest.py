"""Shared plumbing for the topic-B hidden test suite.

The suite never lives inside the working copy it grades. Point it at one with
the ``ROSTER_REPO`` environment variable:

    ROSTER_REPO=/path/to/working-copy PYTHONPATH=/path/to/working-copy \
        python3 -m pytest hidden-tests/ -q --junitxml=out.xml

No test imports ``roster`` into the pytest process. Command-line tests run
``python -m roster`` as a subprocess from a scratch directory, and library
tests run a short driver script the same way, printing JSON on stdout. A
working copy that fails to import therefore cannot take the suite down with it.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest

ENV_VAR = "ROSTER_REPO"


def _resolve_repo() -> Path:
    raw = os.environ.get(ENV_VAR, "").strip()
    if not raw:
        raise RuntimeError(
            f"{ENV_VAR} is not set. Run the suite as: "
            f"{ENV_VAR}=<path to working copy> python3 -m pytest hidden-tests/ -q"
        )
    path = Path(raw).expanduser().resolve()
    if not (path / "roster").is_dir():
        raise RuntimeError(f"{ENV_VAR}={path} does not look like a roster working copy")
    return path


REPO = _resolve_repo()

PRELUDE = textwrap.dedent(
    """
    import datetime as dt, json, sys
    from roster import Shift, RosterError, parse_roster, find_conflicts, hours_by_person

    def emit(value):
        sys.stdout.write(json.dumps(value))

    def shape(shift):
        return {
            "date": shift.date.isoformat(),
            "start": shift.start.strftime("%H:%M"),
            "end": shift.end.strftime("%H:%M"),
            "name": shift.name,
            "line": shift.line,
            "start_at": shift.start_at.isoformat(),
            "end_at": shift.end_at.isoformat(),
        }
    """
).strip()


def _run(args: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO)
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def run_cli(args: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run ``python -m roster`` against the working copy under test."""
    return _run(["-m", "roster", *args], cwd=cwd, timeout=timeout)


def run_driver(body: str, cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    """Run a driver snippet with the working copy importable."""
    script = cwd / "_driver.py"
    script.write_text(PRELUDE + "\n\n" + textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    return _run([str(script)], cwd=cwd, timeout=timeout)


def driver_json(body: str, cwd: Path, timeout: int = 120) -> Any:
    """Run a driver snippet that calls ``emit(...)`` and return what it emitted."""
    proc = run_driver(body, cwd=cwd, timeout=timeout)
    assert proc.returncode == 0, f"driver failed:\n{proc.stdout}\n{proc.stderr}"
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as err:  # pragma: no cover - diagnostic path
        raise AssertionError(f"driver printed no JSON ({err}):\n{proc.stdout}\n{proc.stderr}") from err


def write_roster(cwd: Path, name: str, text: str) -> Path:
    path = cwd / name
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO
