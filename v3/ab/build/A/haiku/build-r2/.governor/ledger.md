## Goal
Implement the five features in SPEC.md correctly, respecting the conventions in docs/CONVENTIONS.md.

## Decisions
- Created ledgerkit/core/convert.py with system-specific row-to-Record converters for A, B, C
- Enhanced system_a parser to handle quoted fields using fields.split_record
- All five commands implemented as subparsers in cli.py
- --config option as global argument applied before subcommand dispatch
- CSV I/O for records uses standard library csv module with proper newline="" handling

## Ruled out
- Dependencies beyond standard library
- Changes to version/inspect commands
- Any modifications to config/ directory

## Notes
All five features complete and tested:
1. ingest - merges exports into normalized CSV (120 rows from samples)
2. report - totals by account or month with --include-refunds option
3. reconcile - finds system disagreements with --tolerance parameter
4. validate - checks export files, rejects invalid rows, returns exit code 2 on errors
5. --config - global option for custom settings path via LEDGERKIT_CONFIG

All CONVENTIONS followed: Decimal for money, ROUND_HALF_EVEN for rounding, logging via get_logger, output via emit, type annotations on all public functions.
