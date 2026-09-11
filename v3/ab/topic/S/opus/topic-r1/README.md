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
python -m ledgerkit report --by month
python -m ledgerkit reconcile --tolerance 0.05
python -m ledgerkit --config /tmp/quarter-close.toml report --by account
```

`report` separates its columns with semicolons and counts refunds in every
total. `--include-refunds` is still accepted, so existing scripts keep working,
but it no longer changes anything.

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
  ingest.py           exports to one ordered list of records
  report.py           totals by account or by month
  reconcile.py        account/month totals the systems disagree on
  validate.py         row by row checks of export files
  legacy_parser.py    the field splitter from the previous importer
  core/               format independent pieces
    fields.py         delimiter aware field splitting
    normalize.py      cleaning and ordering
    recordfile.py     reading and writing the normalized records file
    records.py        the Record type
    values.py         strict date and amount parsing
  parsers/            one reader, and its conversion to records, per format
    system_a.py       Ardent
    system_b.py       Borough (amounts in cents)
    system_c.py       Calder (dates day first)
  utils/
    cache.py          an on disk read cache
config/settings.toml  checked in settings
docs/CONVENTIONS.md   house rules; read this first
samples/              one small export from each system
tests/                tests for what is implemented
SPEC.md               the five commands that are not implemented yet
```

## Status

`version`, `inspect`, `ingest`, `report`, `reconcile`, `validate` and the global
`--config` option all work. `SPEC.md` describes the last five, except for the
two `report` changes noted above under "Running it".
