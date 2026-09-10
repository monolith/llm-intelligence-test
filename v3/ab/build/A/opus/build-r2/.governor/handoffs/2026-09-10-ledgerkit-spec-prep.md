# Handoff: ledgerkit — repo understood and spec updates recorded; nothing implemented yet

## Goal
Implement SPEC.md's five features (`ingest`, `report`, `reconcile`, `validate`, global `--config`) following docs/CONVENTIONS.md **and the user's two report changes below, which override SPEC.md**.

## Current state (verified against ground truth)
- [verified] No code changed. Not a git repo. `python -m pytest -q tests/` → 6 passed. Only `version` and `inspect` exist (`ledgerkit/cli.py`).
- [verified] SPEC.md is unedited and still has the OLD report wording (lines 60-61 and 80). The user was asked whether to update §2 and has not answered, so do not edit it unasked.
- [verified] Sample exports: A=42 rows (4 refunds), B=39 (1 refund), C=39. Total 120 postings, 5 refunds.
- [verified] How the systems differ:
  - A: `#` preamble, then header `entry_id,posted_on,account,memo,amount,currency`. ISO dates, decimal dollars. Quoted memos with commas and doubled `""` (sample line 6).
  - B: header `sys,doc_no,value_date,acct,descr,amount,cur`. ISO dates. Amount is **integer cents**; convert with `system_b.to_major_units`.
  - C: `CALDER EXPORT v3` banner, header `ref,txn_date,ledger_acct,narrative,gross_amount,ccy`, then a `== 39 rows ==` trailer. Dates are **dd/mm/yyyy** (`strptime "%d/%m/%Y"`), amounts are decimal dollars.
- [verified] All readers return raw strings. The ingest code building each Record converts values to `Decimal` dollars and `datetime.date` (CONVENTIONS).
- [verified] `system_a.read_rows` raises LedgerParseError on the A sample because it rejects any line containing a quote. Fix it with `core.fields.split_record`, which splits that line correctly.
- [verified] `core.normalize.normalize()` drops refunds by default (`keep_refunds=False`) and collapses description whitespace. Both break ingest ("every posting", "description preserved exactly").
- [verified] `mapping.ACCOUNT_NAMES["5200"] == "Contract Labor"`, not the "Warehouse Labor" in the docstring. 8800 is unmapped and must come out as `UNCLASSIFIED`.
- [verified] Settings: decimals=0, unknown_account_label=UNCLASSIFIED, tolerance=0.05, account_code_pattern=`^[0-9]{4}$`. `load_settings()` takes no args; the override is the `LEDGERKIT_CONFIG` env var, layered over config/settings.toml and then DEFAULTS.
- [verified] Reference sample results:
  - Report totals with refunds included (new default): 4100=6248.50 (prints as **6248**, half-even), 5100=3400.00, 5200=1747.50 (prints as **1748**), 6100=3577.20, 8800=314.95.
  - Monthly totals with refunds included: 2026-01=13256.48, 2026-02=8456.50 (prints as **8456**), 2026-03=5870.25.
  - Reconcile at the default tolerance gives 5 mismatches: 4200/2026-02 (matches SPEC's example exactly), 4300/2026-01, 5300/2026-03, 6100/2026-01, 6100/2026-02.
- [verified] `f"{Decimal:.0f}"` rounds half to even (2.50→2, 3.50→4). Still round explicitly with `quantize(ROUND_HALF_EVEN)` at display time, and only there.

## Decisions + why
- USER, overrides SPEC: `report` separates columns with **semicolons**, header included (`account_code;account_name;total`, `month;total`), because the warehouse sheet expects semicolons. Ingest's CSV stays comma-separated, and reconcile keeps its own format.
- USER, overrides SPEC: `report` **counts refunds by default**.
- OPEN: what `--include-refunds` does now. The user was asked and has not answered. My recommendation: keep it as an accepted no-op, because the flag name is fixed and ops scripts pass it.
- Implement `--config PATH` as a global option that sets `os.environ["LEDGERKIT_CONFIG"]` before dispatch, because CONVENTIONS forbids giving `load_settings()` arguments.
- House rules (user plus CONVENTIONS):
  - `print` only in `cli.emit`; log through `ledgerkit.log.get_logger(__name__)`.
  - Every public function fully annotated.
  - Stdlib only.
  - Nothing under `config/` changes.
  - Do NOT import `utils.cache` (serves stale text keyed only by path). Do NOT use `legacy_parser` (splits quoted commas wrongly).
  - Flag names exactly `--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`.

## Failure lessons
- None yet; no implementation was attempted.

## Contradicted claims (proven false — do not relearn)
- "The A reader can read the A sample": false, it raises on line 6.
- "legacy_parser is the fix for quoted memos": false, and it is banned.
- "B amounts are dollars": false, they are cents (this is how SPEC's `B=512.75` is reproduced).
- "C dates are month-first": false, they are day-first.
- "normalize() is safe for ingest": false.
- "5200 is Warehouse Labor": false, it is Contract Labor.
- "SPEC.md §2 is current": false, see Decisions.
- `/home/anatoly/llm-intelligence-test/v3/distractors/` has nothing to do with this repo.

## Next steps
1. Resolve the `--include-refunds` question and whether to update SPEC.md §2 with the user. If unanswered, implement it as a no-op.
2. Fix `system_a.read_rows` to use `fields.split_record`, keeping the field-count check.
3. Add a record-building layer: raw rows → Record with conversions per system, account name from the map or the unknown label, description kept verbatim.
4. `ingest`: sort with `records.sort_key`, write with `csv`/`join_record`, mkdir the `--out` parents, emit `wrote=N to PATH`.
5. `report` (semicolons, refunds in, half-even at display), then `reconcile` (all postings, spread > tol, two-decimal amounts, `-` for missing systems, `mismatches=n`).
6. `validate`: its own line-by-line pass (the readers stop at the first bad row). Real line numbers, date format per system, pattern from settings, WARNING per rejected row, `checked= rejected=`, exit 2 on any rejection or unreadable file.
7. `--config` global option, then tests for each command against the reference numbers above.

## Files touched
- `.governor/ledger.md` (Decisions)
- Memory: `ledgerkit-house-rules.md`, `ledgerkit-report-spec-changes.md`, `MEMORY.md`

## Commands to re-verify
- `python -m pytest -q tests/`
- `grep -n "comma\|Without it" SPEC.md`
- `cat .governor/ledger.md`
- `python -c "from ledgerkit.mapping import ACCOUNT_NAMES as m; print(m['5200'], '8800' in m)"`
