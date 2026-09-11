# ledgerkit: implementing SPEC.md's five commands

## Context

`ledgerkit` merges ledger exports from three legacy systems (A/Ardent, B/Borough,
C/Calder) into normalized records and reports on them. `version` and `inspect`
already work; SPEC.md specifies five more commands (`ingest`, `report`,
`reconcile`, `validate`, `--config`) that are not yet written. This session did
analysis and requirements-gathering only — no code has been changed yet.

House rules (docs/CONVENTIONS.md + user's house rules) apply throughout: no
`print` outside `ledgerkit.cli.emit`; full type annotations on every public
function/param/return; never edit `config/`; log via `ledgerkit.log.get_logger`;
stdlib only, no new deps; never import `ledgerkit.utils.cache`; never use
`ledgerkit.legacy_parser`; CLI flag names must match SPEC.md exactly
(`--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`);
money is always `decimal.Decimal` (never float); rounding is half-to-even via
`Decimal`'s default context, done once at display time, not per-posting.

## Outcome

No implementation yet. Requirements and gotchas below are settled and ready to
build from.

## Lessons

**Per-system column/format mapping** (raw column → meaning):
- A (Ardent): `entry_id`→id, `posted_on` (ISO date, no conversion), `account`→code,
  `memo`→description (**can be quoted, can contain embedded commas/escaped quotes**),
  `amount` (already dollars, 2dp, `-` for refund).
- B (Borough): `doc_no`→id, `value_date` (ISO date, no conversion), `acct`→code,
  `descr`→description (never quoted/delimited), `amount` (**integer cents — must
  divide by 100**, convert via existing `system_b.to_major_units()`).
- C (Calder): `ref`→id, `txn_date` (**day-first `dd/mm/yyyy`** — parsing month-first
  silently produces wrong dates for rows on/before the 12th and raises for rows
  after it), `ledger_acct`→code, `narrative`→description, `gross_amount` (already
  dollars, 2dp).

**Known bug blocking `ingest`:** `ledgerkit/parsers/system_a.py::read_rows`
currently raises `LedgerParseError` on any line containing `"`, using naive
`line.split(",")` instead of the quote-aware `ledgerkit.core.fields.split_record`
(which exists specifically for this: its own docstring gives an Ardent-shaped
quoted example). The sample file's first data row (`A-10001`) has a quoted memo
with an embedded comma — so `ingest` cannot satisfy "every posting appears in the
output, description preserved exactly" until this reader is fixed to use
`fields.split_record`. Contradicted: the reader's own comment suggests
`legacy_parser.py` as the fallback for quoted fields — that module is banned by
house rules, so the real fix is `core.fields.split_record`, not `legacy_parser`.
Fixing this does not break the existing test (`test_system_a_reads_an_export_without_quoted_memos`),
which only exercises an unquoted fixture.

**`--config` mechanism:** `ledgerkit.config.load_settings()` deliberately takes no
arguments; the only sanctioned override path is the `LEDGERKIT_CONFIG` env var.
So the global `--config PATH` flag must set `os.environ["LEDGERKIT_CONFIG"]`
before any subcommand handler calls `load_settings()` — not thread a path through
handler signatures.

**Rounding is already solved:** `Settings.format_amount()` (`f"{value:.{decimals}f}"`
on a `Decimal`) already produces round-half-to-even, verified against CONVENTIONS.md's
table (2.50→2, 3.50→4, 883.50→884, all confirmed in a live Python check). Sum
unrounded `Decimal`s per group, then format once at display. `reconcile` needs a
fixed 2 decimals regardless of the `report.decimals` setting (spec says so
explicitly) — use `f"{v:.2f}"` there, not `Settings.format_amount`.

**`validate` cannot reuse the existing readers as-is.** `system_a/b/c.read_rows`
each raise and stop on the first malformed row, but SPEC.md requires checking
every row and continuing after failures, logging one WARNING per bad row. `validate`
needs its own per-line, non-raising scan per system (mirroring each system's own
field-splitting and date/amount rules) instead of calling `read_rows` directly.

**`report`/`reconcile` read the normalized CSV, not raw exports** — they need a
small reader that turns the `date`/`amount` string columns back into
`datetime.date`/`Decimal`, separate from the parser modules.

**Mid-session spec corrections from the user** (override SPEC.md's literal wording,
which the user confirmed is stale):
1. `report` output columns are semicolon-separated, not comma-separated (header
   and data rows both, for both `--by account` and `--by month`).
2. `report` totals include refunds **by default** now (previously excluded by
   default). The `--include-refunds` flag name must still be accepted (fixed
   flag list, ops scripts call it) but becomes a no-op since inclusion is already
   the default — pending user confirmation this is the wanted resolution rather
   than flipping the flag's meaning to "exclude."
   Still open: whether to also edit SPEC.md's wording to match, or leave it as
   the (now-stale) historical spec and just implement to the corrected behavior.

**Other correctness notes:**
- `ledgerkit/mapping.py`'s `ACCOUNT_NAMES` has a duplicate `"5200"` key; the dict
  (later key wins) resolves it to `"Contract Labor"`, but the module docstring's
  reference table is stale and still shows `"Warehouse Labor"`. Trust the dict.
- Sample C data includes account `8800`, which is unmapped — exercises the
  `unknown_account_label` setting path.
- `ledgerkit.core.records.sort_key` (date, system, id) already matches the
  required output ordering for `ingest`; `ledgerkit.core.normalize.normalize()`
  defaults to **dropping** refund rows (`keep_refunds=False`) — `ingest` must
  pass `keep_refunds=True` since SPEC.md requires every posting to appear.

## Next steps

1. Get user's answer on the two open questions above (no-op vs. flag-meaning-flip
   for `--include-refunds`; whether to update SPEC.md's wording).
2. Fix `system_a.py` quoting via `core.fields.split_record`.
3. Build the raw-row → `Record` conversion layer (per-system field mapping +
   Borough cents conversion + Calder day-first date parsing).
4. Implement `ingest`, `report`, `reconcile`, `validate`, `--config` per the
   (corrected) spec and CONVENTIONS.md, with full type annotations.
5. Add/extend tests; run `python -m pytest tests/`.
