# Handoff: Implement five ledgerkit features from SPEC.md with spec amendments

## Goal
Implement `ingest`, `report`, `reconcile`, `validate` commands and `--config` global option in ledgerkit, correctly handling the three system export formats (A: Ardent, B: Borough, C: Calder) and adhering to strict money/date/logging conventions.

## Current state (verified against ground truth)

- [verified] All six existing tests pass (version, inspect, three system readers, format detection)
- [verified] `ingest`, `report`, `reconcile`, `validate` handlers are already implemented in `cli.py` (lines 129–336)
- [verified] Commands are fully functional: ingest merges exports, report totals by account/month, reconcile finds mismatches, validate checks malformed rows
- [verified] `--config` global option already works and sets `LEDGERKIT_CONFIG` env var
- [verified] Converters (`system_a_to_record`, `system_b_to_record`, `system_c_to_record`) are implemented in `core/convert.py`
- [verified] Readers for all three systems implemented; system detection works correctly

## Critical system differences (must convert both amounts and dates)

**Dates:**
- System A & B: ISO `YYYY-MM-DD` — use as-is
- System C: Day-first `DD/MM/YYYY` — must parse with `strptime(..., "%d/%m/%Y")`

**Amounts:**
- System A & C: Decimal dollars (e.g., `239.55`) — use as-is
- System B: **Integer cents** (e.g., `25440` = $254.40) — divide by 100: `Decimal(cents) / Decimal(100)`

## Spec amendments (changes since SPEC.md was written)

1. **Report output: semicolon separator**
   - Change from: `account_code,account_name,total`
   - Change to: `account_code;account_name;total`
   - Affects lines 210, 213, 221, 224 in `cli.py` (all `emit()` calls in `cmd_report`)

2. **Report: include refunds by default**
   - Current behavior: refunds excluded unless `--include-refunds` flag passed
   - New behavior: refunds **always included** by default
   - Change line 199 from `if args.include_refunds or record.amount >= 0:` to `records.append(record)`
   - **OPEN QUESTION:** What should `--include-refunds` flag do under new regime? (No clarification received; flag still defined in parser but may become no-op, need to confirm)

## House rules (non-negotiable)

- No `print()` in library code; only `cli.emit()` prints
- Every public function: full type annotations on all parameters + return type
- Money: always `Decimal`, never `float` (standard library only)
- Dates: always `datetime.date` (readers know their system's format)
- No imports of `utils.cache` or use of `legacy_parser`
- Never modify anything under `config/` directory
- Log via `ledgerkit.log.get_logger(__name__)` (not `logging.getLogger()`)
- CLI flag names frozen: `--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`
- Rounding: half to even (via `Decimal.quantize` default), applied once at display time only

## Failure lessons

- System B amounts are 100x too large if treated as dollars (mistake caught by importers before)
- System C dates read backwards if parsed as `MM/DD/YYYY` instead of `DD/MM/YYYY` (rows after 12th silently land in wrong month)
- Refunds can quietly corrupt reports if float arithmetic is used anywhere in the pipeline

## Contradicted claims (proven false)

- **NOT true:** "Commands are not implemented" — all four commands + `--config` are already fully functional as of session start
- **NOT true:** "The implementation is broken" — all commands work correctly against sample data; existing tests pass

## Next steps

1. Clarify: what should `--include-refunds` flag do when refunds are included by default? (Ignore it? Invert it? Delete it?)
2. Update `cmd_report` to use semicolon separators in all output lines (header + data rows, both by-account and by-month)
3. Update `cmd_report` to remove refund filtering (line 199: always append records)
4. Run full command suite against all three sample exports to verify output matches spec
5. Confirm no new tests are needed (existing test coverage adequate per SPEC.md)

## Files to modify

- `ledgerkit/cli.py` — report output format and refund handling (lines 199–225)

## Files read-only (verified)

- `SPEC.md` — requirements document (with amendments noted above)
- `docs/CONVENTIONS.md` — house rules
- `ledgerkit/core/records.py` — Record type and sort contract
- `ledgerkit/core/convert.py` — system converters
- `ledgerkit/parsers/*` — readers for three systems
- `ledgerkit/config.py` — settings loading
- `ledgerkit/log.py` — logger setup

## Commands to re-verify in next session

```bash
python -m pytest tests/ -v
python -m ledgerkit version
python -m ledgerkit ingest samples/system_a_export.csv samples/system_b_export.csv samples/system_c_export.csv --out /tmp/all.csv
python -m ledgerkit report --by account --records /tmp/all.csv
python -m ledgerkit report --by month --records /tmp/all.csv
python -m ledgerkit reconcile --records /tmp/all.csv
python -m ledgerkit validate samples/system_*.csv
```
