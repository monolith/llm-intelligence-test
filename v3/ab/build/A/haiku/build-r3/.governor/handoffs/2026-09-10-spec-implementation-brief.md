# Handoff: Implement Five Ledgerkit Features

## Goal
Implement `ingest`, `report`, `reconcile`, `validate` commands and `--config` global option to read three incompatible ledger exports (systems A, B, C) and normalize them into one dataset for reporting.

## Current state (verified against ground truth)

- [verified] Three export formats with incompatible amounts/dates:
  - System A (Ardent): ISO date YYYY-MM-DD, decimal dollars, supports quoted fields
  - System B (Borough): ISO date YYYY-MM-DD, **integer cents** (not dollars), no quoting, every row starts with 'B'
  - System C (Calder): dd/mm/yyyy date (day first), decimal dollars, banner + trailer
- [verified] System B requires `system_b.to_major_units()` to convert cents→dollars
- [verified] System C requires parsing dates as dd/mm/yyyy, not YYYY-MM-DD
- [verified] Normalized Record has 7 fields: record_id, source_system, date, account_code, account_name, description, amount (Decimal)
- [verified] Account mapping in `mapping.py` provides account_name lookup; unknown codes use config's `unknown_account_label`
- [verified] Infrastructure exists: `detect_system()`, `read_rows()`, `normalize()`, `config.load_settings()`, `cli.emit()`, `sort_key()`
- [verified] SPEC.md has two corrections applied (see Decisions)

## Decisions + why

- **Report output: semicolon-separated, not comma** — warehouse team's receiving sheet expects semicolons
- **Report includes refunds by default** — changed from exclude-by-default to include-by-default
- **`--include-refunds` flag behavior unclear** — user did not specify whether flag should be removed or inverted; ask next session or infer from usage

## Failure lessons

None yet; this is foundation work with no implementation attempts.

## Contradicted claims

None yet.

## Next steps

1. Clarify `--include-refunds` flag behavior for report (remove entirely? invert to `--exclude-refunds`?)
2. Create readers that convert raw rows to Record objects for each system (A/B/C)
3. Implement `ingest` command (merge, normalize, write CSV)
4. Implement `report` command (read normalized CSV, group, total, output semicolon-delimited)
5. Implement `reconcile` command (find system disagreements)
6. Implement `validate` command (check export files, log warnings, exit code 2 on failures)
7. Implement `--config` global option (wire into CLI argument parser before subcommands)
8. Test all five features against samples

## Files touched

None yet.

## Commands to re-verify

- `python -m pytest tests/` (baseline: existing tests for version/inspect should pass)
- `python -m ledgerkit version` (baseline: should work)
- `python -m ledgerkit inspect samples/system_a_export.csv` (baseline: should work)
