# Handover: implementing SPEC.md

Nothing in `SPEC.md`'s five commands has been written yet — this session was
read-only (repo exploration + two spec corrections from the user, also not
yet applied to `SPEC.md`'s text). Read `docs/CONVENTIONS.md` and `SPEC.md`
before starting; this file is supplementary, not a replacement.

## Open question — resolve before writing `report`

The user gave two corrections to `report` verbally; **`SPEC.md` itself
still has the old wording for both** and has not been edited.

1. **Field separator**: `report`'s output columns are semicolon-separated
   now, not comma-separated. Affects the header line and every data line
   for both `--by account` and `--by month` (SPEC.md's current examples at
   lines ~67 and ~75, and the rule at line ~80, still say comma). Does not
   affect `ingest`'s CSV output — that stays comma-separated per the spec's
   explicit header line.

2. **Refunds default**: refunds (negative-amount postings) should be
   **included** in `report` totals by default now, not excluded.
   **Unresolved**: `--include-refunds` is on the fixed flag-name list, and
   house rules say flag names must stay exactly as `SPEC.md` states — but a
   flag named `--include-refunds` makes no sense once refunds are included
   by default. Asked the user what the flag should do now (no-op that's
   still accepted, or flipped to mean "exclude refunds" despite the name);
   **no answer was given before the session ended**. Get this resolved
   before touching `report`'s argument parsing.

Everything else below reflects `SPEC.md` as written, unchanged.

## House rules (docs/CONVENTIONS.md) — the ones most likely to trip up this work

- No `print` anywhere except `ledgerkit.cli.emit`. Library code returns
  values.
- Every new public function (name doesn't start with `_`) needs full type
  annotations on every parameter and the return type. Checked in review.
- Log through `ledgerkit.log.get_logger(__name__)`. Never
  `logging.getLogger`/`basicConfig`/module-level `logging.warning`.
- Don't edit or add anything under `config/`.
- Don't import `ledgerkit.utils.cache`. File reads go straight through
  `Path.read_text` / the reader modules, not the disk cache.
- Don't use `ledgerkit.legacy_parser`. It's unmaintained and its quote
  handling is wrong (doesn't handle escaped `""` or delimiters inside a
  quoted field) — use `ledgerkit.core.fields.split_record`/`join_record`
  instead, which does.
- Amounts are `decimal.Decimal` from read to display, never `float`.
- Report totals round half to even, at the point of display only (round
  once; don't round individual postings before summing).
  `Settings.format_amount` (ledgerkit/config.py) already implements this
  correctly — verified against the CONVENTIONS.md table (2.50→2, 3.50→4,
  1240.50→1240, 883.50→884). Reuse it for `report`; don't reimplement
  rounding. Note `reconcile`'s per-line amounts are always fixed at 2
  decimals regardless of the `[report] decimals` setting, so that command
  needs its own `.2f`-style formatting, not `format_amount`.
- `--config PATH` has to work by setting the `LEDGERKIT_CONFIG` env var
  before calling `load_settings()` — `load_settings()` deliberately takes
  no arguments, per its own docstring in `ledgerkit/config.py`. There's no
  other entry point for it.
- Flag names are fixed: `--out`, `--by`, `--records`, `--include-refunds`,
  `--tolerance`, `--config` (see open question above on the last of these
  four's semantics changing).

## The three export formats

| | A (Ardent) | B (Borough) | C (Calder) |
|---|---|---|---|
| Shape | `#`-comment preamble, header, rows | header, rows | banner, header, rows, `== N rows ==` trailer |
| id column | `entry_id` | `doc_no` | `ref` |
| date column | `posted_on`, ISO `YYYY-MM-DD` | `value_date`, ISO `YYYY-MM-DD` | `txn_date`, **day-first** `DD/MM/YYYY` |
| account column | `account` | `acct` | `ledger_acct` |
| description column | `memo`, may be quoted, may contain the delimiter | `descr`, never quoted | `narrative`, never quoted |
| amount column | `amount`, plain decimal dollars | `amount`, **integer minor units (cents), no decimal point** | `gross_amount`, plain decimal dollars |

Readers (`ledgerkit/parsers/system_{a,b,c}.py`) hand back raw strings keyed
by each system's own column names — they don't interpret dates or amounts.
That conversion is new code the caller (whatever builds `Record`s for
`ingest`/`validate`) has to write, per-system:

- **Amount**: A and C are already `Decimal` dollars — just parse. B is
  cents-as-integer and *must* go through `system_b.to_major_units()`
  (`Decimal(cents) / 100`); the code comments note two prior importers
  mistakenly treated the raw B column as dollars.
- **Date**: A and B are both ISO, straightforward. C is day-first
  (`DD/MM/YYYY`); parsing it month-first throws for anything past the 12th
  and *silently* lands in the wrong month for anything on/before the 12th —
  no error, so this one is easy to ship broken.

## Known bugs / gaps found while reading the code

- **`system_a.read_rows` cannot read the shipped sample file today.** It
  raises `LedgerParseError` on any `"` in a line, but
  `samples/system_a_export.csv` row 1 (`A-10001`) has a quoted memo — I
  confirmed this fails by running it. `ledgerkit/core/fields.py` already
  has a correct quote-aware splitter (`split_record`, doctested) that just
  isn't wired into `system_a.py` yet, which still does naive
  `line.split(",")`. Fixing this (switch to `fields.split_record`) is a
  prerequisite for `ingest` to actually process the sample data, and for
  `validate` to count fields correctly on quoted A rows. The existing test
  `test_system_a_reads_an_export_without_quoted_memos` only covers the
  *unquoted* case, so it won't be broken by this fix.
- **`core.normalize.normalize()` defaults to `keep_refunds=False`**, i.e.
  it silently drops negative-amount rows unless you pass
  `keep_refunds=True`. `ingest` must pass `keep_refunds=True` explicitly —
  SPEC.md's "every posting in the input files appears in the output,
  nothing filtered" requirement is otherwise violated by the default.
- **`normalize()`'s `_clean()` collapses internal whitespace runs** in
  `description` (`" ".join(text.split())`). Worth a deliberate call on
  whether that's compatible with SPEC.md's "description ... preserved
  exactly" wording (that wording is focused on delimiter/quote characters,
  but the whitespace collapsing is a real transformation to be aware of).
- **`mapping.ACCOUNT_NAMES` has a duplicate `"5200"` key.** The dict's
  actual runtime value is `"Contract Labor"` (the later literal wins); the
  module's own docstring table still shows `"Warehouse Labor"` for 5200 and
  was never updated. Trust the dict, not the docstring comment.
- Account code `8800` appears in both the A and C samples and is **not**
  in `ACCOUNT_NAMES` — a real, ready-made exercise of the
  `unknown_account_label` path (default `"UNCLASSIFIED"`).
- **`validate` can't just call the existing `read_rows()` functions** —
  those raise and stop at the first malformed row (wrong field count,
  wrong `sys` column, missing banner, etc.), but SPEC.md requires checking
  every row and warning once per bad one, not stopping early. `validate`
  needs its own per-line/per-row loop (reusing `fields.split_record` for
  system A) that collects a warning and keeps going instead of raising.
- Once `ingest` has written `account_name` into the normalized CSV,
  `report` and `reconcile` never need `ledgerkit/mapping.py` again — they
  just read that column back out of the normalized file. They also don't
  need the raw exports or the parsers at all; they only read
  `--records PATH`.

## Settings (`config/settings.toml`, layered by `ledgerkit/config.py`)

Defaults in force unless overridden: `report.decimals = 0`,
`report.unknown_account_label = "UNCLASSIFIED"`,
`reconcile.tolerance = 0.05`, `validate.account_code_pattern = "^[0-9]{4}$"`.
`Settings.format_amount(value)` renders at `decimals` places using Decimal's
default context rounding, which is `ROUND_HALF_EVEN` — confirmed by running
it against all four rows of the CONVENTIONS.md rounding table.

## Samples

`samples/system_{a,b,c}_export.csv` — 42 rows (A), 39 rows (B), 39 rows (C).
Account codes used include `8800` (unmapped, in A and C only) and the
duplicate-key `5200`. A's sample has at least one quoted, delimiter-bearing
memo (row 1) — see the read bug above.
