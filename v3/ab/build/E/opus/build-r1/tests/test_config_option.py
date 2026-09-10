"""Tests for the global ``--config`` option."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from conftest import REPO, Runner

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from ledgerkit import cli  # noqa: E402
from ledgerkit.config import CONFIG_ENV_VAR  # noqa: E402

CONFIG_DIR = REPO / "config"


def config_snapshot() -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in CONFIG_DIR.iterdir()}


def test_config_applies_to_version(ledgerkit: Runner, tmp_path: Path) -> None:
    override = tmp_path / "run.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")
    result = ledgerkit("--config", str(override), "version")
    assert result.returncode == 0, result.stderr
    assert f"settings={override}" in result.stdout.splitlines()


def test_config_changes_report_decimals_and_label(ledgerkit: Runner, ingested: Path, tmp_path: Path) -> None:
    before = config_snapshot()
    override = tmp_path / "run.toml"
    override.write_text('[report]\ndecimals = 2\nunknown_account_label = "TO SORT"\n', encoding="utf-8")

    report = ledgerkit("--config", str(override), "report", "--by", "month")
    assert report.returncode == 0, report.stderr
    assert report.stdout.splitlines() == ["month;total", "2026-01;13256.48", "2026-02;8456.50", "2026-03;5870.25"]

    ingest = ledgerkit("--config", str(override), "ingest", str(REPO / "samples" / "system_c_export.csv"))
    assert ingest.returncode == 0, ingest.stderr
    by_account = ledgerkit("report", "--by", "account").stdout
    assert "8800;TO SORT;" in by_account

    assert config_snapshot() == before


def test_config_changes_reconcile_tolerance(ledgerkit: Runner, ingested: Path, tmp_path: Path) -> None:
    override = tmp_path / "run.toml"
    override.write_text("[reconcile]\ntolerance = 16.30\n", encoding="utf-8")
    result = ledgerkit("--config", str(override), "reconcile")
    assert result.stdout.splitlines()[-1] == "mismatches=2"
    # The flag still beats the setting.
    result = ledgerkit("--config", str(override), "reconcile", "--tolerance", "0.05")
    assert result.stdout.splitlines()[-1] == "mismatches=5"


def test_config_file_must_exist(ledgerkit: Runner, tmp_path: Path) -> None:
    result = ledgerkit("--config", str(tmp_path / "nope.toml"), "version")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "nope.toml" in result.stderr


def test_config_rejects_malformed_toml(ledgerkit: Runner, tmp_path: Path) -> None:
    override = tmp_path / "bad.toml"
    override.write_text("[report\n", encoding="utf-8")
    result = ledgerkit("--config", str(override), "version")
    assert result.returncode == 2
    assert "bad.toml" in result.stderr


def test_config_does_not_leak_between_in_process_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv(CONFIG_ENV_VAR, raising=False)
    override = tmp_path / "run.toml"
    override.write_text("[report]\ndecimals = 2\n", encoding="utf-8")

    assert cli.main(["--config", str(override), "version"]) == 0
    assert f"settings={override}" in capsys.readouterr().out
    assert CONFIG_ENV_VAR not in os.environ

    assert cli.main(["version"]) == 0
    assert f"settings={CONFIG_DIR / 'settings.toml'}" in capsys.readouterr().out
