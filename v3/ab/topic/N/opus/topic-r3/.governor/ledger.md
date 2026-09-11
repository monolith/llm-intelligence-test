# Ledger

## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- 2026-09-11, user: report separates fields with `;` and counts refunds by default. `--include-refunds` kept as an accepted no-op (flag names are fixed); no opt-out flag added. SPEC.md updated to match.
- Per-system date/amount reading lives in parsers/system_{a,b,c}.py (parse_date/parse_amount); B is whole cents, C dates are %d/%m/%Y.
- System A reader now uses core.fields.split_record for quoted memos (not legacy_parser).
- `--config` sets LEDGERKIT_CONFIG for the run; load_settings() unchanged. Missing --config file exits 2.
- validate: a Borough amount with a decimal point is rejected (Borough writes whole cents).

## Ruled out

## Notes
