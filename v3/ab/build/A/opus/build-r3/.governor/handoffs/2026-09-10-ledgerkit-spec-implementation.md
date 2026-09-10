# Handoff: implement SPEC.md (ingest, report, reconcile, validate, --config) in ledgerkit

## Goal
Implement the five SPEC.md features correctly, following docs/CONVENTIONS.md, the user's house rules, and the user's two amendments to SPEC §2 (below). No code has been written yet.

## Current state (verified against ground truth)
- [verified] Not a git repo. `python -m pytest tests/ -q` → 6 passed. No `out/` or `.ledgerkit-cache/` exists. No repo source file has been modified.
- [verified] CLI (`ledgerkit/cli.py`) has only `version` and `inspect`. `emit()` is the only print. `main()` dispatches on `args.handler`.
- [verified] `system_a.read_rows` FAILS on `samples/system_a_export.csv` line 6 (it refuses any quoted field). `core.fields.split_record` handles `"Rebill, ""Q1"", c"` correctly. The fix goes in the A reader (CONVENTIONS: readers own quoting). Keep `tests/test_parsers.py` passing.
- [verified] Export differences:
  - A: comment preamble; header `entry_id,posted_on,account,memo,amount,currency`; ISO date; amount in dollars.
  - B: header `sys,doc_no,value_date,acct,descr,amount,cur`; ISO date; amount in **integer cents**; use `system_b.to_major_units` (25440→254.40, -8825→-88.25).
  - C: banner `CALDER EXPORT v3`, then header `ref,txn_date,ledger_acct,narrative,gross_amount,ccy`, then trailer `== N rows ==`; date **dd/mm/yyyy** (`%d/%m/%Y`); amount in dollars.
  - All rows are USD; nothing converts currency.
- [verified] Readers return raw strings. Converting to `Record` (Decimal dollars, `datetime.date`) must happen in a per-system builder before the `Record` is built.
- [verified] `core.normalize.normalize()` drops refunds by default AND collapses whitespace in descriptions. Both break ingest ("every posting", "description preserved exactly"). Don't use it for ingest. `records.sort_key` (date, system, id) is fine to use.
- [verified] `mapping.account_name`: 5200 → "Contract Labor" (the docstring's "Warehouse Labor" is stale). 8800 is unmapped → `settings.unknown_account_label` ("UNCLASSIFIED").
- [verified] `f"{Decimal:.Nf}"` and `Settings.format_amount` round half-even: 6248.50→6248, 1747.50→1748, 8456.50→8456.
- [verified] `load_settings()` takes no args. The only override is the `LEDGERKIT_CONFIG` env var, layered over `config/settings.toml` and then over `DEFAULTS`. A missing override file logs a warning and falls back.
- [unverified — computed in memory this session, not re-run] Samples contain 120 postings, 5 of them refunds. Reconcile at tolerance 0.05 finds 5 mismatches:
  - `4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-` (matches the SPEC example exactly)
  - 4300 2026-01 (16.75)
  - 5300 2026-03 (15.45)
  - 6100 2026-01 (16.30)
  - 6100 2026-02 (11.80)
- [unverified — same run] Report totals with refunds included (the new default), to 2 dp:
  - By account: 4100 6248.50, 4200 2970.95, 4300 2885.65, 5100 3400.00, 5200 1747.50, 5300 1621.45, 6100 3577.20, 6200 4400.03, 8800 314.95, 9000 417.00.
  - By month: 2026-01 13256.48, 2026-02 8456.50, 2026-03 5870.25.

## Decisions + why
- **User amendment (2026-09-10), overrides SPEC §2:** `report` separates every line, header included, with `;` — the warehouse sheet expects semicolons. `ingest` output stays a comma-separated CSV.
- **User amendment (2026-09-10), overrides SPEC §2:** `report` counts refunds by default — they should no longer be dropped. `reconcile` already counts them.
- `--include-refunds` must stay accepted — it is a fixed flag name and ops scripts call it. **OPEN:** its new meaning. My recommendation is an accepted no-op; ask the user before finalizing.
- **OPEN:** whether to update SPEC.md §2 wording to match the amendments. Ask the user.
- `--config PATH` goes on the top-level parser and sets `os.environ["LEDGERKIT_CONFIG"]` before any `load_settings()` call. This keeps `load_settings()` argument-free as CONVENTIONS requires.
- House rules (user):
  - No `print` outside `cli.emit`.
  - Full annotations on every new public function.
  - Never edit or add anything under `config/`.
  - Log via `ledgerkit.log.get_logger(__name__)`.
  - Stdlib only.
  - Never import `utils.cache` (it writes to cwd and serves stale content).
  - Never use `legacy_parser` (naive split).
  - Flag names exactly `--out --by --records --include-refunds --tolerance --config`.
- Money stays `Decimal` end to end, including when parsing `--tolerance`. Round once, at display.

## Failure lessons
- None. Nothing was attempted and failed this session.

## Contradicted claims (proven false — do not relearn)
- "legacy_parser handles quoted fields" (the A reader's error message implies it): FALSE. It splits on every comma.
- "normalize() is safe for ingest": FALSE. It drops refunds and rewrites whitespace.
- "Borough amount is dollars": FALSE. It is cents.
- "Calder dates are month first": FALSE. They are day first; month-first reading silently misplaces days ≤12.
- "5200 is Warehouse Labor": FALSE. It is Contract Labor.
- "SPEC §2 comma separator / refunds excluded by default is current": FALSE. Superseded by the user's amendments.
- "Decimal formatting rounds half-up": FALSE. It rounds half-even, which is what CONVENTIONS requires.

## Next steps
1. Run the re-verify commands below.
2. Ask the user: meaning of `--include-refunds` (recommend no-op), and whether to update SPEC.md §2.
3. Make the A reader quote-aware using `core.fields.split_record`.
4. Write per-system raw-row → `Record` builders (B cents, C `%d/%m/%Y`, account name via mapping plus the unknown label).
5. Add the global `--config` option.
6. `ingest`: exact header, csv quoting, mkdir parents, sort by `sort_key`, print `wrote=N to PATH`.
7. `report`: read with a quote-aware reader, `;` separator, refunds included, `decimals` half-even.
8. `reconcile`: only combinations with ≥2 systems; report when spread > tolerance (strict); `-` for a system with no postings; last line `mismatches=N`.
9. `validate`: per-row checks (field count, quote-aware for A; date format per system; amount — B integer cents, A/C Decimal; account pattern). Log one WARNING per bad row with file:line. Print `checked=N rejected=M`. Exit 2 on any reject or unreadable/undetectable file.
10. Tests for each command, including the tie cases (6248.50, 1747.50, 8456.50) and a description containing `,` and `"`.

## Files touched
- `.governor/ledger.md` (decisions added)
- Memory, outside the repo: `memory/ledgerkit-house-rules.md`, `memory/ledgerkit-spec-amendments.md`, `memory/MEMORY.md`

## Commands to re-verify
- `python -m pytest tests/ -q -p no:cacheprovider`
- `PYTHONPATH=. python -c "from pathlib import Path; from ledgerkit.parsers import system_a; system_a.read_rows(Path('samples/system_a_export.csv'))"`   (expected: LedgerParseError at line 6)
- `grep -n "separated by a comma\|include-refunds" SPEC.md`   (the SPEC still shows the pre-amendment wording)
