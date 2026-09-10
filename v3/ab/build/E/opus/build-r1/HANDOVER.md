# HANDOVER: implementing SPEC.md

Written 2026-09-10 at the end of a read-only session. No code has been changed yet.
The 6 existing tests pass (`python -m pytest tests/`).

Read this together with `SPEC.md` and `docs/CONVENTIONS.md`. Where this file and
SPEC.md disagree, **this file wins** (see "Spec updates" below).

---

## 1. Spec updates from the user (SPEC.md not yet revised)

The user changed two things about `report` after writing SPEC.md. SPEC.md §2 still
has the old wording for both.

1. **`report` output is separated by semicolons, not commas.** This applies to the
   header line and to every data line:

   ```
   account_code;account_name;total
   4100;Freight In;6248
   ```
   ```
   month;total
   2026-01;13256
   ```

   Reason: the warehouse team's spreadsheet is set up for semicolons. This affects
   `report` only. The `ingest` output file stays a comma separated CSV with the
   exact header in SPEC.md §1, and `reconcile` output is unchanged.

2. **Refunds are counted in `report` totals by default.** Negative amounts are no
   longer left out.

### Open questions (the user has not answered yet; ask before or during implementation)

- **`--include-refunds` is now a no-op.** Recommendation given to the user: keep
  accepting the flag, doing nothing, so the operations team's scripts don't break.
  Flag names are fixed. Do **not** add an opt-out flag such as
  `--exclude-refunds` unless the user asks for it.
- **Should SPEC.md §2 be updated** to match the two changes? It was offered and
  not yet approved. Don't edit it without a yes.

---

## 2. House rules (from the user; stricter than CONVENTIONS.md in places)

- Nothing prints except `ledgerkit.cli.emit`. Library code returns values.
- Every new public function (name not starting with `_`) has type annotations on
  all of its parameters and on its return.
- Never create, edit or delete anything under `config/`.
- Log through `from ledgerkit.log import get_logger; _log = get_logger(__name__)`.
  No `logging.getLogger`, no `basicConfig`, no `logging.warning(...)`.
- Standard library only; no new dependencies. Tests use plain pytest or unittest.
- Do **not** import `ledgerkit.utils.cache`. It also writes `.ledgerkit-cache/`
  into the working directory and keys only on the path, so it serves stale data.
- Do **not** use `ledgerkit.legacy_parser`. Its `split_quoted` splits on commas
  inside quotes, which is wrong.
- CLI flag names are exactly `--out`, `--by`, `--records`, `--include-refunds`,
  `--tolerance`, `--config`.
- No changes to `version` or `inspect`, and no subcommands beyond the four new ones.
- Money is `decimal.Decimal` from reading to printing. Never `float`.
- Round once, at display, **half to even**. `f"{Decimal:.Nf}"`, which is what
  `Settings.format_amount` uses, already rounds half to even (verified: 2.50→2,
  3.50→4, 1240.50→1240, 883.50→884). Never use `ROUND_HALF_UP`.

---

## 3. Repository map (what exists)

- `ledgerkit/cli.py`: argparse with subparsers (`dest="command"`, required).
  Handlers are set with `set_defaults(handler=...)`, return an int exit code, and
  `main(argv)` returns `int(handler(args))`. `emit(line)` is the only `print`.
  `inspect` exits 1 on an unreadable file.
- `ledgerkit/config.py`: `load_settings()` takes **no arguments** on purpose.
  - Layering: `DEFAULTS`, then `config/settings.toml`, then the file named by the
    `LEDGERKIT_CONFIG` environment variable.
  - `Settings` fields: `decimals` (int, default 0), `unknown_account_label`
    (default `UNCLASSIFIED`), `tolerance` (a `Decimal`, default 0.05, built as
    `Decimal(str(...))`), `account_code_pattern` (default `^[0-9]{4}$`), and
    `source_path`.
  - `Settings.format_amount(value)` formats at `decimals` places.
  - A missing override file only logs a WARNING and silently falls back to the
    other layers.
