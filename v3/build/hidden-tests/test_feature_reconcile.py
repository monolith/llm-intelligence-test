"""Feature tests for `reconcile`."""

from __future__ import annotations

from conftest import IngestRun, run_cli

EXPECTED_LINES = [
    "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-",
    "MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05",
    "MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55",
    "MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60",
    "MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-",
    "mismatches=5",
]


def test_reconcile_flags_exactly_the_disagreements(ingested: IngestRun) -> None:
    proc = run_cli(["reconcile", "--records", str(ingested.records_path)], cwd=ingested.work)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines() == EXPECTED_LINES


def test_reconcile_tolerance_flag_widens_the_window(ingested: IngestRun) -> None:
    proc = run_cli(
        ["reconcile", "--records", str(ingested.records_path), "--tolerance", "20"],
        cwd=ingested.work,
    )
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.splitlines()
    assert lines[-1] == "mismatches=1"
    assert lines[0] == "MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-"
