# ledgerkit

A command line tool that takes the ledger exports three legacy systems drop into
a directory and turns them into one set of records you can report on.

The three systems are called A (Ardent), B (Borough) and C (Calder) throughout.
Each writes its own file format, and none of them agree about very much.

## Running it

Nothing to install. Python 3.12 and the standard library.

```
python -m ledgerkit version
python -m ledgerkit inspect samples/system_a_export.csv
python -m ledgerkit inspect samples/*.csv
python -m ledgerkit ingest samples/*.csv --out out/records.csv
python -m ledgerkit report --by account
python -m ledgerkit reconcile --tolerance 0.10
python -m ledgerkit validate samples/*.csv
python -m ledgerkit --config /tmp/quarter-close.toml report --by month
```

## Tests

```
python -m pytest tests/
```

The tests use plain `pytest` with no plugins, and cover the behaviour that is
already implemented.

## What is here

```
ledgerkit/            the package
  cli.py              the command line
  config.py           settings loading
  log.py              the project logger
  mapping.py          account code to account name
  legacy_parser.py    the field splitter from the previous importer
  report.py           totals for `report`
  reconcile.py        cross-system comparison for `reconcile`
  validate.py         row checks for `validate`
  core/               format independent pieces
    fields.py         delimiter aware field splitting
    normalize.py      cleaning and ordering
    records.py        the Record type
    store.py          the normalized records file
    values.py         reading one date or amount field
  parsers/            one reader per export format
    system_a.py       Ardent
    system_b.py       Borough
    system_c.py       Calder
  utils/
    cache.py          an on disk read cache
config/settings.toml  checked in settings
docs/CONVENTIONS.md   house rules; read this first
samples/              one small export from each system
tests/                tests for what is implemented
SPEC.md               what ingest, report, reconcile, validate and --config do
```

## Status

`version`, `inspect`, `ingest`, `report`, `reconcile`, `validate` and the global
`--config` option all work as described in `SPEC.md`.
