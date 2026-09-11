# ledgerkit: SPEC.md commands implemented

## Context
ledgerkit (Python 3.12, stdlib only) merges ledger exports from three systems into
one normalized CSV and reports on it. SPEC.md asked for `ingest`, `report`,
`reconcile`, `validate` and a global `--config`. House rules (docs/CONVENTIONS.md
plus the user): no `print` outside `ledgerkit.cli.emit`; full type annotations on
every public function; log only via `ledgerkit.log.get_logger`; `Decimal` money,
never float; no edits or new files under `config/`; no new dependencies; never
import `utils.cache` or `legacy_parser`; flag names exactly as SPEC states
(`--out --by --records --include-refunds --tolerance --config`).

How the exports differ (verified against the samples):
| | date | amount |
|---|---|---|
| A (Ardent) | ISO | dollars; memo may be quoted with `,` and `""` inside |
| B (Borough) | ISO | **whole cents** (`25440` = 254.40) |
| C (Calder) | **dd/mm/yyyy** | dollars |

User changes made after the first SPEC draft (2026-09-11), now written into SPEC.md:
`report` separates fields with `;`, and refunds are always counted in `report` totals.

## Outcome
Done and verified: 27 tests pass (6 original + 21 new in `tests/test_commands.py`),
and the CLI was run end to end against `samples/`.
- System A reader now splits lines with `core.fields.split_record`, so quoted memos work.
- Each `parsers/system_{a,b,c}.py` owns `numbered_lines`, the column constants,
  `parse_date` and `parse_amount`. `parsers.read_records()` builds `Record`s.
- New modules: `core/values.py`, `core/store.py` (normalized CSV),
  `report.py` (half-even rounding at display, `;`), `reconcile.py`, `validate.py`.
- `--config PATH` sets `LEDGERKIT_CONFIG` for the run; `load_settings()` is unchanged.
- Sample results: ingest writes 120 rows; report by account shows 4100 as `6248`
  (6248.50, half even); reconcile finds 5 mismatches; validate reports
  `checked=120 rejected=0`.
- SPEC.md and README.md are updated; `config/settings.toml` is untouched.

## Lessons
- Contradicted: the System A error message said to use `legacy_parser.py` for quoted
  fields. It splits the sample's quoted memo into 8 fields instead of 6.
- Contradicted: the table in the `mapping.py` docstring says 5200 is "Warehouse Labor".
  The code maps it to "Contract Labor", a later duplicate dict key that wins on purpose.
- `core.normalize.normalize()` drops refunds by default and collapses whitespace in
  descriptions. Both break ingest ("every posting", "description exactly"), so it isn't used.
- `Decimal` f-string formatting follows the context's rounding, so round with
  `quantize(..., ROUND_HALF_EVEN)` explicitly.
- `utils/cache.py` keys entries by path only (stale data) and writes into the
  working directory. It's off-limits anyway.

## Next steps
Open questions for the user:
1. `--include-refunds` is now an accepted no-op. Do they want a way to leave refunds
   out of `report`? That would need a new flag name from them.
2. A missing `--config` file exits 2 instead of quietly falling back to defaults. Confirm.
3. `validate` rejects a Borough amount with a decimal point, because Borough writes
   whole cents. Confirm.
No git repository, so nothing was committed.
