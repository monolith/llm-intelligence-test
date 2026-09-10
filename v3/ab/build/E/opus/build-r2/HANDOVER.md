# HANDOVER: implementing SPEC.md

State at handover (2026-09-10): nothing in SPEC.md is implemented yet, and no
repository file has been changed. This file is the only addition. The baseline
`python -m pytest tests/ -q` gives 6 passed. `version` and `inspect` work.

**SPEC.md is out of date for `report`.** Section 2 below lists the user's
changes. Where they conflict with SPEC.md, they win. SPEC.md itself has not
been edited; the user was asked whether to update section 2 and has not
answered yet.

---

## 1. Rules for any work here

These come from the user and from `docs/CONVENTIONS.md`.

- Only `ledgerkit.cli.emit` calls `print`. Library code returns values.
- Log with `from ledgerkit.log import get_logger; _log = get_logger(__name__)`.
  Never use `logging.getLogger`, `logging.basicConfig` or `logging.warning`
  directly.
- Every new public function (name without a leading `_`) has type annotations
  on all of its parameters and on its return.
- Do not create, edit or delete anything under `config/`.
- No new dependencies: standard library only. Tests use plain `pytest` with no
  plugins, or `unittest`.
- **Do not import `ledgerkit.utils.cache`.** It caches file text under
  `.ledgerkit-cache/`, keyed by path, and never invalidates, so it hands back
  stale data.
- **Do not use `ledgerkit.legacy_parser`.** It splits on every comma, even
  inside quotes. An error message in `parsers/system_a.py` points to it;
  ignore that.
- CLI flag names are exactly `--out`, `--by`, `--records`, `--include-refunds`,
  `--tolerance` and `--config`. The operations team's scripts call them.
- Money is always `decimal.Decimal`, never `float`. Dates are
  `datetime.date` inside a `Record`.
- Round once, at display, **half to even**. Never round individual postings.
- Scope: no new subcommands beyond `ingest`, `report`, `reconcile` and
  `validate` (plus the global `--config`). Do not change `version` or
  `inspect`.

## 2. Spec changes after SPEC.md was written (user, 2026-09-10)

1. **`report` separates fields with semicolons, not commas.** This applies to
   every line, the header line included:
   ```
   account_code;account_name;total
   4100;Freight In;6248
   ```
   ```
   month;total
   2026-01;13256
   ```
   The reason: the warehouse team's sheet expects semicolons. Only `report`
   changes. **The `ingest` output file stays comma separated**, exactly as
   SPEC.md section 1 says.
2. **`report` counts refunds (negative amounts) in its totals by default.**
   They are no longer left out.
   - `--include-refunds` must still be accepted, because its name is fixed and
     scripts pass it. It is now a harmless no-op. Plan: keep the flag and
     change its help text to say refunds are always included.
   - Open question: with this change there is no way to get totals without
     refunds. The user was told that restoring that would need a new flag,
     which changes the fixed flag list. They have not asked for one, so do not
     add one.
3. Open question: sheets set up for semicolons often expect a decimal comma.
   At the default `decimals = 0` this doesn't matter. Totals are written with
   `.` as the decimal point unless the user says otherwise. The user has not
   answered this yet.

`reconcile` was not changed. It has always counted refunds.

## 3. Repository map

| Path | What it is |
| --- | --- |
| `ledgerkit/cli.py` | argparse, `emit`, `cmd_version` and `cmd_inspect`. `main(argv) -> int`. New commands go here. |
| `ledgerkit/config.py` | `load_settings()` (takes no arguments, by design). It layers `DEFAULTS`, then `config/settings.toml`, then the file named by `LEDGERKIT_CONFIG`. `Settings` has `decimals`, `unknown_account_label`, `tolerance` (a Decimal), `account_code_pattern` and `source_path`. A missing override file only logs a warning. |
| `ledgerkit/log.py` | The project logger. It writes to stderr in the format `LEDGERKIT LEVEL name: msg`. The level comes from `LEDGERKIT_LOG_LEVEL` (default WARNING). |
| `ledgerkit/mapping.py` | `account_name(code, unknown_label)` and `ACCOUNT_NAMES`. |
| `ledgerkit/core/records.py` | The frozen `Record` dataclass (`record_id`, `source_system`, `date`, `account_code`, `account_name`, `description`, `amount`), plus `RECORD_COLUMNS` (exactly the ingest header), `Record.to_row()`, `Record.month()`, `sort_key` (date, then system, then id) and `LedgerParseError`. |
| `ledgerkit/core/fields.py` | `split_record(line, delimiter)` is a correct quote-aware splitter (quoted fields may contain commas; `""` inside quotes becomes `"`; whitespace is kept). `join_record` also exists. |
| `ledgerkit/core/normalize.py` | `normalize()`. **Unsafe for ingest** (see 5.4). |
| `ledgerkit/parsers/__init__.py` | `detect_system(path)` (from the first line), `read_rows(path)` and `count_data_lines(path)`. |
| `ledgerkit/parsers/system_{a,b,c}.py` | One reader per system. Each returns `list[dict[str, str]]` of **raw strings** keyed by that system's own column names. Readers never interpret values; that is the caller's job. |
| `ledgerkit/legacy_parser.py`, `ledgerkit/utils/cache.py` | Banned (see section 1). |
| `samples/*.csv` | One export per system. |
| `tests/` | Smoke tests for the parsers and the CLI. The CLI tests run `python -m ledgerkit` as a subprocess with `PYTHONPATH` set to the repo. |