- `ledgerkit/log.py`: the one handler, on stderr, format
  `LEDGERKIT %(levelname)s %(name)s: %(message)s`, propagation off. The level
  comes from `LEDGERKIT_LOG_LEVEL` (default WARNING).
- `ledgerkit/mapping.py`: `account_name(code, unknown_label)` and `is_known(code)`,
  both of which strip and upper-case the code.
  - **5200 is "Contract Labor"**: the key appears twice and the later one wins.
    The docstring table still says "Warehouse Labor"; ignore the docstring.
  - Known codes: 4100, 4200, 4300, 5100, 5200, 5300, 6100, 6200, 9000.
  - **8800 is unknown** and appears in both the A and C samples.
- `ledgerkit/core/records.py`:
  - `Record` is a frozen dataclass: `record_id, source_system, date (date),
    account_code, account_name, description, amount (Decimal)`.
  - Methods: `is_refund()`, `month()` (returns `YYYY-MM`), and `to_row()` (ISO
    date, amount `.2f`).
  - `RECORD_COLUMNS` is exactly the `ingest` header.
  - `sort_key` orders by date, then system, then id, which is exactly the
    `ingest` order.
  - `LedgerParseError(ValueError)`.
- `ledgerkit/core/fields.py`:
  - `split_record(line, delimiter=",")` is quote-aware, handles doubled `""`, and
    works one line at a time. It is the correct splitter for A.
  - `join_record` quotes fields containing the delimiter, `"`, or `\n` (not `\r`).
- `ledgerkit/core/normalize.py`: **`normalize()` is unsuitable for `ingest` as it
  stands.**
  - It drops refunds unless `keep_refunds=True`.
  - It always collapses runs of whitespace inside descriptions, but the spec says
    descriptions are preserved exactly.
  - Either sort with `sort_key` yourself or change `normalize` carefully. It has no
    other callers today.
- `ledgerkit/parsers/__init__.py`:
  - `detect_system(path)` works from the first line. It returns "A", "B" or "C",
    or raises `LedgerParseError`.
  - `read_rows(path)` dispatches to the right reader.
  - `count_data_lines(path)` is used by `inspect`. For C it assumes a trailer is
    present.
- `ledgerkit/parsers/system_{a,b,c}.py`:
  - Each has `read_rows(path)`, which returns `list[dict[str, str]]` of **raw
    strings** keyed by that system's own column names. Readers do not convert
    values.
  - Each has a `COLUMNS` tuple and constants (`BANNER`, `COMMENT_PREFIX`,
    `HEADER_PREFIX`, `SYSTEM_LETTER`, `TRAILER_PATTERN`).
  - Readers **raise on the first bad row**. Line numbers are physical file line
    numbers (`enumerate(..., start=1)` over every line).
- `ledgerkit/legacy_parser.py`, `ledgerkit/utils/cache.py`: both off limits (see §2).
- `samples/`: A has 42 rows, B 39, C 39. Each is a complete, well-formed example.

---

## 4. How the three exports differ

| | A (Ardent) | B (Borough) | C (Calder) |
|---|---|---|---|
| Shape | `#` comment lines, header, rows | header, rows | banner `CALDER EXPORT v3`, header, rows, trailer `== N rows ==` |
| Detected by first line | `# ARDENT LEDGER EXPORT` | `sys,doc_no,value_date` | `CALDER EXPORT` |
| record id | `entry_id` | `doc_no` | `ref` |
| date | `posted_on`, ISO `YYYY-MM-DD` | `value_date`, ISO | `txn_date`, **`dd/mm/yyyy` day first** |
| account | `account` | `acct` | `ledger_acct` |
| description | `memo` (quoted when it contains `,` or `"`, with `""` escaping) | `descr` (never quoted, no commas) | `narrative` (never quoted) |
| amount | `amount`, decimal dollars | `amount`, **integer cents** | `gross_amount`, decimal dollars |
| currency | `currency` | `cur` | `ccy` |
| other | none | `sys` column, always `B` | trailer count mismatch logs a WARNING only |

