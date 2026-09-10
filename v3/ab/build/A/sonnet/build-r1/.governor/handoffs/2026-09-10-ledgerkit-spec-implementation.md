# Handoff: Implement the five SPEC.md commands for ledgerkit

## Goal
Implement `ingest`, `report`, `reconcile`, `validate`, and the `--config` global
flag in `ledgerkit/`, per `SPEC.md` plus two verbal amendments below, following
`docs/CONVENTIONS.md`. No code has been written yet — this is pure discovery.

## Current state (verified against ground truth)
- [verified] Not a git repo (`git status` fails with "not a git repository").
- [verified] No source files have been modified. Repo root contains: `cli-calls.jsonl`,
  `config/`, `docs/`, `ledgerkit/`, `README.md`, `samples/`, `SPEC.md`, `tests/`.
- [verified] Only `version` and `inspect` subcommands exist in `ledgerkit/cli.py`.
  `ingest`/`report`/`reconcile`/`validate` are not implemented; `build_parser()` has
  no `--config` global option yet.
- [verified] `ledgerkit/parsers/system_a.py::read_rows` explicitly raises
  `LedgerParseError` on any line containing `"`, but `samples/system_a_export.csv`
  **does** contain quoted memo fields (e.g. `"Rebill, ""Q1 true-up"", carrier"`).
  This must be fixed (use `ledgerkit/core/fields.py::split_record`, which already
  handles this quoting correctly) before `ingest` can read the real sample file.
- [verified] `ledgerkit/core/normalize.py::normalize()` defaults to
  `keep_refunds=False` (drops negative-amount rows) and collapses internal
  whitespace in `description` via `" ".join(record.description.split())`.
- [verified] `ledgerkit/config.py::load_settings()` takes no args; reads
  `config/settings.toml` layered with the file named by `LEDGERKIT_CONFIG` env var.
  `Settings.format_amount()` does NOT round — CONVENTIONS.md confirms rounding
  happens once, at display, via `Decimal.quantize` (default mode is ROUND_HALF_EVEN).
- [verified] `ledgerkit/mapping.py` defines `"5200"` twice in the `ACCOUNT_NAMES`
  dict literal; Python keeps the second ("Contract Labor"). `account_name()` /
  `is_known()` already resolve this correctly, no extra handling needed.
- [verified] All three readers (`system_a/b/c.read_rows`) raise and **stop at the
  first bad row** — they cannot be reused as-is for `validate`, which must check
  every row and report every failure.
- [verified] Per-system raw field → Record mapping:
  - A: `entry_id`→record_id, `posted_on`→date (ISO `YYYY-MM-DD`), `account`→account_code,
    `memo`→description, `amount`→amount (already dollars, decimal).
  - B: `doc_no`→record_id, `value_date`→date (ISO), `acct`→account_code, `descr`→description,
    `amount`→amount (**integer cents** — convert with `system_b.to_major_units()`).
  - C: `ref`→record_id, `txn_date`→date (**`DD/MM/YYYY`, day first** — NOT ISO,
    NOT month-first), `ledger_acct`→account_code, `narrative`→description,
    `gross_amount`→amount (already dollars, decimal).
- [verified] Reusable pieces: `core/records.py` (`Record`, `RECORD_COLUMNS`,
  `sort_key` = date,system,id — matches `ingest`'s required ordering, `Record.to_row()`
  already renders amount at 2dp), `core/fields.py` (`split_record`/`join_record`,
  quote-aware), `mapping.account_name(code, unknown_label)`.
- [unverified, carried from prior discussion] `--config PATH` should be a
  top-level argparse option (added before `add_subparsers`), and the handler
  should set `os.environ["LEDGERKIT_CONFIG"]` before any `load_settings()` call —
  mirrors how `cmd_version` already calls `load_settings()` inside the handler.

