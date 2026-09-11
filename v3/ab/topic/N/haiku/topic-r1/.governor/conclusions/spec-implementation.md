---
type: generic
context: Preparing to implement five new ledgerkit commands
---

## Context

Ledgerkit merges exports from three legacy accounting systems (A/Ardent, B/Borough, C/Calder) into normalized records. Each system has its own file format and conventions. Five commands remain unimplemented: `ingest`, `report`, `reconcile`, `validate`, and `--config`. The warehouse team depends on these commands.

## Outcome: Critical Implementation Details

**System-specific conversions (non-negotiable):**
- **System B amounts**: Stored as integer cents (e.g., 25440 = $254.40). Must divide by 100 when building Records.
- **System C dates**: Written DD/MM/YYYY (day-first), not MM/DD/YYYY. Misreading silently corrupts rows ≤12th of month.
- **System A amounts & dates**: ISO dates and decimal dollars; no conversion needed.

**The five commands:**
1. `ingest FILE [FILE ...]` — Merge any combination of exports into normalized CSV (sorted: date, system, record_id).
2. `report --by account|month` — Print totals grouped by account code or month, **semicolon-separated** (not comma). Refunds **included by default** (changed from spec).
3. `reconcile [--tolerance N]` — Report account/month pairs where systems disagree; show spread and per-system totals.
4. `validate FILE [FILE ...]` — Check for malformed rows (field count, date format per-system, amount numeric, account code matches regex). Exit 0 if all pass, 2 if any rejected.
5. `--config PATH` — Global flag (before subcommand) overrides settings file; layering is: defaults → config/settings.toml → override file.

**Type system & rounding:**
- Amounts in-memory: `decimal.Decimal` only (never float). Borough conversion happens at Record construction.
- Dates in-memory: `datetime.date`.
- Rounding: `Decimal.quantize(..., rounding=ROUND_HALF_EVEN)` at output time only. Do not round intermediate values.
- Account names: Look up code in `mapping.ACCOUNT_NAMES`; unknown codes use `settings.unknown_account_label`.

**Logging & output:**
- All messages: Use logger via `from ledgerkit.log import get_logger; _log = get_logger(__name__)`. No direct `print()` except in `cli.emit()`.
- Public functions: Full type annotations on all parameters and return type (checked in review).
- No dependencies beyond standard library.

**Readers return raw strings:** Each system's reader (`system_a.read_rows()`, etc.) returns `list[dict[str, str]]` keyed by source column names (e.g., Ardent uses "entry_id", Borough uses "doc_no"). Conversion to Record happens at caller, which knows the system.

## Lessons

- Borough's cents-as-amount is a classic foot-gun; the docstring warns importers have been caught treating cents as dollars and getting 100x overages.
- Calder's DD/MM/YYYY silently corrupts rows on dates ≤12th if parsed as MM/DD (day lands in wrong month, no error).
- Changes to spec after writing (report delimiter, refund default) are corrections to what the warehouse team actually needs; implement these, not the old wording.

## Next steps

Implement in order: (1) Readers that convert to Records, (2) `ingest`, (3) `report`, (4) `reconcile`, (5) `validate`. Add `--config` flag to all commands. Wire up in CLI.
