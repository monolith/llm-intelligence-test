# HANDOVER: implementing SPEC.md

Notes for the next session. Nothing in SPEC.md is implemented yet, and no code
has been changed. The only file the previous session added is this one.
`python -m pytest tests/` passes (6 tests) on the untouched tree.

Read SPEC.md, docs/CONVENTIONS.md, and the spec updates below. Where they
disagree with SPEC.md, **the updates below win**.

---

## 1. Spec updates from the user (SPEC.md still has the old wording)

These came from the user after SPEC.md was written. SPEC.md has **not** been
edited to reflect them. The user was asked whether to update SPEC.md section 2
and has not answered yet, so leave it alone unless they say to.

1. **`report` uses semicolons, not commas.** Both the header and the data lines
   are separated by `;`. The warehouse team's sheet is set up for semicolons.
   ```
   account_code;account_name;total
   4100;Freight In;1234
   ```
   ```
   month;total
   2026-01;5678
   ```
   This applies to `report` only. `ingest` still writes a comma-separated CSV,
   and `reconcile`'s output doesn't change.
2. **Refunds count in `report` totals by default.** Negative amounts are no
   longer dropped. A total is the plain sum of every posting.

### Open question: `--include-refunds` (not answered yet)

`--include-refunds` is one of the fixed flag names the ops scripts call, so it
must stay accepted. Removing it would make argparse reject any script that
passes it. With refunds now included by default, the recommended handling
(proposed to the user, not yet confirmed) is: **keep accepting the flag and
have it do nothing.** Don't add an `--exclude-refunds` or any other new flag;
that would be a flag name outside the fixed list. Confirm with the user if you
can.

---

## 2. House rules (from the user; most also appear in docs/CONVENTIONS.md)

- No `print` in library code. `ledgerkit.cli.emit` is the only function that
  prints, and all standard output goes through it.
- Every new public function (any name not starting with `_`) has type
  annotations on **all** of its parameters **and** on its return.
- Don't edit, create or delete anything under `config/`.
- Log through the project logger:
  `from ledgerkit.log import get_logger; _log = get_logger(__name__)`.
  No `logging.getLogger`, no `basicConfig`, no module-level `logging.warning`.
- No new dependencies: standard library only. Tests use plain pytest with no
  plugins, or unittest.
- **Don't import `ledgerkit.utils.cache`.** It's also unsafe: it keys on the
  path only, so a changed file returns stale data, and it writes
  `.ledgerkit-cache/` into the working directory.
- **Don't use `ledgerkit.legacy_parser`.** It splits on every comma, which
  breaks quoted memos.
- Keep the CLI flag names exactly as SPEC.md states them: `--out`, `--by`,
  `--records`, `--include-refunds`, `--tolerance`, `--config`.
- Money is `decimal.Decimal` from the moment it's read to the moment it's
  printed. Never `float`.
- Report totals round **half to even**, once, at display time. Don't round the
  individual postings.
- Dates are `datetime.date` inside a `Record`.
- Don't change `version` or `inspect`, and add no subcommands beyond `ingest`,
  `report`, `reconcile` and `validate`.

---

## 3. How the three exports differ

| | A (Ardent) | B (Borough) | C (Calder) |
|---|---|---|---|
| How it's detected (first line) | `# ARDENT LEDGER EXPORT` | starts with `sys,doc_no,value_date` | starts with `CALDER EXPORT` |
| File layout | `#` comment lines, then header, then rows | header, then rows; column `sys` is always `B` | banner line, header, rows, then trailer `== N rows ==` |
| Record id column | `entry_id` | `doc_no` | `ref` |
| Date column | `posted_on`, ISO `YYYY-MM-DD` | `value_date`, ISO `YYYY-MM-DD` | `txn_date`, **`dd/mm/yyyy` (day first)** |
| Account column | `account` | `acct` | `ledger_acct` |
| Description column | `memo`, **may be quoted** (commas inside, `""` for a literal quote) | `descr`, never quoted | `narrative`, not quoted |
| Amount column | `amount`, decimal dollars | `amount`, **integer cents** | `gross_amount`, decimal dollars |
| Currency column | `currency` | `cur` | `ccy` |

### Amounts and dates are NOT comparable as written

- **B amounts are whole cents.** `25440` is $254.40 and `-8825` is -$88.25.
  Convert with `ledgerkit.parsers.system_b.to_major_units` (checked: it gives
  `-88.25` for `-8825`). Nothing calls it yet. If you forget it, B comes out
  100 times too large with no error. Convert while reading, before the value
  goes into a `Record`.
