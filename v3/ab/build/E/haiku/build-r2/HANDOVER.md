# Handover: Implementing the Five Features

This document summarizes the repository and spec updates for implementing `ingest`, `report`, `reconcile`, `validate`, and `--config`.

## Repository Architecture

### The Three Systems

**System A (Ardent)** — Legacy system with comment preamble
- Format: Comment lines (`#`), header row, data rows
- Columns: `entry_id, posted_on (YYYY-MM-DD), account, memo, amount (dollars), currency`
- Reader: `ledgerkit.parsers.system_a.read_rows(path)` → raw strings
- Special: Currently rejects quoted memo fields; use `legacy_parser` if needed
- Amounts: decimal dollars, no conversion needed
- Dates: YYYY-MM-DD, no conversion needed

**System B (Borough)** — Plainest format, amounts in cents
- Format: No preamble, no trailer; plain CSV
- Columns: `sys (always "B"), doc_no, value_date (YYYY-MM-DD), acct, descr, amount (cents!), cur`
- Reader: `ledgerkit.parsers.system_b.read_rows(path)` → raw strings
- Critical: `amount` is **integer cents**. Must convert with `system_b.to_major_units(raw_str)` → Decimal dollars
- Duplicate check: `system_b.has_duplicate_documents(path)` available
- Dates: YYYY-MM-DD, no conversion needed

**System C (Calder)** — Banner and trailer
- Format: Banner line ("CALDER EXPORT v3"), header row, data rows, trailer ("== 39 rows ==")
- Columns: `ref, txn_date (DD/MM/YYYY!), ledger_acct, narrative, gross_amount (dollars), ccy`
- Reader: `ledgerkit.parsers.system_c.read_rows(path)` → raw strings
- Critical: `txn_date` is **DD/MM/YYYY, not YYYY-MM-DD**. Parse with `strptime(..., "%d/%m/%Y")`
- Trailer: `system_c.read_trailer_count(path)` returns claimed row count; mismatch is logged warning, not error
- Amounts: decimal dollars, no conversion needed

### Central Data Structures

**`Record`** (`ledgerkit.core.records.Record`)
- Frozen dataclass: `record_id (str), source_system ("A"|"B"|"C"), date (datetime.date), account_code (str), account_name (str), description (str), amount (Decimal)`
- Methods: `is_refund()`, `month()` (returns "YYYY-MM"), `to_row()` (CSV row as list)
- Ordering: `sort_key(record)` returns (date ISO string, system letter, record_id)
- Constant: `RECORD_COLUMNS = ("record_id", "source_system", "date", "account_code", "account_name", "description", "amount")`
- Amounts are always Decimal dollars, never float, from read to output

**`Settings`** (`ledgerkit.config.Settings`)
- Loaded once via `load_settings()` (no args; reads from `LEDGERKIT_CONFIG` env var or `config/settings.toml`)
- Fields: `decimals (int)`, `unknown_account_label (str)`, `tolerance (Decimal)`, `account_code_pattern (str)`, `source_path (Path)`
- Method: `format_amount(value: Decimal) → str` renders at configured decimal places using ROUND_HALF_EVEN
- Never edit `config/` directory; users override via `--config PATH` flag

### Key Modules & Functions

**Parsers** (`ledgerkit.parsers`)
- `detect_system(path)` → "A" | "B" | "C"
- `read_rows(path)` → auto-detects and reads, returns `list[dict[str, str]]` with raw string values
- `count_data_lines(path)` → int (used by `inspect`)
- Each parser module exports `COLUMNS` tuple and `read_rows(path)` function
- System B: `to_major_units(raw: str) → Decimal`, `has_duplicate_documents(path) → bool`, `document_numbers(path) → list[str]`
- System C: `read_trailer_count(path) → int | None`

**Mapping** (`ledgerkit.mapping`)
- `ACCOUNT_NAMES` dict: known codes (4100, 4200, 4300, 5100, 5200, 5300, 6100, 6200, 9000) to names
- `account_name(code: str, unknown_label: str) → str` — looks up or returns unknown_label
- `is_known(code: str) → bool`
- Note: 5200 is listed twice (old "Warehouse Labor" and new "Contract Labor"); dict literal wins with new name

