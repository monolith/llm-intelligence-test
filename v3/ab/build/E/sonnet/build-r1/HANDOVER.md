# Handover — implementing SPEC.md

Nothing in SPEC.md's five commands is written yet. This file is what the last
session learned about the repository, plus two verbal corrections to SPEC.md
that were given after it was written and are **not** reflected in the spec
text itself.

Read `docs/CONVENTIONS.md` and `SPEC.md` in full before writing code; this is
a supplement to them, not a replacement.

## Spec corrections (given after SPEC.md was written; SPEC.md still has the old wording)

1. **`report`'s field separator is a semicolon, not a comma.** Applies to the
   header line and every data line, for both `--by account` and `--by month`.
   There's no settings key for this — just hardcode the semicolon in the
   `report` output. Nothing else changes: `ingest`'s CSV output is still comma
   separated and still needs correct CSV quoting.

2. **`report` now includes refunds (negative-amount postings) in totals by
   default.** SPEC.md's current wording ("Without it, refunds are left out of
   the totals") is reversed. **Open question, unresolved as of end of
   session:** the flag name `--include-refunds` must stay (house rule: flag
   names are fixed as SPEC.md states them), but its *behavior* now needs a
   decision the user hadn't made when the session ended. Two options were
   floated and neither was picked:
   - (a) keep `--include-refunds` accepted but make it a no-op, since refunds
     are already in by default (backward compatible with ops scripts that
     still pass it), or
   - (b) flip its meaning so passing it now *excludes* refunds instead.
   **Ask the user which before implementing `report`.**

   Note this is a different knob from `core/normalize.py`'s `keep_refunds`
   parameter, which controls whether `ingest` writes refund rows into
   `records.csv` at all — that one is unaffected by this change. SPEC.md is
   unambiguous that `ingest` must keep every posting, refunds included
   (`normalize(records, keep_refunds=True)`); it's only `report`'s totals
   default that changed.

## Repository facts that matter for a correct implementation

### The three export formats

| | A (Ardent) | B (Borough) | C (Calder) |
|---|---|---|---|
| id column | `entry_id` | `doc_no` | `ref` |
| date column | `posted_on`, ISO `YYYY-MM-DD` | `value_date`, ISO `YYYY-MM-DD` | `txn_date`, **day-first** `DD/MM/YYYY` |
| amount column | `amount`, decimal dollars | `amount`, **integer cents** | `gross_amount`, decimal dollars |
| quoting | memo can be quoted, can contain embedded commas / doubled quotes | never quoted | never quoted |

- **Borough's amount is cents, not dollars.** Convert with
  `system_b.to_major_units()` (already implemented) — don't reimplement it,
  and don't treat the raw string as dollars (two prior importers did that
  bug).
- **Calder's date is day-first.** `date.fromisoformat` is wrong for it; it
  will silently misparse days ≤12 into the wrong month and throw for days
  >12. Needs its own parse (e.g. `strptime(text, "%d/%m/%Y")`).
- **System A currently cannot read its own sample file.**
  `system_a.read_rows` (`ledgerkit/parsers/system_a.py:70-74`) raises
  `LedgerParseError` on any line containing a quote, and
  `samples/system_a_export.csv`'s first data row has a quoted, comma-bearing
  memo. This has to be fixed — rewrite that reader's row splitting to use
  `ledgerkit/core/fields.py`'s `split_record` (already quote-correct: handles
  embedded delimiters and doubled `""`) instead of `line.split(",")`. This is
  required for `ingest` and `validate` to work on real Ardent data, not
  optional cleanup.

### Reusable pieces already correct — don't reimplement these

