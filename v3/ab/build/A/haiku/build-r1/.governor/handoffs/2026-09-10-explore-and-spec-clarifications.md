# Handoff: Ledgerkit SPEC exploration complete; two spec clarifications captured

## Goal
Implement five new CLI commands (`ingest`, `report`, `reconcile`, `validate`, `--config`) to merge and report on ledger exports from three legacy systems (A, B, C).

## Current state (verified against ground truth)

- [verified] No code changes made this session; all tests pass (`pytest tests/` returns 6/6 PASSED)
- [verified] Three export systems fully understood:
  - **System A (Ardent):** ISO dates (YYYY-MM-DD), decimal dollar amounts, CSV with comment header, supports quoted fields
  - **System B (Borough):** ISO dates, **amounts in integer cents (divide by 100 required)**, plain CSV, no quotes
  - **System C (Calder):** **dd/mm/yyyy date format (day-first, not month-first)**, decimal dollar amounts, CSV with banner and trailer
- [verified] Core abstractions in place: Record dataclass, readers returning raw strings, system detection, account mapping, config layering, logging infrastructure
- [verified] House rules documented: Decimal money only, half-to-even rounding, full type annotations on public functions, no print in lib code, stdlib only, no config/ edits
- [verified] SPEC.md read and understood for all five commands with their exact flag names

## Decisions + why

- **Report output: semicolon-delimited, not comma-delimited** — User clarified warehouse team's sheet is configured for semicolons; overrides SPEC.md wording
- **Refunds included in report totals by default** — Changed from exclude-by-default; overrides SPEC.md wording; user clarified this is final behavior
- **Flag behavior TBD: `--include-refunds`** — User did not yet clarify what happens to this flag now that refunds are default-included; three options exist (remove, invert to `--exclude-refunds`, or no-op); awaiting next session input before implementation

## Failure lessons
(None; this was exploration phase)

## Contradicted claims
(None)

## Next steps

1. **Clarify `--include-refunds` flag** — Next session must ask/decide: remove it, invert to `--exclude-refunds`, or keep as no-op
2. **Implement `ingest` command** — Read any number of exports, convert to Records, normalize, write sorted CSV
3. **Implement `report` command** — Read normalized CSV, total by account or month (refunds included), output semicolon-delimited
4. **Implement `reconcile` command** — Find account/month pairs where two+ systems disagree, report spreads
5. **Implement `validate` command** — Check files for malformed rows, log warnings, exit code 2 if any rejected
6. **Implement `--config` global option** — Parse before subcommand, pass to `load_settings()` via LEDGERKIT_CONFIG

## Files touched
None (exploration only)

## Commands to re-verify

```bash
python -m pytest tests/ -v
```

Expected: 6 PASSED. If not, something broke the baseline.

## Key implementation notes for next session

- Readers (`system_a.read_rows()`, etc.) return raw strings; converters must call System B's `to_major_units()` and parse System C dates
- All output must be sorted by `sort_key()` (date, system, record_id)
- Refunds (negative amount) are now included in report totals and reconcile calculations
- Output goes through `emit()` in cli.py only; diagnostics through `get_logger(__name__)`
- Config: built-in defaults → checked-in `config/settings.toml` → `LEDGERKIT_CONFIG` override, all read-only
- Settings sections: `[report]` (decimals, unknown_account_label), `[reconcile]` (tolerance), `[validate]` (account_code_pattern)