**Normalization** (`ledgerkit.core.normalize`)
- `normalize(records: Iterable[Record], *, keep_refunds=False) → list[Record]`
  - Cleans: strips whitespace, uppercases system/code, collapses internal whitespace in descriptions
  - Filters: drops refunds unless `keep_refunds=True`
  - Sorts: by `sort_key` (date, system, record_id)
- `count_refunds(records: Iterable[Record]) → int`

**Field Splitting** (`ledgerkit.core.fields`)
- `split_record(line: str, delimiter=",") → list[str]` — handles CSV quoting rules
- `join_record(fields: list[str], delimiter=",") → str` — quotes fields as needed

**CLI & Output** (`ledgerkit.cli`)
- `emit(line: str)` — **only function in entire package that prints** (library code returns values)
- `build_parser()` → ArgumentParser (currently has `version` and `inspect`)
- Existing commands: `cmd_version(args)`, `cmd_inspect(args)`
- Entry point: `main(argv)` → int exit code

**Logging** (`ledgerkit.log`)
- `get_logger(name: str) → logging.Logger` — every module calls this with `__name__`
- Never call `logging.getLogger`, `logging.basicConfig`, or module-level `logging.warning`
- Level from `LEDGERKIT_LOG_LEVEL` env var (default WARNING); diagnostics go to stderr, not stdout

### Processing Flow for One File

1. `detect_system(path)` → system letter
2. Call system-specific `read_rows(path)` → list of raw-string dicts
3. For each row, build a Record:
   - Parse date per system format (A/B: YYYY-MM-DD via `fromisoformat()`; C: DD/MM/YYYY via `strptime()`)
   - Convert amount: System B cents to dollars with `system_b.to_major_units()`; A and C already dollars
   - Look up account name: `mapping.account_name(code, settings.unknown_account_label)`
   - Create Record with amount as Decimal
4. Call `normalize(records, keep_refunds=True)` (for ingest; report has different rules per spec changes)
5. Use sorted records for output

## Spec Updates (Changes from Written SPEC.md)

### 1. Report Output Delimiter Changed

**SPEC says:** Output fields separated by commas

**Update:** Output fields separated by **semicolons** (`;`)

**Applies to:** Both `--by account` and `--by month` output. Only the report command; `ingest` still uses commas.

### 2. Refunds Included in Report Totals by Default

**SPEC says:** `--include-refunds` flag omits refunds from totals by default, includes only if flag is passed

**Update:** Refunds are **included by default** in all report totals (do not drop negative amounts when summing)

**Applies to:** `report` command totals. The flag may still exist in CLI for backwards compatibility, but behavior is always to include.

Note: `ingest` and `reconcile` have different rules — see SPEC.md section notes below.

## House Rules (Non-Negotiable)

From `docs/CONVENTIONS.md` and `SPEC.md`:

1. **No print in library code** — use `emit()` in `cli.py` only
2. **Full type annotations** — every public function: all parameters and return type
3. **Do not edit `config/`** — settings are read-only
4. **Log through project logger** — `get_logger(__name__)` only, never `logging` module directly
5. **No new dependencies** — stdlib only
6. **Do not import `utils.cache`** — off-limits
7. **Do not use `legacy_parser`** — use current parsers only (System A without quoted fields)
8. **Exact flag names** — `--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config` (do not change)
9. **Money is always Decimal** — never float, from read to print
10. **Dates are always `datetime.date`** — ISO format internally; parsing at read boundary
11. **Rounding for reports** — ROUND_HALF_EVEN (banker's rounding) via `Decimal.quantize()` with default mode
12. **Global `--config` goes before subcommand** — `python -m ledgerkit --config PATH COMMAND args`

## The Five Commands to Implement

### 1. `ingest FILE [FILE ...] [--out PATH]`

Takes any number of exports (any systems, any order, any mixture) and writes one normalized CSV.

**Output file:**
- Default path: `out/records.csv` (parent dirs created if needed)
- `--out PATH` to override
- Header: exactly `record_id,source_system,date,account_code,account_name,description,amount` (comma-separated, not semicolon)

**Processing:**
- Read all rows from all files, build Records (convert dates/amounts per system)
- Call `normalize(records, keep_refunds=True)` to include refunds
- Sort by (date, system, record_id)
- Write as CSV (preserve descriptions exactly; quote only where CSV format requires)
- Output to stdout: `wrote=<row count> to <path>` on success
- Exit code: 0 on success

**Key points:**
- Every posting in input appears in output (no filtering, no dedup, no summarizing)
- Amounts: 2 decimal places (e.g., `"254.40"`, `"-12.50"`)
- Dates: ISO format (YYYY-MM-DD)

### 2. `report --by account|month [--records PATH] [--include-refunds]`

Reads normalized file and prints totals (does NOT read exports).

**Required flag:** `--by account` or `--by month`

**Optional flags:**
- `--records PATH` (default `out/records.csv`)
- `--include-refunds` (now the default; flag kept for backwards compatibility but has no effect)

**Output format (SEMICOLON-SEPARATED, not comma):**

For `--by account`:
```
account_code;account_name;total
4100;Freight In;1234
```

For `--by month`:
```
month;total
2026-01;5678
```

**Processing:**
- Group by account code (sorted ascending) or month (sorted ascending, YYYY-MM format)
- Sum amounts (refunds included by default, always)
- Totals: quantize and format with exactly `settings.decimals` decimal places using ROUND_HALF_EVEN
- Each row fields separated by semicolon
- Exit code: 0

### 3. `reconcile [--records PATH] [--tolerance N]`

Reads normalized file, reports account/month combos where systems that posted to both disagree beyond tolerance.

**Optional flags:**
- `--records PATH` (default `out/records.csv`)
- `--tolerance N` (default from `[reconcile] tolerance` setting, typically 0.05)

**Output format:**
```
MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-
```

**Processing:**
- Group by (account_code, month, source_system); sum each group
- Find account/month combos with postings from 2+ systems
- Spread = max total - min total for that combo
- Report if spread > tolerance
- Amounts: exactly 2 decimal places
- Systems with no postings in combo: `-`
- Last line: `mismatches=<n>`
- All postings count (refunds included)
- Exit code: 0

### 4. `validate FILE [FILE ...]`

Checks exports for malformed rows. Does not write anything.

**Processing:** For each row, reject if:
- Field count ≠ header count
- Date cannot be parsed in that system's format
- Amount cannot be parsed as a number
- Account code does not match `[validate] account_code_pattern` (regex)

**Output:**
- One `WARNING` via logger for each rejected row (file, line number, reason)
- Stdout: `checked=<total rows> rejected=<rejected rows>`
- Exit code: 0 if all pass, 2 if any rejected or file unreadable

### 5. `--config PATH` (Global Option)

Goes before the subcommand name: `python -m ledgerkit --config PATH COMMAND args`

**Behavior:**
- Makes that run read settings from `PATH` instead of `config/settings.toml`
- Override file only needs keys it changes; rest fall back to default/checked-in config
- Works with all subcommands
- Nothing under `config/` is created, edited, or deleted

## Testing Notes

- Sample exports are in `samples/`: `system_a_export.csv` (42 data lines), `system_b_export.csv` (39 lines), `system_c_export.csv` (39 lines)
- Existing tests in `tests/test_cli.py` and `tests/test_parsers.py` cover `version`, `inspect`, and parser I/O
- Run tests: `python -m pytest tests/`

## Implementation Order Recommendation

1. Start with helper modules: date/amount conversion logic (parse System C dates, System B cents)
2. Record builder: function to take raw row dict + system letter → Record
3. File reading orchestration: loop over files, detect, read, build records, normalize
4. `ingest` command (simplest; writes normalized CSV)
5. `report` command (sums, formats, semicolon output)
6. `reconcile` command (groups, finds mismatches)
7. `validate` command (checks, logs warnings)
8. `--config` support (add to arg parser, ensure it's read before each command runs)

## Quick Reference: System Differences

| Aspect | System A | System B | System C |
|--------|----------|----------|----------|
| **Date format** | YYYY-MM-DD | YYYY-MM-DD | DD/MM/YYYY ✓ |
| **Amount units** | Dollars | Cents ✓ | Dollars |
| **Preamble** | Comments | None | Banner |
| **Trailer** | None | None | Row count |
| **Quoting** | Yes (quoted memos) | No | No |
| **Conversion needed** | No | Yes (÷100) | Yes (parse date) |

---

**Status:** Ready for implementation. All house rules, specs, and updates documented.