## Decisions + why
- User has verbally amended SPEC.md's `report` command, superseding the written
  spec text (SPEC.md itself is NOT yet edited to reflect this — treat the two
  bullets below as authoritative over the SPEC.md text they contradict):
  1. **`report`'s column separator is `;` (semicolon), not `,`.** Scoped to
     `report` only — confirmed with user this does not apply to `ingest`'s CSV
     (fixed comma header per spec) or to `reconcile`'s `MISMATCH ...` line.
  2. **`report` totals include refunds by default now.** Previously refunds were
     excluded unless `--include-refunds` was passed; now they're included unless
     told otherwise. Flag name `--include-refunds` is fixed (cannot rename per
     house rules / SPEC's "Flag names" list) — asked user whether it should
     become a no-op or invert to "exclude refunds"; **user has not yet answered
     this question**. Default to accepting the flag as a harmless no-op unless
     told otherwise when implementation starts — but confirm with user first if
     possible.
- House rules (given directly by user, apply to all five features): no `print`
  in library code, only `ledgerkit.cli.emit` prints; every new public function
  fully type-annotated (params + return); never edit anything under `config/`;
  log via `ledgerkit.log.get_logger`, never `logging` directly; no new
  dependencies (stdlib only); never import `ledgerkit/utils/cache.py`; never use
  `ledgerkit/legacy_parser.py`; keep CLI flag names exactly as SPEC.md states
  (`--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`).

## Failure lessons
(none yet — no implementation attempted this session)

## Contradicted claims (proven false — do not relearn)
- SPEC.md's `report` example showing comma-separated columns is superseded by
  the user's semicolon amendment — do not implement comma separation for `report`.
- SPEC.md's "without [--include-refunds], refunds are left out of the totals" is
  superseded — refunds are in by default now.
- The error message inside `system_a.py`'s quoted-line rejection ("see
  legacy_parser.py for quoted fields") is a dead end — `legacy_parser.py` is
  banned by house rules; use `core/fields.py::split_record` instead.

## Next steps
1. Get user's answer on `--include-refunds` semantics now that refunds default
   to included (no-op vs. invert-to-exclude) before wiring `report`'s flag.
2. Fix `ledgerkit/parsers/system_a.py::read_rows` to use `core/fields.split_record`
   instead of `line.split(",")`, so quoted memos parse instead of raising.
3. Build the raw-row → `Record` conversion per system (likely a new module, e.g.
   `ledgerkit/core/build.py` or similar) handling the three date formats and the
   Borough cents conversion — decide whether `normalize()` is reused as-is or
   whether `ingest` needs `keep_refunds=True` and to skip/adjust the whitespace
   collapse in description (SPEC requires description preserved "exactly,
   including any delimiter or quote characters").
4. Implement `ingest`: merge all input files regardless of system/order, write
   sorted normalized CSV with exact header, `wrote=<n> to <path>` summary, create
   parent dirs, exit 0.
5. Implement `report`: read normalized CSV (not raw exports), group by account or
   month, apply rounding (Decimal.quantize, ROUND_HALF_EVEN, at
   `settings.decimals`), semicolon-separated output, refunds in by default per
   amendment above.
6. Implement `reconcile`: group by (account_code, month, source_system), spread =
   max−min system total among systems that posted, tolerance comparison (Decimal),
   `-` for missing systems, `MISMATCH ...` lines + trailing `mismatches=<n>` line,
   all amounts fixed 2dp regardless of report's decimals setting.
7. Implement `validate`: needs its own permissive line-by-line scan per system
   (cannot reuse strict `read_rows`), checking field count vs header, per-system
   date parse, amount parse, account code regex from
   `[validate] account_code_pattern`; WARNING per rejected row via project logger
   (file + line number + reason); `checked=<n> rejected=<n>` summary; exit 2 on
   any rejection or unreadable file, else 0.
8. Implement `--config PATH` as a top-level argparse arg; set `LEDGERKIT_CONFIG`
   env var before handler's `load_settings()` call; verify it works with every
   subcommand and touches nothing under `config/`.
9. Run `python -m pytest tests/` after each command is implemented; existing
   tests (`test_parsers.py`, `test_cli.py`) must keep passing untouched.

## Files touched
(none — discovery only this session)

## Commands to re-verify
- `python -m pytest tests/` — confirm existing tests still pass before and after changes.
- `cat SPEC.md` — check if SPEC.md has since been edited to reflect the semicolon/refunds amendments (it had not been, as of this handoff).
- `python -m ledgerkit inspect samples/system_a_export.csv` — sanity check after touching `system_a.py`.
