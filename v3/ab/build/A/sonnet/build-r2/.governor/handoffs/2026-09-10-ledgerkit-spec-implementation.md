# Handoff: implement the five SPEC.md commands for ledgerkit

## Goal
Implement `ingest`, `report`, `reconcile`, `validate`, and the global `--config`
flag in `SPEC.md`, respecting `docs/CONVENTIONS.md`. Nothing has been
implemented yet — this session was research only.

## Current state (verified against ground truth)
- [verified] No code has been written. `ledgerkit/`, `ledgerkit/core/`,
  `ledgerkit/parsers/`, `ledgerkit/utils/` contain only the pre-existing files
  (checked via `ls` this session, no `ingest.py`/`report.py`/etc exist).
- [verified] Not a git repository (`git status` fails with "not a git
  repository").
- [verified] Only `version` and `inspect` are wired up in `ledgerkit/cli.py`.
- [verified] `.governor/ledger.md` has the goal only, no decisions/ruled-out
  recorded yet.
- [unverified, but read in full this session] `SPEC.md`, `docs/CONVENTIONS.md`,
  `README.md`, and every file under `ledgerkit/` (`cli.py`, `config.py`,
  `log.py`, `mapping.py`, `legacy_parser.py`, `core/fields.py`,
  `core/normalize.py`, `core/records.py`, `parsers/__init__.py`,
  `parsers/system_a.py`, `parsers/system_b.py`, `parsers/system_c.py`,
  `utils/cache.py`) plus all three sample exports and both test files were
  read this session — re-read before trusting fine details, but the structural
  facts below were extracted directly from that reading.

## Decisions + why
- **`report` output uses `;` not `,`, and refunds are included in totals by
  default** — user correction given verbally after SPEC.md was written;
  SPEC.md's own text (section 2) is stale and was NOT edited to match. Full
  detail and the still-open question about what `--include-refunds` should do
  now (my working assumption: it stays accepted as a no-op, since inclusion is
  already the default and the flag name is fixed by SPEC.md/ops scripts) is in
  memory file `spec_report_amendments.md` — **read that memory file before
  writing `report`**, do not rely only on SPEC.md.
- **`ingest` must NOT use the default of `normalize(keep_refunds=False)`** —
  it needs `normalize(records, keep_refunds=True)`, because SPEC.md requires
  every posting to survive ingest and the default silently drops refunds.
- **`system_a.py`'s data-row reader needs to switch from `line.split(",")` to
  `ledgerkit.core.fields.split_record`** — as shipped it raises
  `LedgerParseError` on any quoted memo line, and the real sample file
  (`samples/system_a_export.csv` line 6, `A-10001`) has one, so ingest cannot
  currently read the sample. Do NOT use `legacy_parser.py` to fix this (house
  rule + the module is explicitly unmaintained) — `core/fields.py` already
  has exactly the quoting logic needed (its own docstring example is that
  exact row).
- **`--config PATH` should be implemented by setting
  `os.environ[LEDGERKIT_CONFIG]`** before any handler calls `load_settings()`,
  because `load_settings()` is deliberately zero-argument per
  `docs/CONVENTIONS.md` ("Configuration" section) — do not change its
  signature, do not touch anything under `config/`.

## Failure lessons
(none yet — no implementation attempted this session)

## Contradicted claims (proven false — do not relearn)
- "The three export amount/date columns are directly comparable as written" —
  false. B's amount is integer cents (needs `system_b.to_major_units`), C's
  date is day-first `dd/mm/yyyy` (needs day-first parsing, NOT the naive
  month-first read that silently misfiles dates ≤12).
- "SPEC.md is current and complete for `report`" — false, see amendments
  above; SPEC.md's stated comma separator and refund-excluded-by-default text
  for `report` no longer hold.

## Next steps
1. Read memory file `spec_report_amendments.md` in the auto-memory store
   (already indexed in `MEMORY.md`) before writing any `report` code.
2. Fix `ledgerkit/parsers/system_a.py` to parse quoted data rows via
   `ledgerkit.core.fields.split_record` instead of raising on `"` in the line.
3. Implement `ingest`: build `Record`s per system (A/C dates ISO already, C is
   day-first `dd/mm/yyyy`, B amount needs `to_major_units`, unknown account
   codes fall back to `[report] unknown_account_label` via
   `ledgerkit.mapping.account_name`), call
   `normalize(records, keep_refunds=True)`, write CSV via
   `core.fields.join_record` (or equivalent quoting), print the
   `wrote=<n> to <path>` summary through `cli.emit`.
4. Implement `report`: read back `out/records.csv` (or `--records` path),
   group by account or month, apply `--include-refunds` semantics per the
   amendment above, round once with `Decimal.quantize(..., ROUND_HALF_EVEN)`
   at display time using `Settings.format_amount`, print with `;` separators.
5. Implement `reconcile`: group by (account_code, month, source_system), sum
   per group (refunds always included per SPEC.md), compute spread vs
   `--tolerance`/`[reconcile] tolerance`, format per SPEC.md's `MISMATCH` line.
6. Implement `validate`: cannot reuse `read_rows()` as-is since it aborts on
   the first bad row — needs its own tolerant per-line scan per system
   (field count, per-system date parse, numeric amount parse,
   `[validate] account_code_pattern` match), one `WARNING` per bad row via
   `ledgerkit.log.get_logger`, continuing past errors; exit 2 if anything
   rejected or a file is unreadable.
7. Wire `--config` as a global `argparse` option on the top-level parser
   (before subparsers, matching SPEC.md's `--config PATH COMMAND ...` order).
8. Run `python -m pytest tests/` and add tests for the four new commands.

## Files touched
None yet.

## Commands to re-verify
- `ls ledgerkit ledgerkit/core ledgerkit/parsers ledgerkit/utils` — confirm no
  implementation has appeared since this brief was written.
- `python -m pytest tests/` — baseline should currently pass with only
  `version`/`inspect` tests.
- `cat SPEC.md` — re-check section 2 (`report`) against the amendments above;
  SPEC.md itself was not edited this session.
