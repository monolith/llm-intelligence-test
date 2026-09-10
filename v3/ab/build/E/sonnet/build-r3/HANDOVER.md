# Handover — implementing SPEC.md's five commands

Nothing in `ledgerkit/` has been changed yet. This is everything gathered from
reading the repo and from verbal amendments the user gave, before writing any
of `ingest`, `report`, `reconcile`, `validate`, or `--config`.

## Spec amendments (override the written SPEC.md text)

Given verbally on 2026-09-10, twice, consistently:

1. **`report`'s printed lines are semicolon separated, not comma separated.**
   SPEC.md still shows commas (`account_code,account_name,total` etc.) — that
   wording is stale. This is scoped to `report`'s own output lines only:
   - `ingest`'s normalized CSV keeps the exact comma-separated header SPEC.md
     specifies (`record_id,source_system,date,account_code,account_name,description,amount`).
   - `reconcile`'s space-separated `MISMATCH ...` lines are unaffected.
2. **Refunds are included in `report` totals by default now.** SPEC.md's
   wording ("Without it, refunds are left out of the totals") is stale. This
   brings `report` in line with `reconcile`, which already includes refunds
   unconditionally per SPEC.md §3.
   - **Open question, unresolved:** what does `--include-refunds` do now that
     refunds are already included by default? Never got an answer. Default
     assumption going in was: no-op. Ask before finalizing this flag's
     behavior — do not just silently decide.
   - The flag name itself is not in question: it must stay `--include-refunds`
     regardless of what it ends up doing, per the "Flag names" section of
     SPEC.md and the house rule that CLI flag names are fixed.

Nothing else in SPEC.md has been amended. Everything else below is drawn from
reading the code, not from the user.

## House rules (from the task prompt, apply to all new code)

- No `print` in library code — `ledgerkit.cli.emit` is the only function
  allowed to print. Library code returns values.
