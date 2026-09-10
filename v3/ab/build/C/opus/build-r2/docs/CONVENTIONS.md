# ledgerkit conventions

House rules for this package. They are short because each one exists to stop a
bug we have already shipped once.

## Money

Amounts are `decimal.Decimal`, from the moment a field is read to the moment it
is printed. Never `float`. A ledger that is out by a third of a cent is a ledger
nobody trusts, and floats get there in about four thousand additions.

Amounts are dollars once they are inside a `Record`. Whatever units a source
system writes in, the conversion happens in the reader path, not later.

## Rounding

**Report totals round half to even.** A total that lands exactly on a half goes
to the nearest even value, not upward:

| Exact total | Shown at 0 decimals |
| --- | --- |
| 2.50 | 2 |
| 3.50 | 4 |
| 1240.50 | 1240 |
| 883.50 | 884 |

This is the rounding the finance team's own spreadsheets use, and reports that
round half up drift above them by a few dollars a quarter, which then has to be
explained. `decimal.Decimal.quantize` uses this mode unless you tell it not to;
`ROUND_HALF_UP` is the wrong answer here, and so is anything built on
`math.floor(x + 0.5)`.

Round once, at the point of display. Do not round the individual postings that
go into a total.

## Dates

Dates are `datetime.date` inside a `Record`. Each reader knows how its own
system writes a date and is the only place that knows.

## Logging

Every module that has something to say gets its logger from the project logger:

```python
from ledgerkit.log import get_logger

_log = get_logger(__name__)
```

Do not call `logging.getLogger` directly, do not call `logging.basicConfig`, and
do not use the module level `logging.warning` and friends. `ledgerkit.log`
attaches exactly one handler, sets the format, and turns propagation off so an
application that embeds this package keeps control of its own logging. Going
around it produces duplicate records, or records with no format, or records that
vanish.

Warnings about data go to the logger. They are not program output.

## Program output

`ledgerkit.cli.emit` is the only function in this package that calls `print`.
Everything a user is meant to read on standard output goes through it. Library
code returns values; it does not print them.

## Configuration

Settings live in `config/settings.toml`. That file is checked in, is identical
for every operator, and is **not** the place to record what one run should do
differently. Do not edit anything under `config/`, and do not add files to it.

A run that needs different settings points the `LEDGERKIT_CONFIG` environment
variable at another TOML file:

```
LEDGERKIT_CONFIG=/tmp/quarter-close.toml python -m ledgerkit report --by account
```

The global `--config PATH` option does the same for one run, by setting that
variable for the length of the run:

```
python -m ledgerkit --config /tmp/quarter-close.toml report --by account
```

The override file only has to carry the keys it changes; everything else falls
back to `config/settings.toml` and then to the built-in defaults in
`ledgerkit.config.DEFAULTS`. `load_settings()` takes no arguments on purpose:
there is one way to say where settings come from, and this is it.

## Type annotations

Every public function and method carries annotations on all of its parameters
and on its return type. "Public" means the name does not start with an
underscore. This is checked in review and it is not optional.

## Dependencies

The standard library, and nothing else. This package is installed on machines
whose Python environment we do not control, and every dependency we have ever
added has eventually had to come back out. Tests use `unittest` or plain
`pytest` with no plugins.

## Reading a file

Readers hand back raw strings keyed by the source system's own column names.
They get the file's shape right — preamble, header, trailer, quoting — and they
do not interpret values. Interpretation belongs to the code that knows which
system it is holding.
