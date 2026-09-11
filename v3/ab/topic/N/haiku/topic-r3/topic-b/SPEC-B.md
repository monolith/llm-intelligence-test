# SPEC-B — `roster`, a shift-roster checker

Build the Python package `roster`. It reads a small plain-text roster, finds
scheduling conflicts, totals hours per person, and exposes a command line.

Python 3.12, standard library only. No third-party packages, no network. The
module layout inside the package is yours to choose; only the public names and
the command line below are fixed.

---

## 1. The roster format

One shift per line:

```
YYYY-MM-DD HH:MM-HH:MM name
```

- Lines are split with `str.splitlines()`. Each line is stripped of leading and
  trailing whitespace before anything else happens.
- A line that is empty after stripping is ignored.
- A line whose first character after stripping is `#` is a comment and is
  ignored. `#` anywhere else on a line is ordinary text.
- The line is split into at most three parts on runs of whitespace
  (`stripped.split(None, 2)`): the date, the time range, and the name.
- The date must be exactly `YYYY-MM-DD`, zero-padded, and a real calendar date.
  `2026-5-1` and `2026-02-30` are not valid.
- The time range must be exactly `HH:MM-HH:MM`, both times zero-padded 24-hour
  clock times (`00:00` through `23:59`). `8:00-16:00` is not valid.
- The name is the rest of the line after the time range, with leading and
  trailing whitespace removed. It may contain spaces, `#`, `:` and `-`, and is
  kept verbatim otherwise. It must not be empty.
- Two shifts belong to the same person when their names are exactly equal.
  Comparison is case-sensitive: `Ann` and `ann` are two different people.

### Midnight

A shift starts at `start` on `date`. If `end` is **strictly greater than**
`start`, the shift ends the same day. If `end` is **strictly less than**
`start`, the shift crosses midnight and ends on the following day. If `end`
**equals** `start`, the shift is zero-length: it ends at the instant it starts
and it lasts 0.0 hours.

Example: `2026-05-01 22:00-06:00 Ann` runs from 2026-05-01 22:00 to
2026-05-02 06:00 and lasts 8.0 hours.

---

## 2. Public API

All five names must be importable directly from `roster`:

```python
from roster import Shift, RosterError, parse_roster, find_conflicts, hours_by_person
```

### `Shift`

A frozen dataclass with exactly these fields, in this order:

```python
@dataclass(frozen=True)
class Shift:
    date: datetime.date   # the calendar date the shift starts on
    start: datetime.time  # start time of day
    end: datetime.time    # end time of day, as written on the line
    name: str             # the person, verbatim
    line: int             # 1-based line number in the parsed text
```

and these two read-only properties:

- `start_at -> datetime.datetime` — `datetime.combine(date, start)`.
- `end_at -> datetime.datetime` — `datetime.combine(date, end)`, plus one day
  when `end < start`.

Both are naive datetimes. No time zones anywhere in this task.

### `RosterError`

```python
class RosterError(ValueError):
    line: int      # 1-based line number of the offending line
    reason: str    # one of the four strings below
```

`str(err)` must be exactly `f"line {err.line}: {err.reason}"`.

`reason` is one of exactly these four strings, checked in this order, first
match wins:

| reason | when |
| --- | --- |
| `"bad line"` | the stripped line splits into fewer than two parts |
| `"bad date"` | the first part is not a valid `YYYY-MM-DD` date |
| `"bad time"` | the second part is not a valid `HH:MM-HH:MM` range |
| `"missing name"` | there is no third part, or it is empty after stripping |

So `2026-13-01 nonsense Ann` reports `"bad date"`, not `"bad time"`.

### `parse_roster(text: str) -> list[Shift]`

Returns the shifts in the order their lines appear in `text`, each with its
1-based `line`. Raises `RosterError` on the **first** malformed line and parses
no further. An empty text, or one holding only comments and blanks, returns
`[]`.

### `find_conflicts(shifts: Iterable[Shift]) -> list[tuple[Shift, Shift]]`

Two shifts conflict when they belong to the same person and their intervals
overlap by more than an instant:

```
a.start_at < b.end_at and b.start_at < a.end_at
```

That formula is the whole rule. Touching does not count: a shift ending at
16:00 and one starting at 16:00 are fine. Shifts belonging to different people
never conflict, however much they overlap. A zero-length shift conflicts only
with a shift of the same person that strictly contains its instant, and never
with another zero-length shift. Every conflicting unordered pair is reported
exactly once, so three mutually overlapping shifts yield three pairs.

Inside a pair, the shift with the smaller `(start_at, line)` comes first. The
returned list is sorted by

```
(a.name, a.start_at, a.line, b.start_at, b.line)
```

with names compared as ordinary Python strings.

### `hours_by_person(shifts: Iterable[Shift]) -> dict[str, float]`

Maps each name appearing in `shifts` to that person's total hours. Sum the
whole durations first, then round **once** at the end with `round(total, 2)` —
do not round the individual shifts. A person whose shifts are all zero-length
still appears, with `0.0`. Midnight-crossing shifts count their full length.
The keys are inserted in ascending name order, so `list(result)` is sorted.
An empty input returns `{}`.

Example: three 20-minute shifts for one person total `1.0`, not `0.99`.

---

## 3. Command line

`python -m roster check <file>` is the only supported invocation.

1. Read `<file>` as UTF-8 and parse it.
2. If the file cannot be read, print exactly `{file}: cannot read file` to
   stderr — `{file}` being the path exactly as it was given on the command
   line — print nothing to stdout, and exit **2**.
3. If parsing raises `RosterError`, print exactly
   `{file}: line {line}: {reason}` to stderr, print nothing to stdout, and
   exit **2**.
4. Otherwise print one line per conflict to stdout, in the order
   `find_conflicts` returns them, each formatted as

   ```
   {name}: {date} {start}-{end} overlaps {date} {start}-{end}
   ```

   with the dates as `YYYY-MM-DD` and the times as `HH:MM`, exactly as they
   appear in the roster (the `end` printed is the written end time, not the
   next-day date). The first shift of the pair is printed first. Example:

   ```
   Ann Diaz: 2026-05-01 08:00-16:00 overlaps 2026-05-01 15:00-20:00
   ```

   Exit **1** if there was at least one conflict.
5. If there were no conflicts, print exactly `no conflicts` to stdout and
   exit **0**.

Any other command line — a missing file argument, extra arguments, an unknown
subcommand, no arguments at all — prints exactly
`usage: python -m roster check <file>` to stderr and exits **2**.

---

## 4. Worked example

Input file `week.txt`:

```
# week 18
2026-05-01 08:00-16:00 Ann Diaz
2026-05-01 15:00-20:00 Ann Diaz

2026-05-01 16:00-22:00 Bo Fell
2026-05-01 22:00-06:00 Ann Diaz
2026-05-02 05:30-09:00 Ann Diaz
```

`python -m roster check week.txt` prints

```
Ann Diaz: 2026-05-01 08:00-16:00 overlaps 2026-05-01 15:00-20:00
Ann Diaz: 2026-05-01 22:00-06:00 overlaps 2026-05-02 05:30-09:00
```

and exits 1. `hours_by_person` on the same file gives
`{"Ann Diaz": 24.5, "Bo Fell": 6.0}`.

---

## 5. Tests you can run

`tests/test_public.py` holds three smoke tests. From the task directory:

```
python -m pytest tests/
```

They cover a fraction of the behaviour above. The spec, not the smoke tests,
is the contract.