- Every new public function (name doesn't start with `_`) has type
  annotations on every parameter and on its return.
- Do not edit anything under `config/` (i.e. `config/settings.toml` itself —
  see the `--config` note below for why this doesn't block implementing the
  `--config` flag).
- Log through `ledgerkit.log.get_logger(__name__)`, never `logging.getLogger`
  / `logging.basicConfig` / module-level `logging.warning`.
- No new dependencies — standard library only.
- Do not import `ledgerkit.utils.cache`.
- Do not use `ledgerkit.legacy_parser`.
- Keep CLI flag names exactly as SPEC.md states: `--out`, `--by`, `--records`,
  `--include-refunds`, `--tolerance`, `--config`.

## What's already implemented and reusable

- `ledgerkit/core/fields.py` — `split_record`/`join_record`, a hand-rolled
  quote-aware CSV splitter/joiner (handles doubled `""` quoting). Use this,
  not `csv` module wrangling, for anything quote-sensitive.
- `ledgerkit/core/records.py` — `Record` dataclass (frozen), `RECORD_COLUMNS`,
  `sort_key` (date, then source_system, then record_id — this is the required
  `ingest` output order), `Record.to_row()`, `Record.month()`,
  `Record.is_refund()`, and `LedgerParseError`.
- `ledgerkit/core/normalize.py` — `normalize(records, *, keep_refunds=False)`
  strips/uppercases fields, collapses whitespace in descriptions, sorts by
  `sort_key`, and **drops refunds by default**. That default exists for an
  older reporting flow and is wrong for `ingest`: SPEC.md requires every
  posting to appear in `ingest`'s output, so `ingest` must call this with
  `keep_refunds=True`.
- `ledgerkit/config.py` — `load_settings()` (no arguments — see `--config`
  note below), `Settings` dataclass with `.format_amount(value)`. Verified
  by hand that `Settings.format_amount` already does the correct
  round-half-to-even rounding CONVENTIONS.md requires (Python's
  `Decimal.__format__` defaults to `ROUND_HALF_EVEN`): `2.50→2`, `3.50→4`,
  `1240.50→1240`, `883.50→884` all check out. Sum raw, unrounded `Decimal`s
  per group and call `format_amount` once at display time — don't round the
  postings themselves.
- `ledgerkit/mapping.py` — `account_name(code, unknown_label)`, `is_known`.
  Only covers a fixed set of codes (4100–9000 range); anything else (e.g.
  `8800`, present in both the A and C sample files) must render as the
  `unknown_account_label` setting, not be dropped or error.
- `ledgerkit/parsers/*` — `read_rows(path)` per system, returning raw string
  dicts keyed by that system's own column names. `parsers/__init__.py` has
  `detect_system`, `read_rows` (dispatches by sniffing), `count_data_lines`.

## The three export formats — what has to be converted, what doesn't

| | A (Ardent) | B (Borough) | C (Calder) |
|---|---|---|---|
| Framing | `#`-comment preamble, then header | header row only | banner line, header, trailer `== N rows ==` |
| Quoting | memo may be quoted, `""` escaping | never quoted | never quoted |
| Date as written | `YYYY-MM-DD` | `YYYY-MM-DD` | `dd/mm/yyyy` (**day first**) |
| Amount as written | decimal dollars, `-` for refund | **integer cents, no decimal point** | decimal dollars |

- Only B's amount needs unit conversion (÷100) — `system_b.to_major_units`
  already does this correctly. A and C are already dollars.
- Only C's date needs a different parser (day-first) — reading it month-first
  silently produces a wrong-but-valid date for day ≤ 12 and only throws for
  day > 12. A and B are already ISO.
- Calder's trailer row-count mismatch is logged as a `WARNING`, not treated as
  an error (see `system_c.read_rows`) — don't reject a file over it.

## A real bug that will break `ingest` on the shipped sample data

`system_a.read_rows` currently **raises `LedgerParseError` on any data line
containing a `"`**, because quoted-memo support was deliberately stubbed out
years ago (see its docstring/comment). But `samples/system_a_export.csv`'s
very first data row *is* a quoted memo:
`A-10001,2026-01-03,4100,"Rebill, ""Q1 true-up"", carrier",239.55,USD`.

`core/fields.split_record` already parses this exact string correctly (it's
literally the module's doctest example). `ingest` will crash on the shipped
sample unless `system_a.read_rows` is changed to use
`fields.split_record(line)` instead of `line.split(",")`, and the
`LedgerParseError` raised on seeing a `"` is removed. This is not forbidden by
any house rule — it's not `legacy_parser`, no new dependency — and looks like
the actual intended fix rather than a design choice to preserve.

Existing test `tests/test_parsers.py::test_system_a_reads_an_export_without_quoted_memos`
only exercises unquoted lines, so it won't catch a regression here either way
— write a new test with a quoted line once this is fixed.

## `validate` needs a different reading strategy than the existing readers

SPEC.md requires `validate` to check every row and **not stop at the first bad
one**, logging a `WARNING` per rejected row. But `system_a/b/c.read_rows` are
fail-fast: they raise `LedgerParseError` and abort on the first malformed
line. Calling `read_rows` directly won't satisfy "checks all of them" for
files with more than one bad row. `validate` will need its own lenient,
line-by-line pass per system (field-count check against each system's known
`COLUMNS`, per-system date parse, amount parse, and the
`[validate] account_code_pattern` regex from settings) that continues past a
bad row instead of raising.

## `--config PATH` vs. `load_settings()`'s no-argument contract

SPEC.md wants a global `--config PATH` flag that "works with every
subcommand." But `ledgerkit/config.py` and `docs/CONVENTIONS.md` are explicit
that `load_settings()` takes zero arguments and only ever reads
`LEDGERKIT_CONFIG` from the environment ("there is exactly one place a caller
can say where settings come from, and it is the environment").

Reconciliation: when `--config PATH` is passed, the CLI should set
`os.environ["LEDGERKIT_CONFIG"] = PATH` before dispatching to the subcommand
handler, rather than changing `load_settings()`'s signature. This satisfies
"works with every subcommand" without touching `config/` — the "don't edit
`config/`" rule is about the checked-in `config/settings.toml` directory, not
about `ledgerkit/config.py`.

Argparse-wise, add `--config` to the top-level parser (before
`add_subparsers()`), matching the usage shown in SPEC.md
(`--config PATH COMMAND ...`, i.e. the global flag precedes the subcommand).

## `reconcile` notes

- Group every posting by `(account_code, month, source_system)`, total each
  group. Only consider account/month combinations where **at least two**
  systems posted.
- Spread = max system total − min system total for that combination.
- Report combinations whose spread exceeds `--tolerance` (default from
  `[reconcile] tolerance` setting, currently `0.05` in
  `config/settings.toml`), ordered by account code then month.
- A system with no postings in a combination prints as a literal `-`, not
  `0.00`.
- All postings count, refunds included unconditionally — SPEC.md is correct
  here and unaffected by the `report` amendments above.

## Reference material already read this session

- `SPEC.md` — the five commands' full behavioral spec (see amendments above).
- `README.md`, `docs/CONVENTIONS.md` — house rules on money (`Decimal`
  everywhere), rounding (half-to-even), dates, logging, program output,
  configuration, type annotations, dependencies, and reader responsibilities.
- `samples/system_{a,b,c}_export.csv` — one real export per system; use these
  for manual sanity checks once `ingest` exists (39 data rows each in B/C, 42
  lines in A per `tests/test_cli.py`'s `data_lines=42` assertion, which
  includes the header and preamble in that line count).
- `tests/test_cli.py`, `tests/test_parsers.py` — existing smoke tests; neither
  covers the five new commands yet.
