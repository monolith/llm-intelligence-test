# ledgerkit: preparation for implementing SPEC.md

## Context
ledgerkit (Python 3.12, stdlib only) reads ledger exports from three systems, A (Ardent), B (Borough) and C (Calder). SPEC.md defines four new subcommands (`ingest`, `report`, `reconcile`, `validate`) and a global `--config` option. So far the repo has only been read and analysed; **no code has been written**. Verified 2026-09-11: the 6 existing tests pass.

## Outcome

**The user changed `report` after writing SPEC.md; these changes override SPEC §2:**
- Output fields are separated by semicolons (`account_code;account_name;total`, `month;total`). This applies only to `report`. The records CSV and `reconcile` output are unchanged.
- Refunds are included by default. `--include-refunds` is still accepted but does nothing, because the ops scripts pass it. Do not add an exclude flag.

**User's house rules** (beyond docs/CONVENTIONS.md):
- Do not import `utils.cache` and do not use `legacy_parser`.
- Do not edit `config/`, and add no dependencies.
- `print` appears only in `cli.emit`. Log through `ledgerkit.log.get_logger`.
- Every public function has full type annotations.
- Flag names stay exactly as in SPEC.md.

**How the exports differ** (readers return raw strings; convert while building each `Record`):

| | Date | Amount | Shape |
|---|---|---|---|
| A | ISO | Decimal dollars | `#` preamble; memos quoted with embedded `,` and `""` |
| B | ISO | **Integer cents**; convert with `system_b.to_major_units` | Header + rows, never quoted |
| C | **`dd/mm/yyyy`**; parse with `%d/%m/%Y` | Decimal dollars | Banner, header, rows, `== N rows ==` trailer |

**Traps (verified):**
- The A reader raises on the sample because it rejects any quote. Fix it with `core.fields.split_record`.
- Contradicted: "use `legacy_parser` for quoted fields". The A reader's error message says this, but `legacy_parser` splits on every comma, including those inside quotes.
- Contradicted: "`normalize()` is safe for ingest". By default it drops refunds, and it also strips ids and collapses whitespace in descriptions. Sort with `records.sort_key` only.
- Contradicted: "5200 = Warehouse Labor". That comes from the out-of-date docstring; the dict's later key wins, so 5200 is **Contract Labor**. Code 8800 is unmapped and shows as `UNCLASSIFIED`.
- Rounding must be explicit: `quantize(..., ROUND_HALF_EVEN)` once, on the total. `Settings.format_amount` only lays the value out; it does not choose a rounding mode.
- Money is `Decimal` throughout, and `--tolerance` is parsed as `Decimal`.
- `--config` should set `LEDGERKIT_CONFIG` before the handler runs. `load_settings()` stays argument-free by convention.
- `validate` cannot reuse `read_rows`, because the readers stop at the first bad row and return no line numbers.

**Expected results on `samples/`** (default settings, verified):
- `ingest`: `wrote=120` (5 of them refunds). Getting 115 means refunds were dropped.
- `report --by account`: 4100 6248, 4200 2971, 4300 2886, 5100 3400, 5200 1748, 5300 1621, 6100 3577, 6200 4400, 8800 315, 9000 417
- `report --by month`: 2026-01 13256, 2026-02 8456, 2026-03 5870. Half up would give 6249 and 8457, which is wrong.
- `reconcile`: `mismatches=5`. The first line matches SPEC exactly: `MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-`
- `validate`: expected `checked=120 rejected=0` [unverified: not yet implemented].

## Lessons
- These conversions are only confirmed correct because the reconcile output matches SPEC's example line. Use that line as the regression check.

## Next steps
1. Waiting on the user for two answers:
   - Should SPEC.md §2 be updated to match the amendments?
   - Should `validate` reject a B amount that isn't whole cents (such as `12.50`)? Recommendation: yes, because `to_major_units` would fail on it during ingest.
2. Then implement, in this order: A-reader quoting fix, record building, `ingest`, `report`, `reconcile`, `validate`, `--config`. Add tests using the expected results above.
