# Ledger

## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- 2026-09-10 (user): `report` separates columns with semicolons, not commas (overrides SPEC.md §2, which still says comma). This covers the header line too. Only `report` changes; ingest's CSV stays comma-separated.
- 2026-09-10 (user): `report` counts refunds in its totals by default (overrides SPEC.md §2). What `--include-refunds` should do now is still open. The flag name stays fixed.

## Ruled out

## Notes
