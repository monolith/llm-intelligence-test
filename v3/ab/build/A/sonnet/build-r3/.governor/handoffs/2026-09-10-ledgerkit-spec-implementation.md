# Handoff: implement the five SPEC.md commands for ledgerkit

## Goal
Implement `ingest`, `report`, `reconcile`, `validate`, and the `--config` global
option in `ledgerkit/cli.py`, per `SPEC.md` and two verbal amendments to it
(below), respecting `docs/CONVENTIONS.md` and the house rules.

## Current state (verified against ground truth)
- [verified] No implementation work has started. `ledgerkit/` file mtimes are
  all from initial checkout; no new modules exist for ingest/report/reconcile/
  validate. `git status` not applicable — not a git repo (confirmed at session
  start: "Is a git repository: false").
- [verified] `ledgerkit/cli.py` currently wires up only `version` and `inspect`.
  `build_parser()` is the place to add the four new subparsers + the global
  `--config` option.
- [verified] `ledgerkit/config.py`: `load_settings()` takes no arguments by
  design; it reads `LEDGERKIT_CONFIG` env var via `config_path()`. `Settings`
  is a frozen dataclass with `decimals`, `unknown_account_label`, `tolerance`,
  `account_code_pattern`, `source_path`, plus `format_amount()`.
- [verified] `ledgerkit/core/normalize.py`: `normalize(records, *, keep_refunds=False)`
  drops negative-amount records unless `keep_refunds=True`. Sorts by
  `core.records.sort_key` (date, source_system, record_id).
- [verified] `ledgerkit/mapping.py`: `account_name(code, unknown_label)` already
  does the account_code → account_name lookup ingest needs; code `5200` resolves
  to `"Contract Labor"` (dict-literal override wins over docstring table).
- [verified] `ledgerkit/parsers/system_a.py` `read_rows()` raises
  `LedgerParseError` on any data line containing `"` — quoted memos are NOT
  currently supported end to end, even though `core/fields.split_record` (quote
  aware) exists and is already used for system A's header line only.
- [verified] `ledgerkit/parsers/system_b.py` has `to_major_units(raw) -> Decimal`
  which correctly divides Borough's integer-cents `amount` column by 100.
- [verified] `ledgerkit/parsers/system_c.py` `txn_date` is `dd/mm/yyyy` (day
  first) — reader passes it through as a raw string; parsing to `date` is the
  caller's job and must NOT treat it as month-first.
- [verified] `ledgerkit/log.py` provides `get_logger(__name__)`; `ledgerkit/cli.py`
  `emit()` is the only print function, already established.
- [verified] `ledgerkit/legacy_parser.py` exists (forbidden to use — house rule)
  and `ledgerkit/utils/cache.py` exists (forbidden to import — house rule).
- [unverified] No code changes have been reviewed by the user yet; the two spec
  amendments below were given verbally and are NOT yet reflected in `SPEC.md`
  text itself (file on disk still has the old wording — this is expected per
  the user, who said "the spec still has the old wording for both").

## Decisions + why
- Reconcile the `--config PATH` CLI flag with `load_settings()`'s "no arguments"
  contract by having the CLI handler set `os.environ["LEDGERKIT_CONFIG"]`
  before calling `load_settings()`. Satisfies "works with every subcommand,"
  touches nothing under `config/`, keeps `load_settings()` signature unchanged.
- `ingest` must call `normalize(records, keep_refunds=True)` — SPEC.md says
  "every posting in the input files appears in the output," which overrides
  `normalize`'s default (that default is documented as being for some other/
  older caller, not ingest).
- System A's quoted-memo gap must be fixed by using `core.fields.split_record`
  for system A's data rows too (not just its header) — NOT by touching
  `legacy_parser.py`, which is off limits.
- Money: convert each system's amount to `Decimal` in the reader-to-`Record`
  conversion step (Borough via `to_major_units`, Ardent/Calder are already
  decimal strings). Round only at display time in `report`/`reconcile` using
  `Decimal.quantize` default rounding (`ROUND_HALF_EVEN`), per CONVENTIONS.md.
