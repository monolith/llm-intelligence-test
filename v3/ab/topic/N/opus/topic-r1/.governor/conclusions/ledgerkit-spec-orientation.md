# ledgerkit: orientation before implementing SPEC.md

## Context
ledgerkit (`python -m ledgerkit`, Python 3.12, stdlib only) merges ledger exports from three systems (A Ardent, B Borough, C Calder). Only `version` and `inspect` exist. SPEC.md asks for `ingest`, `report`, `reconcile`, `validate` and a global `--config`. The rules are in docs/CONVENTIONS.md. This session read and verified the repo; no code was written. Existing tests: 6/6 pass.

## Outcome

**Export differences (verified 2026-09-11 against samples/ and the code):**

| | A | B | C |
|---|---|---|---|
| Shape | `#` preamble, header, rows | header, rows (`sys`=`B` on every row) | banner `CALDER EXPORT v3`, header, rows, `== N rows ==` trailer |
| Date | ISO | ISO | `dd/mm/yyyy`, **day first** |
| Amount | decimal dollars | **integer cents** (`system_b.to_major_units` divides by 100) | decimal dollars |
| Quoting | memos can be quoted, `""` = literal quote | none | none |
| Sample rows | 42 | 39 | 39 |

Correct `ingest` of the three samples = 120 rows.

**Traps confirmed in code:**
- `system_a.read_rows` raises on any line containing `"`, which includes the shipped sample at line 6. Fix it with `core.fields.split_record`.
- `core.normalize.normalize()` drops refunds by default (`keep_refunds=False`). It also collapses whitespace in descriptions and strips ids. Unfit for `ingest`, which must keep every posting and keep descriptions and ids exactly.
- Code `5200` resolves to "Contract Labor": the dict has the key twice and the later entry wins. Code `8800` (present in A and C) is unmapped, so it gets `unknown_account_label`.
- Default `Decimal` formatting and `quantize` round half to even, which matches the conventions (2.50→2, 883.50→884). Never use float or ROUND_HALF_UP.
- `load_settings()` takes no args, so `--config` must set `LEDGERKIT_CONFIG` in `main()` before dispatch (ideally restoring it afterwards).
- Contradicted: the table in the `mapping.py` docstring (5200 = Warehouse Labor). It is out of date.
- Contradicted: the A reader's error message pointing to `legacy_parser.py`. That module splits naively and breaks quoted memos.

**User decisions that override SPEC.md §2 (2026-09-11):**
- `report` separates fields with `;` (header and data). `ingest` stays comma separated. `reconcile` output is space separated and unchanged.
- `report` counts refunds by default.

**User house rules:**
- `print` only in `cli.emit`.
- Full type annotations on every new public function.
- Never edit `config/`.
- Log through `ledgerkit.log.get_logger`.
- No dependencies.
- Don't import `utils.cache`, which is keyed on path only and so goes stale.
- Don't use `legacy_parser`.
- Flag names exactly `--out --by --records --include-refunds --tolerance --config`.

## Lessons
- Convert B amounts and C dates only when building a `Record`. Readers return raw strings by design.
- C dates with day ≤ 12 parse without error if read month first, landing in the wrong month. Only dates after the 12th fail. So a lack of errors proves nothing.
- `validate` can't reuse the readers, which stop at the first bad row. It needs its own pass over every row, with quote-aware field counts and physical line numbers.

## Next steps
Open questions for the user (unanswered):
1. `--include-refunds` is now redundant. Keep it as an accepted flag that changes nothing (proposed)? Is a new opt-out flag wanted, and what should it be called?
2. Keep `.` as the decimal point in the semicolon report (proposed), or switch to `,`?
3. Update SPEC.md §2 to match the new decisions?
4. `validate`: reject B amounts that aren't whole cents (proposed yes)? Reject a B `sys` value other than `B` (not in SPEC's list)?
5. `--config` pointing at a missing file: currently a warning plus defaults. Should it be an error?

After that, implement the five features, adding tests under tests/ (plain pytest).
