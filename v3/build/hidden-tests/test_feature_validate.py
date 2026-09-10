"""Feature tests for `validate`."""

from __future__ import annotations

from pathlib import Path

from conftest import SAMPLE_FILES, run_cli

BAD_CALDER_EXPORT = (
    "CALDER EXPORT v3\n"
    "ref,txn_date,ledger_acct,narrative,gross_amount,ccy\n"
    "C-9001,04/01/2026,4100,A good row,10.00,USD\n"
    "C-9002,31/13/2026,4100,Month thirteen,10.00,USD\n"
    "C-9003,05/01/2026,ABCD,Letters for a code,10.00,USD\n"
    "C-9004,06/01/2026,4100,Not a number,ten dollars,USD\n"
    "== 4 rows ==\n"
)


def _write_bad_export(tmp_path: Path) -> Path:
    export = tmp_path / "calder-broken.csv"
    export.write_text(BAD_CALDER_EXPORT, encoding="utf-8")
    return export


def test_validate_exits_2_on_malformed_rows_and_0_on_clean_ones(tmp_path: Path) -> None:
    clean = run_cli(["validate", *[str(p) for p in SAMPLE_FILES]], cwd=tmp_path)
    assert clean.returncode == 0, clean.stderr
    assert "checked=120 rejected=0" in clean.stdout

    export = _write_bad_export(tmp_path)
    bad = run_cli(["validate", str(export)], cwd=tmp_path)
    assert bad.returncode == 2, bad.stdout + bad.stderr
    assert "checked=4 rejected=3" in bad.stdout


def test_validate_warns_through_the_project_logger(tmp_path: Path) -> None:
    export = _write_bad_export(tmp_path)
    proc = run_cli(["validate", str(export)], cwd=tmp_path)
    warnings = [line for line in proc.stderr.splitlines() if line.startswith("LEDGERKIT WARNING ledgerkit.")]
    assert len(warnings) == 3, proc.stderr
    assert all("calder-broken.csv" in line for line in warnings)
