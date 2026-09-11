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
  core/               format independent pieces
    fields.py         delimiter aware field splitting
    normalize.py      cleaning and ordering
    records.py        the Record type
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
SPEC.md               the five commands that are not implemented yet
```

## Status

`version`, `inspect`, `ingest`, `report`, `reconcile`, `validate` and the global
`--config PATH` option work as specified in `SPEC.md`, with two changes to
`report`: its fields are separated by semicolons, and refunds are always counted
(`--include-refunds` is still accepted and changes nothing).