All samples are USD, and no currency conversion is specified. All three systems
write refunds with a leading minus sign.

### Conversions required, in the reader path, before building a `Record`

- **B amount:** `system_b.to_major_units(raw)` turns cents into `Decimal` dollars
  (quantized to 0.01). `25440` → 254.40 and `-8825` → -88.25. Apply it to B only.
  The header just says `amount`, so treating it as dollars gives figures 100 times
  too big and no error.
- **A and C amounts:** `Decimal(text)` directly.
- **C date:** `datetime.strptime(text, "%d/%m/%Y").date()`. Month-first parsing
  raises on days after the 12th, and silently puts the other rows in the wrong
  month. Proof it is day first: `C-0409` is `15/01/2026`.
- **A and B dates:** `date.fromisoformat(text)`.
- The spec's example line only comes out right with both conversions:
  `MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-`. A = 231.46 +
  223.54. B = 25347 + 25928 cents. C's 4200 rows all fall in January or March
  when read day first.

### Blocker: the A reader cannot read the A sample

`system_a.read_rows` raises `LedgerParseError` on any data line containing `"`,
and sample lines 6–7 have quoted memos (`"Rebill, ""Q1 true-up"", carrier"`). Fix
it to split with `core.fields.split_record(line)` in place of `line.split(",")`
and the quote check. The error message points to `legacy_parser.py`; don't
follow it. After the fix, `test_system_a_reads_an_export_without_quoted_memos`
must still pass. Add a test with quoted memos.

---

## 5. Implementation notes per feature

### `ingest FILE [FILE ...] [--out PATH]`
- For each file: `detect_system`, then the system's reader, then build a `Record`
  per row using the conversions in §4, with
  `account_name = mapping.account_name(code, settings.unknown_account_label)`.
- Keep **every** posting: no refund filter, no dedup, and descriptions exactly as
  the source wrote them (don't use `normalize()` as it stands).
- Sort with `records.sort_key`.
- Default `--out` is `out/records.csv`, relative to the working directory. Create
  parent directories with `mkdir(parents=True, exist_ok=True)`.
- Write the header `record_id,source_system,date,account_code,account_name,description,amount`
  exactly, using the `csv` module (open with `newline=""`; consider
  `lineterminator="\n"`) or `fields.join_record`. Descriptions with `,` or `"`
  must be quoted properly. Amounts are `.2f`.
- On success, emit exactly `wrote=<n> to <path>` and exit 0. The spec doesn't
  say what happens on error; a nonzero exit with a logged message is reasonable.

### `report --by account|month [--records PATH] [--include-refunds]`
- Read the normalized CSV, not the exports, with the `csv` module (descriptions
  may be quoted). Parse amounts as `Decimal`. Default `--records` is
  `out/records.csv`.
- **Separator `;`** and **refunds included by default** (see §1).
  `--include-refunds` is accepted and does nothing.
- `--by account`: header `account_code;account_name;total`, then one line per
  code in ascending order. `--by month`: header `month;total`, one line per
  `YYYY-MM` in ascending order.
- Sum the exact values and format once with `settings.format_amount(total)`,
  which uses `[report] decimals` and rounds half to even.
- Exit 0.

### `reconcile [--records PATH] [--tolerance N]`
- Parse `--tolerance` as `Decimal` (`type=Decimal` or a converter), never
  `float`. Default is `settings.tolerance`.
- Group by (account_code, month, source_system) and sum, including refunds.
  Consider only (account, month) pairs posted to by at least 2 systems.
- Spread = largest system total minus smallest. Report when the spread is
  **strictly greater** than the tolerance.
- Order by account code, then month. Line format:
  `MISMATCH <acct> <YYYY-MM> spread=<x.xx> A=<x.xx|-> B=<x.xx|-> C=<x.xx|->`.
  Every amount has 2 places, and a system with no postings is written `-`.
- Always emit `mismatches=<n>` as the last line. Exit 0.

### `validate FILE [FILE ...]`
- You can't reuse the `read_rows` functions as they are, because they stop at the
  first bad row. Walk each file line by line, reusing the reader constants and
  splitters, and **check every row**.
- Reject a row when:
  - its field count differs from the header (for A, count with `split_record`,
    which is quote aware);
  - its date doesn't parse in that system's format (ISO for A and B, `%d/%m/%Y`
    for C);
  - its amount isn't a number;
  - its account code doesn't match `settings.account_code_pattern` (`re`;
    decide between `match` and `fullmatch`, though the default pattern is
    anchored).