## 4. How the three exports differ

| | A (Ardent) | B (Borough) | C (Calder) |
| --- | --- | --- | --- |
| First line (used for detection) | `# ARDENT LEDGER EXPORT` | `sys,doc_no,value_date` | `CALDER EXPORT` (for example `CALDER EXPORT v3`) |
| File shape | `#` comment preamble, header, rows | header, rows (first column is always `B`) | banner, header, rows, trailer `== N rows ==` (a count mismatch only produces a warning) |
| Id column | `entry_id` | `doc_no` | `ref` |
| Date column and format | `posted_on`, ISO `YYYY-MM-DD` | `value_date`, ISO | `txn_date`, **`dd/mm/yyyy`, day first** |
| Account column | `account` | `acct` | `ledger_acct` |
| Description column | `memo` (**quoted** when it contains commas, with `""` escapes) | `descr` (never quoted, commas scrubbed out) | `narrative` (not quoted) |
| Amount column and units | `amount`, decimal dollars (`239.55`, `-125.00`) | `amount`, **integer cents** (`25440` = $254.40, `-8825` = −$88.25) | `gross_amount`, decimal dollars |
| Currency column | `currency` | `cur` | `ccy` (all `USD` in the samples) |

Conversions that must happen when rows become `Record`s:

- **B amount:** `system_b.to_major_units(raw)` gives Decimal dollars. If you
  skip it, totals come out 100× too big and nothing errors.
- **C date:** `datetime.strptime(raw, "%d/%m/%Y").date()`. If you read it
  month first, the dates after the 12th fail and the dates up to the 12th
  land silently in the wrong month.
- A and C amounts: `Decimal(raw)`. A and B dates: `date.fromisoformat(raw)`.

## 5. Traps in the existing code

1. **`system_a.read_rows` rejects the A sample.** It raises `LedgerParseError`
   on any line containing `"` (sample line 6), and the error message points
   at `legacy_parser`. The fix is to split data lines with
   `fields.split_record(line)` instead of `line.split(",")`, and delete the
   check that rejects quotes. The header is already split with
   `split_record`. The existing test `test_system_a_reads_an_export_without_quoted_memos`
   must keep passing. `system_b` and `system_c` use `line.split(",")`, which
   is correct because those systems never quote.
2. **5200 is named "Contract Labor".** `ACCOUNT_NAMES` lists `"5200"` twice
   and the later entry wins. The module docstring's "Warehouse Labor" is
   stale. **8800 is not in the map**, so it gets the `unknown_account_label`
   setting (`UNCLASSIFIED`). Use `mapping.account_name(code,
   settings.unknown_account_label)`.
3. **The readers stop at the first bad row** by raising. `validate` must check
   every row, so it needs its own line-by-line pass instead of calling
   `read_rows`.
4. **Do not use `normalize()` as it is in ingest.** By default
   (`keep_refunds=False`) it drops refunds, and it always squashes whitespace
   inside descriptions. It also strips and upper-cases the account code. SPEC
   requires every posting, the description exactly as written, and the
   account code as written. Build `Record`s directly and sort with
   `records.sort_key`.
5. **Rounding:** Decimal `quantize(..., ROUND_HALF_EVEN)`. Formatting a Decimal
   with an f-string, as `Settings.format_amount` does, was verified to round
   half to even (2.50→2, 3.50→4, 1240.50→1240, 883.50→884). Several sample
   totals land exactly on .50, so the samples do exercise this. Never use
   `ROUND_HALF_UP` or `floor(x+0.5)`.
6. **`load_settings()` must stay argument-free.** Implement `--config` by
   setting `os.environ[config.CONFIG_ENV_VAR]` in `main()` after parsing and
   before calling the handler. If `main()` is also called in-process by tests,
   consider restoring the previous value afterwards.
7. `inspect`'s `count_data_lines` is unrelated to the new work. Leave it
   alone.

## 6. Plan for each feature

### ingest `FILE [FILE ...] [--out PATH]`
- For each file: `detect_system`, then that system's `read_rows`, then build
  `Record`s using the conversions in section 4. `record_id` stays as the
  source wrote it; `source_system` is `A`, `B` or `C`.
