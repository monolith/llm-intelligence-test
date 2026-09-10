# Handover: Five Features to Implement

This document contains everything needed to implement the five commands in SPEC.md: `ingest`, `report`, `reconcile`, `validate`, and `--config`.

## Repository Overview

**ledgerkit** is a CLI tool that normalizes exports from three legacy ledger systems (A, B, C) and produces reports. Currently `version` and `inspect` work; the five features below are not implemented.

Key files:
- `ledgerkit/cli.py` — command line parser and handlers
- `ledgerkit/core/records.py` — the `Record` dataclass
- `ledgerkit/core/normalize.py` — `normalize()` function
- `ledgerkit/mapping.py` — account code → name mapping
- `ledgerkit/config.py` — settings loading
- `ledgerkit/parsers/` — readers for each system
- `config/settings.toml` — checked-in default settings

## The Three Export Systems: Key Differences

### System A (Ardent)
- **Format**: Preamble (comment lines starting with `#`) + header + data rows
- **Header**: `entry_id, posted_on, account, memo, amount, currency`
- **Date format**: ISO (YYYY-MM-DD), e.g., `2026-01-03`
- **Amount**: Decimal dollars (e.g., `239.55`, `-125.00` for refunds)
- **Detection**: First line is `"# ARDENT LEDGER EXPORT"`
- **Parser**: `ledgerkit/parsers/system_a.py`

### System B (Borough)
- **Format**: Header + data rows (no preamble)
- **Header**: `sys, doc_no, value_date, acct, descr, amount, cur`
- **Date format**: ISO (YYYY-MM-DD), e.g., `2026-01-07`
- **Amount**: **Integer cents, not dollars.** `25440` = $254.40. `−8825` = −$88.25. **Must divide by 100.**
- **Detection**: First line starts with `"sys,doc_no,value_date"`
- **Parser**: `ledgerkit/parsers/system_b.py`; function `to_major_units(raw)` converts cents to dollars

### System C (Calder)
- **Format**: Banner + header + data rows + trailer
- **Header**: `ref, txn_date, ledger_acct, narrative, gross_amount, ccy`
- **Date format**: DD/MM/YYYY, e.g., `02/01/2026` = January 2nd (not February 1st)
- **Amount**: Decimal dollars (e.g., `386.54`)
- **Detection**: First line is `"CALDER EXPORT"`
- **Parser**: `ledgerkit/parsers/system_c.py`

## Data Flow & Architecture

1. **Readers** extract raw strings keyed by source system's column names. No conversion happens here.
   - `read_rows(path)` → `list[dict[str, str]]`

2. **Caller converts raw strings to `Record` objects:**
   - Amount: System A and C as-is; System B must divide by 100
   - Date: System A and B parse as YYYY-MM-DD; System C parse as DD/MM/YYYY
   - Account name: look up in `mapping.ACCOUNT_NAMES`, fall back to `settings.unknown_account_label`
   - Use `mapping.account_name(code, unknown_label)` helper

3. **`normalize(records, keep_refunds=False)`** cleans and sorts:
   - Strips field text, upper-cases system and account code
   - Collapses whitespace in description
   - Filters refunds by default (set `keep_refunds=True` to keep them)
   - Sorts by `(date, source_system, record_id)` via `sort_key(record)`

4. **Output**: `Record.to_row()` renders as list matching `RECORD_COLUMNS` order

## Settings & Configuration

Settings are layered: built-in defaults → `config/settings.toml` → `$LEDGERKIT_CONFIG` override.

**Load settings:**
```python
from ledgerkit.config import load_settings
settings = load_settings()  # no arguments
```

**Available settings:**
- `settings.decimals` — decimal places for report totals
- `settings.unknown_account_label` — label for unknown account codes
- `settings.tolerance` — max $ difference for systems to agree (reconcile)
- `settings.account_code_pattern` — regex pattern to validate codes
- `settings.source_path` — Path to the settings file used

**Methods:**
- `settings.format_amount(value: Decimal) -> str` — render amount at configured decimals with half-to-even rounding

## House Rules (Non-Negotiable)

