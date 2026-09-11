# Ledgerkit Spec Setup and Clarifications

## Context
Implementing five new features for ledgerkit (a CLI tool that merges exports from three legacy accounting systems and produces normalized records and reports). Read SPEC.md, CONVENTIONS.md, codebase, and three systems' export formats.

## Outcome
Codebase fully understood. Two critical spec amendments received before implementation started:
1. **Report output format**: Columns separated by semicolons, not commas
2. **Refund handling in report**: Include by default (was: exclude by default)

## Key Implementation Requirements

**Amounts and dates need conversion:**
- **System A (Ardent)**: Decimal dollars; ISO YYYY-MM-DD — no conversion needed
- **System B (Borough)**: Integer cents (divide by 100 to get dollars); ISO YYYY-MM-DD — convert cents → dollars
- **System C (Calder)**: Decimal dollars; **DD/MM/YYYY format** — parse day-first, not month-first

**Report output:**
- Account mode: `account_code;account_name;total` (semicolon-separated)
- Month mode: `month;total` (semicolon-separated)
- All postings included (refunds count toward totals)

**House rules enforced:**
- All amounts are `Decimal` (never float)
- Rounding is half-to-even via `Decimal.quantize()` default
- Full type annotations on all public functions
- No print in library code (use `cli.emit()` only)
- Log through `ledgerkit.log.get_logger()`
- Flag names are fixed: `--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`

## Open Question
Status of `--include-refunds` flag: keep as no-op in parser, or remove entirely? (Asked but not yet answered.)

## Next Steps
1. Clarify flag handling for `--include-refunds`
2. Implement in order: `ingest` (core), `validate`, `report`, `reconcile`, `--config`