- Keep every posting: no filtering, no deduplication. Sort with `sort_key`.
- `--out` defaults to `out/records.csv`. Run `mkdir(parents=True, exist_ok=True)`
  on the parent directory. Write with `csv.writer` (comma, minimal quoting,
  `newline=""`), header = `RECORD_COLUMNS`, rows = `Record.to_row()` (the
  amount already has 2 decimal places).
- On success, `emit(f"wrote={n} to {path}")` and return exit code 0. What
  happens when a file can't be read or parsed is not specified; logging a
  warning and returning non-zero is reasonable.

### report `--by account|month [--records PATH] [--include-refunds]`
- Read the normalized CSV with `csv` (it is comma separated) and parse the
  amounts as Decimal. `--by` is required, with `choices=["account", "month"]`.
- **Include refunds by default** (section 2). `--include-refunds` is accepted
  and does nothing.
- By account: header `account_code;account_name;total`, codes ascending,
  account name taken from the records file. By month: header `month;total`,
  months (`YYYY-MM`) ascending.
- Each total is rounded half to even to `settings.decimals` places.
  **Separator `;`** (section 2). Exit code 0.

### reconcile `[--records PATH] [--tolerance N]`
- Parse `--tolerance` as a Decimal (argparse `type=Decimal`). The default is
  `settings.tolerance`.
- Total by (account code, month, system), **refunds included**. Consider only
  the (code, month) pairs that at least 2 systems posted to. Spread = largest
  system total − smallest. Report when spread **>** tolerance.
- Line format: `MISMATCH {code} {month} spread={s:.2f} A={a:.2f} B={b:.2f} C={c:.2f}`,
  with `-` for a system that has no postings. Always list A, B and C.
  Order by code, then month. The last line is always `mismatches={n}`.
  Exit code 0.

### validate `FILE [FILE ...]`
- Walk each file line by line, tracking **physical line numbers**. Skip the
  structure lines (A: `#` lines and the header; B: the header; C: the banner,
  the header and the trailer) and blank lines.
- Split each data row with `fields.split_record` (quote-aware, needed for A).
  Reject the row when any of these hold:
  - its field count differs from the header's;
  - its date doesn't parse in that system's format (A/B ISO, C `%d/%m/%Y`);
  - its amount isn't a number (B: an integer number of cents, as in
    `to_major_units`; A/C: a Decimal);
  - its account code doesn't `re.fullmatch`/`re.search`
    `settings.account_code_pattern` (the pattern is anchored, `^[0-9]{4}$`).
- For each rejected row, send one `_log.warning(...)` naming the file, the
  line number and the reason. Check every row; don't stop at the first bad one.
- `emit(f"checked={checked} rejected={rejected}")`. Exit code 2 if any row
  was rejected or any file couldn't be read (including a file that
  `detect_system` doesn't recognise); otherwise 0.

### `--config PATH` (global, given before the subcommand)
- `parser.add_argument("--config", ...)` on the top-level parser. In `main()`,
  if it was given, set `LEDGERKIT_CONFIG` before dispatching. It works for
  every subcommand, `version` included (`version` prints
  `settings=<path>`, which makes a handy test). Never write under `config/`.

## 7. Expected results on the samples (default settings)

Computed during this session with a throwaway script that used the
conversions above.

- **ingest:** 120 rows (A 42, B 39, C 39), 5 of them refunds. The first A
  description must come out as `Rebill, "Q1 true-up", carrier`, so in the CSV
  it is quoted as `"Rebill, ""Q1 true-up"", carrier"`.
- **report --by account** (refunds included, 0 decimals):
  4100 Freight In 6248 (exact 6248.50) · 4200 Duty and Brokerage 2971 ·
  4300 Storage 2886 · 5100 Packaging Materials 3400 · 5200 Contract Labor 1748
  (exact 1747.50) · 5300 Equipment Rental 1621 · 6100 Utilities 3577 ·
  6200 Insurance 4400 · 8800 UNCLASSIFIED 315 · 9000 Suspense 417
- **report --by month:** 2026-01 13256 · 2026-02 8456 (exact 8456.50) ·
  2026-03 5870
- For reference only, the old refunds-excluded totals were 5100 3765,
  6100 3619, 8800 346, and months 13381 / 8587 / 6053.
- **reconcile** (tolerance 0.05):
  ```
  MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-
  MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05
  MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55
  MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60
  MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-
  mismatches=5
  ```
  The first line matches SPEC.md's example exactly, which confirms the B
  cents and C day-first handling.
- **validate** on the three samples: expected `checked=120 rejected=0`, exit
  code 0. **Not verified:** all codes, including 8800, match `^[0-9]{4}$`, and
  every C date parsed day first, but the A and B dates weren't parse-checked.

## 8. Other notes

- The extra working directory `/home/anatoly/llm-intelligence-test/v3/distractors`
  holds unrelated prose documents. It has nothing to do with ledgerkit.
- Add tests for the new commands under `tests/`, following the subprocess
  style in `tests/test_cli.py`. Use `tmp_path` for `--out` and `--config`
  files so nothing gets written into the repo or `config/`.