1. **No print in library code** — only `cli.emit(line)` calls `print()`. Library functions return values.
2. **Full type annotations** — every public function (name doesn't start with `_`) must have type hints on all parameters and return type.
3. **Use project logger** — `from ledgerkit.log import get_logger; _log = get_logger(__name__)`. Never call `logging.getLogger()` directly.
4. **Amounts are `Decimal`** — never `float`. Convert at read time (System B cents → dollars). Rounding happens at display time only, using half-to-even mode (banker's rounding).
5. **Dates are `datetime.date`** — each reader knows its own system's date format.
6. **Never edit `config/`** — settings are checked in and identical for all operators. Overrides come via `LEDGERKIT_CONFIG` env var.
7. **No new dependencies** — standard library only.
8. **Don't import `utils.cache` or use `legacy_parser`** — these are known problematic modules.
9. **Keep CLI flags exactly as specified** — `--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`.

## Spec Updates (Differ from Written SPEC.md)

### 1. Report Command — Output Delimiter
**SPEC says**: columns separated by commas
**ACTUAL**: columns separated by **semicolons (`;`)**
The warehouse team's sheet is configured for semicolon-delimited input.

### 2. Report Command — Refunds in Totals
**SPEC says**: refunds dropped by default, included with `--include-refunds` flag
**ACTUAL**: refunds **included by default** in report totals

Note: The `--include-refunds` flag is mentioned in SPEC.md but its behavior/necessity needs clarification (likely to be removed, or possibly reversed to exclude refunds).

## The Five Commands to Implement

### 1. `ingest` — merge exports into one normalized CSV
```
python -m ledgerkit ingest FILE [FILE ...] [--out PATH]
```
- Reads any number of exports from any mix of systems A, B, C
- Writes one normalized CSV with header: `record_id,source_system,date,account_code,account_name,description,amount`
- Output sorted by date, then system, then record_id
- `--out PATH` defaults to `out/records.csv`; creates parent directories
- Prints summary: `wrote=<row_count> to <path>`
- Exit code 0 on success

### 2. `report` — totals by account or month
```
python -m ledgerkit report --by account|month [--records PATH] [--include-refunds]
```
- Reads normalized file (default `out/records.csv`)
- `--by account`: columns `account_code;account_name;total`, sorted by code
- `--by month`: columns `month;total`, sorted chronologically (YYYY-MM format)
- **Columns separated by semicolons, not commas**
- **Refunds included by default** (note: spec update on flag)
- Amounts formatted per `settings.decimals` using half-to-even rounding
- Exit code 0

### 3. `reconcile` — find disagreements between systems
```
python -m ledgerkit reconcile [--records PATH] [--tolerance N]
```
- Reads normalized file; groups by account code, month, and source system
- Compares totals for combinations where ≥2 systems posted
- Spread = max total − min total
- Reports mismatches where spread > tolerance (default from `settings.tolerance`)
- Format: `MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-`
- Systems with no postings shown as `-`
- Ends with `mismatches=<n>`
- Exit code 0

### 4. `validate` — reject malformed rows
```
python -m ledgerkit validate FILE [FILE ...]
```
- Checks export files without writing
- Rejects rows if:
  - field count ≠ header field count
  - date can't be parsed in system's format
  - amount can't be parsed as number
  - account code doesn't match `settings.account_code_pattern` regex
- One `WARNING` log per rejected row (via project logger)
- Prints summary: `checked=<rows> rejected=<rows>`
- Exit code 0 if all pass; exit code 2 if any row rejected or file unreadable

### 5. `--config PATH` — global settings override
```
python -m ledgerkit --config PATH COMMAND ...
```
- Global option, given before subcommand
- Makes this run read settings from PATH instead of default
- Works with all subcommands
- Implementation: already handled by `load_settings()` reading `$LEDGERKIT_CONFIG` env var; CLI just needs to set it

## Key Functions & Utilities Available

**Parsing:**
- `parsers.detect_system(path)` → `"A"` | `"B"` | `"C"`
- `parsers.read_rows(path)` → `list[dict[str, str]]` (auto-detects system)
- `parsers.count_data_lines(path)` → int

**System-specific:**
- `parsers.system_b.to_major_units(raw: str)` → `Decimal` (cents → dollars)

**Records:**
- `Record` dataclass with `to_row()` method and helper methods `is_refund()`, `month()`
- `sort_key(record)` → sort tuple for standard ordering
- `RECORD_COLUMNS` tuple of header names

**Normalization:**
- `normalize(records, keep_refunds=False)` → cleaned, sorted list
- `count_refunds(records)` → int

**Mapping:**
- `mapping.account_name(code, unknown_label)` → name
- `mapping.is_known(code)` → bool
- `mapping.ACCOUNT_NAMES` dict

**Fields:**
- `core.fields.split_record(line, delimiter=",")` → list of fields (respects quoting)
- `core.fields.join_record(fields, delimiter=",")` → line (quotes as needed)

**Config:**
- `config.load_settings()` → `Settings` object
- `Settings.format_amount(Decimal) → str` with proper rounding

**Logging:**
- `log.get_logger(__name__)` → logger instance

**CLI:**
- `cli.emit(line)` → prints to stdout (only printing function in library code)

## Testing

Run existing tests:
```
python -m pytest tests/
```

Tests are in `tests/test_cli.py` (smoke tests for version, inspect) and `tests/test_parsers.py` (reader tests). New tests for the five commands will likely be added.

## Next Steps

1. Implement the five commands in `cli.py`, wiring them to the argument parser
2. Implement handler functions for each command
3. Each handler should:
   - Read files using `parsers.read_rows()` or open normalized CSV
   - Convert raw strings to `Record` objects (pay attention to date/amount conversions per system)
   - Use `normalize()` as appropriate
   - Format and `emit()` output
   - Return appropriate exit code
4. Ensure all public functions have full type annotations
5. Log diagnostics through the project logger, not print
6. Remember: `--include-refunds` flag behavior needs clarification (may be removed or reversed)
