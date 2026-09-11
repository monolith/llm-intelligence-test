# Ledger

## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- 2026-09-11 (user): `report` separates fields with `;`, not `,`, for both the header and data lines. This overrides SPEC.md §2. `ingest` output stays comma separated.
- 2026-09-11 (user): `report` counts refunds in totals by default. This overrides SPEC.md §2. `--include-refunds` stays accepted because it is a fixed flag name, but it no longer changes anything.

## Ruled out

## Notes
