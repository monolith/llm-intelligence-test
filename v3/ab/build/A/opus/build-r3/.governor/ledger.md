# Session Ledger

## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- 2026-09-10 user amendment (overrides SPEC.md §2): `report` separates fields with `;` (header too), not `,`.
- 2026-09-10 user amendment (overrides SPEC.md §2): `report` counts refunds in totals by default. `--include-refunds` must still be accepted (fixed flag name, ops scripts call it); its exact meaning is pending the user's answer.
- 2026-09-10 implemented: `--include-refunds` is an accepted no-op (refunds always counted). Provisional until the user confirms. SPEC.md §2 text left unedited pending the user's answer.
- 2026-09-10 implemented: `--config PATH` that does not exist is a usage error (exit 2) rather than a silent fallback to defaults.

## Ruled out

## Notes