- **C dates are day first.** Parse `txn_date` with `%d/%m/%Y`. Read month
  first, dates after the 12th crash, and dates up to the 12th silently land in
  the wrong month. The C reader passes the field through untouched, so
  converting it is the caller's job.
- A and B dates are ISO. A and C amounts are ordinary decimal dollars with a
  minus sign on refunds.

**Check:** SPEC's reconcile example comes out only if both conversions are
done. For 4200 in February 2026: A = 231.46 + 223.54 = 455.00; B = 25347 +
25928 cents = 512.75; C has no 4200 postings in February (its 4200 rows are
dated 15/01, 18/01, 22/01, 17/03 and 19/03). That gives
`MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-`. Use it as a test
case.

### Sample facts (`samples/`)

- A: 42 rows, 4 refunds, 2 quoted memos (lines 6 and 7). B: 39 rows, 1 refund.
  C: 39 rows, and its trailer says 39. **120 postings in total.**
- Account code `8800` isn't in the account map: 4 rows, 2 in A and 2 in C. It
  gets the `UNCLASSIFIED` label, but it matches the `^[0-9]{4}$` pattern, so
  `validate` must accept it.
- No record id appears twice, within a file or across files.
- All files are plain ASCII with LF line endings.

---

## 4. Traps in the existing code

1. **`system_a.read_rows` can't read the A sample.** It raises
   `LedgerParseError` on any line containing `"` (confirmed: it fails on
   `system_a_export.csv` line 6). Its error message points to
   `legacy_parser.py`; don't go there. Use `ledgerkit.core.fields.split_record`,
   which handles quoted fields and doubled quotes correctly (confirmed on
   `"Rebill, ""Q1 true-up"", carrier"`). Either fix the A reader to split with
   it, or parse A rows with it in the new code. Existing test
   `test_system_a_reads_an_export_without_quoted_memos` must keep passing.
2. **Don't use `ledgerkit.core.normalize.normalize()` for ingest.** It drops
   refunds by default (`keep_refunds=False`), and `_clean` collapses whitespace
   inside descriptions. SPEC requires every posting in the output and the
   description kept exactly. Sort with `ledgerkit.core.records.sort_key`
   (date, then system, then record id) instead.
3. **Account 5200 is named "Contract Labor".** `mapping.ACCOUNT_NAMES` lists
   5200 twice on purpose; the later entry wins. The module docstring's table
   still says "Warehouse Labor"; ignore it. Use
   `mapping.account_name(code, settings.unknown_account_label)`.
4. **The readers stop at the first bad row** (`LedgerParseError`). `validate`
   has to check every row, so it needs its own row-by-row pass that splits A
   lines with the quote-aware splitter.
5. **`load_settings()` takes no arguments by design.** CONVENTIONS says the
   one way to point at other settings is the `LEDGERKIT_CONFIG` environment
   variable. Implement `--config PATH` as a top-level argparse option (before
   the subcommand) that `main()` turns into `os.environ["LEDGERKIT_CONFIG"]`
   (`config.CONFIG_ENV_VAR`) before calling the handler. Settings are layered:
   `DEFAULTS`, then `config/settings.toml`, then the override file. A missing
   override file only logs a warning and falls back; SPEC doesn't say whether
   that should be an error.
6. **Rounding.** `Settings.format_amount` formats with an f-string, which
   rounds half to even under the default decimal context (checked: 2.50→2,
   3.50→4, 1240.50→1240, 883.50→884, matching CONVENTIONS). It depends on the
   context, though, so round explicitly with
   `value.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_EVEN)`
   before formatting. Never use `ROUND_HALF_UP` or `floor(x + 0.5)`.
7. **`count_data_lines`** (used by `inspect`) for C assumes banner, header and
   trailer, and subtracts 3. Don't touch `inspect`.
8. **`csv.writer` ends lines with `\r\n` by default.** SPEC doesn't say which
   line ending to use, so choose deliberately (probably `lineterminator="\n"`,
   to match the input files).

---

## 5. What each feature needs (SPEC plus the updates)

### `ingest FILE [FILE ...] [--out PATH]`
- Detect each file with `parsers.detect_system`. Files can be mixed and in any
  order.
- Build a `Record` for every row:
  - `record_id`: the raw id.
  - `source_system`: `A`, `B` or `C`.
  - `date`: parsed as in section 3.
  - `account_code`: the code the source wrote.
  - `account_name`: from the map, or the unknown label.
  - `description`: exactly as written.
  - `amount`: `Decimal` dollars, with B divided by 100.
- Header exactly
  `record_id,source_system,date,account_code,account_name,description,amount`.
- ISO dates and two-decimal amounts (`Record.to_row` already renders both).
- Quote fields as CSV requires (`csv` module or `fields.join_record`).
- Nothing is filtered, deduplicated or summarized. Sort by date, then system,
  then id.