- Open question: B amounts are cents, and `to_major_units` requires an integer.
  Decide whether `12.50` in B counts as "a number". Rejecting it is the safer
  reading, given the format.
- For each rejected row, log one `_log.warning(...)` naming the file, the
  physical line number, and the reason.
- Emit `checked=<n> rejected=<m>`. Exit 2 if any row was rejected **or** any file
  couldn't be read or detected (`OSError`, `LedgerParseError`). Otherwise exit 0.
- Write nothing to disk.

### `--config PATH` (global, before the subcommand)
- Add it to the top-level parser, not the subparsers, so
  `python -m ledgerkit --config X report ...` works with every subcommand,
  including `version`, which already prints `settings=<source_path>`.
- `load_settings()` must keep taking no arguments. Implement the option by setting
  `os.environ["LEDGERKIT_CONFIG"]` in `main()` before the handler runs. The
  override is layered on top of `config/settings.toml`.
- Things to consider:
  - Restore the environment variable after the run, so in-process `main()` calls
    in tests don't leak into each other.
  - A missing `--config` file currently only warns and falls back. The spec is
    silent; consider failing loudly, or at least keep the warning.
- Never write into `config/`. Tests should put override TOML files in `tmp_path`.

---

## 6. Reference numbers from the samples

These were computed with a throwaway script, not with ledgerkit. Use them as
acceptance targets for `ingest samples/*.csv` followed by the commands below,
with default settings (decimals 0, tolerance 0.05).

- `ingest`: `wrote=120 to out/records.csv` (42 A, 39 B, 39 C, of which 5 are
  refunds).
- `report --by account` (refunds included, semicolons):
  ```
  account_code;account_name;total
  4100;Freight In;6248
  4200;Duty and Brokerage;2971
  4300;Storage;2886
  5100;Packaging Materials;3400
  5200;Contract Labor;1748
  5300;Equipment Rental;1621
  6100;Utilities;3577
  6200;Insurance;4400
  8800;UNCLASSIFIED;315
  9000;Suspense;417
  ```
  Half-even checks: 4100's exact total is 6248.50, which shows as 6248; 5200's is
  1747.50, which shows as 1748.
- `report --by month`:
  ```
  month;total
  2026-01;13256
  2026-02;8456
  2026-03;5870
  ```
  The exact totals are 13256.48, 8456.50 (half-even gives 8456) and 5870.25.
- `reconcile`:
  ```
  MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-
  MISMATCH 4300 2026-01 spread=16.75 A=- B=744.30 C=761.05
  MISMATCH 5300 2026-03 spread=15.45 A=204.10 B=- C=219.55
  MISMATCH 6100 2026-01 spread=16.30 A=533.60 B=549.90 C=533.60
  MISMATCH 6100 2026-02 spread=11.80 A=498.25 B=510.05 C=-
  mismatches=5
  ```
- `validate samples/*.csv` should pass every row (`checked=120 rejected=0`, exit
  0), assuming the default account pattern. 8800 matches `^[0-9]{4}$`.

---

## 7. Suggested order

1. Fix the A reader to handle quoted memos, and add a test.
2. Add per-system record building (conversions in §4), plus the ingest writer.
3. `report` and `reconcile`, reading the normalized CSV.
4. `validate`.
5. `--config`.
6. Tests for each feature in `tests/`, using subprocesses as in `test_cli.py`.
   Run them from a temp working directory or pass `--out` into `tmp_path`, so
   nothing is written into the repo.
