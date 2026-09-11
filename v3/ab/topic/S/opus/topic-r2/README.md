# ledgerkit

A command line tool that takes the ledger exports three legacy systems drop into
a directory and turns them into one set of records you can report on.

The three systems are called A (Ardent), B (Borough) and C (Calder) throughout.
Each writes its own file format, and none of them agree about very much.

## Running it

Nothing to install. Python 3.12 and the standard library.

```
python -m ledgerkit version
python -m ledgerkit inspect samples/*.csv
python -m ledgerkit validate samples/*.csv
python -m ledgerkit ingest samples/*.csv --out out/records.csv
python -m ledgerkit report --by account
python -m ledgerkit report --by month --records out/records.csv
python -m ledgerkit reconcile --tolerance 0.10
python -m ledgerkit --config /tmp/quarter-close.toml report --by account
```

`report` separates its fields with semicolons and counts refunds in every total;
both changed after `SPEC.md` was written. `--include-refunds` is still accepted.

## Tests

```
python -m pytest tests/
```

The tests use plain `pytest` with no plugins.

## What is here

```
ledgerkit/            the package
  cli.py              the command line
  config.py           settings loading
  log.py              the project logger
  mapping.py          account code to account name
  formats.py          which column means what, per system
  ingest.py           exports to normalized records
  recordfile.py       writing and reading the normalized file
  report.py           totals by account or month
  reconcile.py        where the systems disagree
  validate.py         row by row checks of an export
  legacy_parser.py    the field splitter from the previous importer
  core/               format independent pieces
    fields.py         delimiter aware field splitting
    normalize.py      cleaning and ordering
    records.py        the Record type
    values.py         reading amounts and dates, rounding totals
  parsers/            one reader per export format
    system_a.py       Ardent
    system_b.py       Borough
    system_c.py       Calder
  utils/
    cache.py          an on disk read cache
config/settings.toml  checked in settings
docs/CONVENTIONS.md   house rules; read this first
samples/              one small export from each system
tests/                tests
SPEC.md               the specification for ingest, report, reconcile, validate and --config
```

## Status

All of `version`, `inspect`, `ingest`, `report`, `reconcile`, `validate` and the
global `--config` option work.