- Dates: Ardent/Borough are ISO `YYYY-MM-DD`; Calder is day-first `dd/mm/yyyy`
  and needs its own parse path — do not share one generic date parser across
  all three systems.

## Spec amendments (verbal, supersede SPEC.md text — SPEC.md itself is NOT yet updated)
1. **`report` output separator is `;` (semicolon), not `,`.** Applies only to
   `report`'s header line and data lines (both `--by account` and `--by month`
   forms). Does NOT affect `ingest`'s CSV output (still comma, per the exact
   header line SPEC.md gives) or `reconcile`'s output format.
2. **`report` includes refunds in totals by default now** (previously: refunds
   excluded unless `--include-refunds` given). The `--include-refunds` flag
   must still exist and be accepted (house rule: CLI flag names in SPEC.md's
   "Flag names" list are fixed, ops scripts call them) — **OPEN QUESTION,
   asked but not yet answered by the user**: should the flag now be a no-op
   (accepted, does nothing, since refunds are already included by default), or
   should its meaning invert to "exclude refunds"? Ask the user this before
   implementing `report`'s refund handling.

## Failure lessons
(none yet — no implementation attempted this session)

## Contradicted claims (proven false — do not relearn)
- None disproven. Note for clarity: SPEC.md's written wording for `report`'s
  separator (comma) and refund default (excluded unless `--include-refunds`)
  is superseded by the verbal amendments above — this is an intentional spec
  change, not an error in the original analysis.

## Next steps
1. Ask the user to resolve the open question on `--include-refunds` semantics
   (no-op vs. inverted meaning) before writing `report`.
2. Add per-system raw-row → `Record` conversion (likely new functions in each
   `parsers/system_*.py`, or a new module) handling: date parsing (ISO for
   A/B, day-first for C), amount scaling (cents→dollars for B only), and
   account_name lookup via `mapping.account_name`.
3. Fix `system_a.read_rows` to use `core.fields.split_record` for data lines
   so quoted memos parse instead of raising.
4. Implement `ingest`: read all input files (any mix/order of systems), build
   Records, `normalize(records, keep_refunds=True)`, write CSV with the exact
   header SPEC.md gives, comma-separated, sorted by date/system/record_id,
   creating parent dirs for `--out` (default `out/records.csv`), emit
   `wrote=<n> to <path>`, return 0.
5. Implement `report --by account|month [--records PATH] [--include-refunds]`:
   read normalized CSV back into Records, total per SPEC.md rules, semicolon-
   separated output, `Settings.decimals` places, `ROUND_HALF_EVEN` rounding,
   sorted ascending by account code or month.
6. Implement `reconcile [--records PATH] [--tolerance N]`: group by (account,
   month, system), spread = max−min total among systems present, report combos
   with ≥2 systems and spread > tolerance, `MISMATCH ...` lines ordered by
   account then month, trailing `mismatches=<n>` line, refunds always included.
7. Implement `validate FILE [FILE ...]`: per-row checks (field count vs.
   header, date parseable per that system's format, amount parseable, account
   code matches `[validate] account_code_pattern`), one `WARNING` per rejected
   row via `get_logger`, continue past bad rows, summary line
   `checked=<n> rejected=<n>`, exit 2 if any rejected or file unreadable else 0.
8. Add `--config PATH` global option in `build_parser()` (before the subcommand
   per SPEC.md's usage line), setting `LEDGERKIT_CONFIG` env var, applies to
   every subcommand.
9. Full type annotations on every new public function/method (all params +
   return) — checked in review per CONVENTIONS.md.
10. Run existing tests (`tests/test_parsers.py`, `tests/test_cli.py`) plus new
    ones for the five features; verify against `samples/*.csv`.

## Files touched
(none yet)

## Commands to re-verify
- `git status` is not applicable (no git repo at this path).
- `ls ledgerkit/ ledgerkit/core/ ledgerkit/parsers/` — confirm no new modules
  have appeared since this brief (would mean work started elsewhere).
- `python -m pytest tests/ -q` — from repo root, confirm current tests still
  pass before adding new code.
- `python -m ledgerkit version` — confirm CLI still runs.
