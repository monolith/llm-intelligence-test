# Ledger

## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- 2026-09-11, user: `report` separates fields with `;`, not `,` (overrides SPEC.md §2).
- 2026-09-11, user: `report` counts refunds by default (overrides SPEC.md §2). `--include-refunds` is still accepted and has no effect.
- The A reader splits rows with `core.fields.split_record` (quoted memos); legacy_parser is not used.
- Amount/date interpretation lives in each parser module (`parse_date`, `parse_amount`, `to_record`).
- `--config` sets `LEDGERKIT_CONFIG` for the duration of the run; `load_settings()` keeps taking no arguments.
- ingest does not call `normalize()`, because it drops refunds and rewrites descriptions.

## Ruled out

## Notes