- `--out` defaults to `out/records.csv`. Create parent directories.
- On success, `emit(f"wrote={n} to {path}")` and exit 0.

### `report --by account|month [--records PATH] [--include-refunds]`
- Reads only the normalized file (default `out/records.csv`), with a
  quote-aware CSV reader.
- **Refunds count by default** (update 2). `--include-refunds` is accepted and
  does nothing (the open question in section 1).
- `--by account`: header `account_code;account_name;total`, codes ascending.
- `--by month`: header `month;total`, months ascending as `YYYY-MM`.
- **Fields separated by `;`** (update 1).
- Totals are summed as `Decimal`, rounded half to even to `[report] decimals`
  places (default 0), once, at display.
- Exit 0.

### `reconcile [--records PATH] [--tolerance N]`
- Reads the normalized file. **Refunds count.**
- Group by account code, month and system, and total each group.
- Consider only account and month combinations that at least 2 systems posted
  to.
- Spread is the largest system total minus the smallest. Report the
  combination when spread > tolerance (**strictly** greater).
- Parse `--tolerance` as `Decimal`. It defaults to `[reconcile] tolerance`
  (0.05), which `Settings.tolerance` already holds as a `Decimal`.
- Line format: `MISMATCH <code> <YYYY-MM> spread=X.XX A=X.XX B=X.XX C=X.XX`.
  All amounts have 2 decimal places, and a system with no postings is `-`.
  Order by account code, then month.
- The last line is always `mismatches=<n>`. Exit 0.

### `validate FILE [FILE ...]`
- Writes nothing.
- Reject a row if:
  - its field count differs from the header (quote-aware for A);
  - its date doesn't parse in that system's format (ISO for A and B,
    `%d/%m/%Y` for C);
  - its amount isn't a number;
  - its account code doesn't match `[validate] account_code_pattern`.
- Judgment call: for B, also reject an amount that isn't an integer number of
  cents (`to_major_units` raises on those).
- One `_log.warning(...)` per rejected row, naming the file, the physical line
  number, and what's wrong. Check every row; don't stop at the first bad one.
- Skip A's comment lines, C's banner and trailer, and the header row.
- `emit(f"checked={checked} rejected={rejected}")`.
- Exit 2 if any row is rejected or a file can't be read (missing file,
  unrecognized first line). Otherwise exit 0.

### `--config PATH` (global)
- A top-level option, given before the subcommand, that works with every
  subcommand. Set `LEDGERKIT_CONFIG` in `main()` (see section 4, trap 5).
- Never create or modify anything under `config/`.

---

## 6. Repository map

- `ledgerkit/cli.py`: argparse (`build_parser`), `emit`, `cmd_version`,
  `cmd_inspect`, and `main(argv) -> int`. New subcommands go here, with
  handlers set through `set_defaults(handler=...)`.
- `ledgerkit/config.py`: `Settings` (decimals, unknown_account_label,
  tolerance as Decimal, account_code_pattern, source_path), `load_settings()`,
  `CONFIG_ENV_VAR`, `DEFAULTS`.
- `ledgerkit/log.py`: `get_logger`. It logs to stderr with the format
  `LEDGERKIT %(levelname)s %(name)s: %(message)s`; the level comes from
  `LEDGERKIT_LOG_LEVEL` and defaults to WARNING.
- `ledgerkit/mapping.py`: `ACCOUNT_NAMES`, `account_name(code,
  unknown_label)`, `is_known(code)`.
- `ledgerkit/core/records.py`: `Record` (frozen dataclass with `month()`,
  `to_row()` and `is_refund()`), `RECORD_COLUMNS`, `sort_key`,
  `LedgerParseError`.
- `ledgerkit/core/fields.py`: `split_record` and `join_record`, both
  quote-aware.
- `ledgerkit/core/normalize.py`: `normalize()`. **Don't use it for ingest**
  (trap 2).
- `ledgerkit/parsers/__init__.py`: `detect_system`, `read_rows`,
  `count_data_lines`, `SYSTEMS`.
- `ledgerkit/parsers/system_a.py`, `system_b.py`, `system_c.py`: the readers
  (raw strings keyed by each system's own column names), `COLUMNS`, `BANNER`
  or `HEADER_PREFIX`, and `system_b.to_major_units`.
- `ledgerkit/legacy_parser.py` and `ledgerkit/utils/cache.py`: **off-limits**.
- `tests/test_cli.py` runs the CLI as a subprocess with `PYTHONPATH=REPO`;
  follow that pattern for new CLI tests.
- `tests/test_parsers.py` contains the reader smoke tests.
