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
python -m ledgerkit ingest samples/*.csv
python -m ledgerkit report --by account
python -m ledgerkit report --by month
python -m ledgerkit reconcile
python -m ledgerkit validate samples/*.csv
python -m ledgerkit --config /tmp/quarter-close.toml report --by account
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
  checks.py           row by row validation
  config.py           settings loading
  log.py              the project logger
  mapping.py          account code to account name
  reporting.py        reading records back, totalling, reconciling
  legacy_parser.py    the field splitter from the previous importer
  core/               format independent pieces
    convert.py        raw export rows to records
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

All five things `SPEC.md` asks for are implemented.

Two of them do not match the wording in `SPEC.md`, because the wording was
superseded after it was written: `report` separates its columns with `;` rather
than `,`, and it counts refunds into its totals by default rather than leaving
them out. `--include-refunds` is still accepted. `SPEC.md` is left as it was.
