# ledgerkit SPEC.md recon — pre-implementation

## Context
Repo `ledgerkit` (Python 3.12, stdlib only) merges/reports on ledger exports from three
legacy systems (A/Ardent, B/Borough, C/Calder). `version` and `inspect` are implemented;
`SPEC.md` specifies five more pieces of CLI surface (`ingest`, `report`, `reconcile`,
`validate`, `--config`) that are not written yet. This session was pure reconnaissance —
read SPEC.md, docs/CONVENTIONS.md, the whole package, and the three sample exports — no
code was written. Full write-up was given to the user in conversation; this file is the
distillate for a future session that picks up implementation.

## Outcome
No code changes made. Produced a complete map of the format differences and the specific
traps in the existing code that implementation must route around. User then gave two verbal
amendments to SPEC.md for the `report` command (SPEC.md text itself was NOT edited) and the
session ended on an open question before implementation started.

## Lessons

**Format differences (verified by reading samples + parser source):**
- Dates: A and B are ISO `YYYY-MM-DD`. **C is day-first `dd/mm/yyyy`** — the one that needs
  a non-default `strptime` and silently misdates the 1st–12th of a month if read month-first.
- Amounts: A and C are decimal dollars, 2 places, direct to `Decimal`. **B is integer minor
  units (cents), no decimal point** — must go through `system_b.to_major_units` (÷100) or
  every Borough total comes out 100x too large with no error raised.

**Traps in existing code an implementer must route around:**
- `system_a.read_rows` currently **raises `LedgerParseError` on any line containing a quote**
  instead of parsing quoted memos (the sample file has one: `A-10001`). Its own error message
  points at `legacy_parser.py`, which is explicitly forbidden to use. Correct fix: use
  `ledgerkit.core.fields.split_record` (already exists, already used by `system_a.read_header`).
- `system_c.read_rows` also does a raw `line.split(",")` on `narrative` with no quote
  handling — same fix applies, nothing guarantees Calder narratives are comma-free.
- `mapping.ACCOUNT_NAMES` defines `"5200"` twice; the second entry (`"Contract Labor"`) wins.
  The docstring table above it is stale and still shows `Warehouse Labor` — **the dict is
  ground truth, not the docstring**.
- `core/normalize.normalize()` drops refund rows (negative amount) unless called with
  `keep_refunds=True`. `ingest` must pass `keep_refunds=True` since SPEC requires every
  posting to appear in output, nothing filtered.
- `config.load_settings()` takes zero arguments by design, only reads `LEDGERKIT_CONFIG` env
  var. The `--config PATH` global flag must be implemented by setting that env var (or
  equivalent single-mechanism routing) before any handler calls `load_settings()`, and must
  be a top-level argparse arg (given *before* the subcommand per SPEC), not per-subparser.
- Existing readers (`read_rows`) raise and **stop at the first malformed row**. SPEC's
  `validate` must check every row and continue past bad ones — cannot call `read_rows()`
  directly, needs its own row-by-row loop reusing `detect_system`/header readers.
- `reconcile`: a system absent from an account/month combo renders as `-` and must be
  **excluded from the spread calculation**, not treated as $0.00.
- House rules confirmed present and consistent in `docs/CONVENTIONS.md`: `Decimal` only for
  money, `ROUND_HALF_EVEN` rounding done once at display time, `ledgerkit.log.get_logger`
  per module, only `cli.emit` prints, `config/` untouched, full type annotations on every
  public function/method, stdlib only, exact flag names
  (`--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`).
- Do not import `ledgerkit.utils.cache` (forbidden) or `ledgerkit.legacy_parser` (forbidden,
  unmaintained, not imported anywhere in the current tree).

**Verbal SPEC amendments from user (2026-09-11), SPEC.md text itself unchanged:**
1. `report`'s output columns are separated by `;` (semicolon), not `,`. Applies only to
   `report`'s printed lines — `ingest`'s CSV output is unaffected and stays comma-delimited.
2. `report` totals include refunds **by default now** (previously SPEC.md said refunds were
   excluded unless `--include-refunds` was passed).

## Next steps
- **Open question, unanswered as of session end**: since refunds are now included by
  default, what should the (still-required, per the fixed flag-name list) `--include-refunds`
  flag do? Offered two options to the user, awaiting a decision before writing `report`:
  - (a) keep flag accepted but as a no-op (safe for existing ops scripts that already pass it)
  - (b) repurpose the flag to mean *exclude* refunds when passed (flips its name's meaning)
- Once that's answered: implement `ingest`, `report`, `reconcile`, `validate`, `--config` per
  SPEC.md plus the two verbal amendments above, applying all the trap-avoidance items listed
  under Lessons.
- Fix `system_a.py` (and probably `system_c.py`) to use `core.fields.split_record` before
  `ingest` can pass on the sample data as-is (the quoted-memo row will otherwise hard-fail).
