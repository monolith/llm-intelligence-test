"""Feature test for `--config`."""

from __future__ import annotations

import csv
from pathlib import Path

from conftest import SAMPLE_FILES, run_cli

OVERRIDE = """[report]
decimals = 2
unknown_account_label = "NOT_MAPPED"
"""


def test_config_flag_and_environment_variable_both_select_settings(tmp_path: Path) -> None:
    override = tmp_path / "quarter-close.toml"
    override.write_text(OVERRIDE, encoding="utf-8")

    ingest = run_cli(
        ["--config", str(override), "ingest", *[str(p) for p in SAMPLE_FILES], "--out", "out/r.csv"],
        cwd=tmp_path,
    )
    records = tmp_path / "out" / "r.csv"
    assert records.is_file(), ingest.stderr
    rows = list(csv.DictReader(records.read_text(encoding="utf-8").splitlines()))
    unmapped = {row["account_name"] for row in rows if row["account_code"] == "8800"}
    assert unmapped == {"NOT_MAPPED"}

    with_flag = run_cli(
        ["--config", str(override), "report", "--by", "account", "--records", str(records)],
        cwd=tmp_path,
    )
    assert with_flag.returncode == 0, with_flag.stderr
    assert "6248.50" in with_flag.stdout

    with_env = run_cli(
        ["report", "--by", "account", "--records", str(records)],
        cwd=tmp_path,
        extra_env={"LEDGERKIT_CONFIG": str(override)},
    )
    assert with_env.returncode == 0, with_env.stderr
    assert "6248.50" in with_env.stdout
