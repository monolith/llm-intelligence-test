# Ledger

## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- 2026-09-11 (user, overrides SPEC §2): `report` output, header included, is separated by `;` not `,`. `ingest`'s normalized CSV stays comma-separated.
- 2026-09-11 (user, overrides SPEC §2): refunds count in `report` totals by default. `--include-refunds` must still be accepted (flag names are fixed); what it does now is an open question for the user.
- 2026-09-11 (implemented, pending user confirmation): `--include-refunds` is accepted and does nothing.
- 2026-09-11 (my call on spec gaps): `ingest` exits 2 and writes nothing if any input can't be read; `--config` pointing at a missing file is an error (exit 2); `validate` rejects a B amount with a decimal point (must be integer cents); report/reconcile exit 2 if the records file can't be read; `--tolerance` must be >= 0.
- Conversions live in each reader (`parse_date`/`parse_amount`/`to_record`); the A reader now handles quoted memos via `core.fields.split_record`.

## Ruled out

## Notes