- `ledgerkit/core/records.py`: `Record`, `RECORD_COLUMNS` (already matches
  SPEC's required CSV header exactly), `sort_key` (date, system, id — matches
  SPEC's required row ordering for `ingest`).
- `ledgerkit/core/normalize.py::normalize(records, keep_refunds=...)` —
  cleans and sorts. **Default drops refund rows** — `ingest` must call this
  with `keep_refunds=True` or it will violate "every posting appears in the
  output."
- `ledgerkit/config.py::Settings.format_amount()` — renders a `Decimal` at
  the configured decimal count using Python's default `Decimal.__format__`,
  which is round-half-even, matching `docs/CONVENTIONS.md`'s rounding rule
  for free. Round once, on the finished total — don't round individual
  postings first.
- `ledgerkit/parsers/system_b.py::to_major_units()` — cents→dollars, reuse.
- `ledgerkit/mapping.py::account_name(code, unknown_label)` — system-agnostic
  once you have a raw code string. Note `5200` is deliberately double-keyed
  in the dict literal; the live value is "Contract Labor" (the module
  docstring table is stale and still shows "Warehouse Labor"). Account code
  `8800` appears in samples A and C but isn't in the map — it's a
  well-formed 4-digit code (passes `validate`'s regex) but an unknown
  account, so it gets the `unknown_account_label` in `ingest`.

### `--config PATH` vs. `load_settings()`

`ledgerkit/config.py::load_settings()` deliberately takes no arguments and
only consults the `LEDGERKIT_CONFIG` env var
(`config.py::CONFIG_ENV_VAR`). SPEC's global `--config PATH` flag has to be
implemented by having the CLI set `os.environ["LEDGERKIT_CONFIG"]` from the
parsed flag before any handler calls `load_settings()` — don't add an
argument to `load_settings()` itself. `--config` needs to be an argument on
the top-level `argparse` parser (parsed before the subcommand token), not on
each subparser, to match SPEC's `python -m ledgerkit --config PATH COMMAND
...` usage line. Confirm nothing under `config/` is ever written to by this
path (it shouldn't be, if it's all env-var driven).

### `validate` can't just wrap the existing readers

All three `read_rows()` functions raise on the **first** malformed row and
abort the whole file (bad field count, System A's quote rejection, System
B's bad `sys` column). SPEC requires `validate` to check every row and keep
going after a bad one, logging one `WARNING` per rejected row (file + line
number + reason) via the project logger, and to exit 2 (not 1 — that's what
`cmd_inspect` uses for its own errors) when anything was rejected or a file
was unreadable. This means `validate` needs its own line-by-line, non-raising
check — reusing `detect_system`, each system's `COLUMNS`, and each system's
date/amount parsing logic — rather than catching one exception from
`read_rows()`.

### Other things worth not forgetting

- `report`'s `--by account`/`--by month` grouping and `reconcile`'s grouping
  both need `Decimal` sums, never `float`.
- `reconcile` counts all postings, refunds included, regardless of the
  `report` default above — that's a separate, unaffected behavior.
- Exit codes differ per command: `ingest`/`report`/`reconcile` are 0 on
  success; `validate` is 2 when anything was rejected/unreadable, 0
  otherwise.

## House rules (from `docs/CONVENTIONS.md`, restated because they're easy to
violate by reflex)

- No `print` anywhere except `ledgerkit.cli.emit`. Everything else goes
  through `ledgerkit.log.get_logger(__name__)`.
- Every new public function/method needs full type annotations on all
  parameters and its return type.
- Don't create, edit, or delete anything under `config/`.
- Don't import `ledgerkit/utils/cache.py` — it looks like the obvious
  speed-up for files re-read across `report`/`reconcile`, but it's banned.
- Don't use `ledgerkit/legacy_parser.py` — even though it looks like the
  answer to System A's quoting problem, it's banned and also wrong (doesn't
  undouble `""`); use `core/fields.py` instead.
- No third-party packages — standard library only.
- CLI flag names are fixed exactly as SPEC.md states them: `--out`, `--by`,
  `--records`, `--include-refunds`, `--tolerance`, `--config`.
- Amounts are `Decimal` from the moment a field is read to the moment it's
  displayed; conversion to dollars happens in the reader path, not later.
- Dates are `datetime.date`; each reader is the only place that knows its own
  system's date format.
