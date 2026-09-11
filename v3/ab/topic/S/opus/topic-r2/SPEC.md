# SPEC: the five commands ledgerkit still owes the warehouse team

`python -m ledgerkit` currently answers to `version` and `inspect`. This
specifies the five things it has to do next. Everything here is new work; none
of it is implemented.

Read `docs/CONVENTIONS.md` before writing any of it.

---

## 1. `ingest` — merge exports into one normalized file

```
python -m ledgerkit ingest FILE [FILE ...] [--out PATH]
```

Takes any number of export files, from any of the three systems, in any order
and any mixture, and writes one normalized CSV.

- `--out PATH` — where to write. Default `out/records.csv`. Parent directories
  are created if they do not exist.
- The output is a comma separated file with this header line, exactly:

  ```
  record_id,source_system,date,account_code,account_name,description,amount
  ```

- `record_id` is the identifier the source system gave the posting, unchanged.
- `source_system` is the single letter `A`, `B` or `C`.
- `date` is an ISO date, `YYYY-MM-DD`.
- `account_code` is the code the source system wrote.
- `account_name` is the name that code has in the package's account map. A code
  the map does not know is written with the label from the
  `[report] unknown_account_label` setting rather than being left blank.
- `description` is the source system's description text, preserved exactly,
  including any delimiter or quote characters it contained. It is quoted in the
  output where the CSV format requires it.
- `amount` is dollars with two decimal places, negative for a refund.
- **Every posting in the input files appears in the output.** Nothing is
  filtered, deduplicated or summarized.
- Rows come out ordered by date, then source system, then record id.
- One summary line goes to standard output when the write succeeds:

  ```
  wrote=<row count> to <path>
  ```

- Exit code 0 on success.

## 2. `report` — totals by account or by month

```
python -m ledgerkit report --by account|month [--records PATH] [--include-refunds]
```

Reads a normalized file and prints totals. It does not read the exports.

- `--by account|month` — required. Which grouping to total by.
- `--records PATH` — the normalized file to read. Default `out/records.csv`.
- `--include-refunds` — include postings with a negative amount in the totals.
  Without it, refunds are left out of the totals.
- `--by account` prints a header line and then one line per account code, codes
  ascending:

  ```
  account_code,account_name,total
  4100,Freight In,1234
  ```

- `--by month` prints a header line and then one line per month, months
  ascending, each month written `YYYY-MM`:

  ```
  month,total
  2026-01,5678
  ```

- Each total is shown with exactly as many decimal places as the
  `[report] decimals` setting says.
- The fields on a line are separated by a comma.
- Exit code 0.

## 3. `reconcile` — where the systems disagree

```
python -m ledgerkit reconcile [--records PATH] [--tolerance N]
```

Reads a normalized file and reports account and month combinations where the
systems that both posted to it do not agree on the total.

- `--records PATH` — default `out/records.csv`.
- `--tolerance N` — dollars. Two systems agree when their totals differ by no
  more than this. Default is the `[reconcile] tolerance` setting.
- Group every posting by account code, month and source system, and total each
  group. Consider only the account and month combinations that at least two
  systems posted to.
- The spread of a combination is its largest system total minus its smallest.
- A combination whose spread is greater than the tolerance is reported, one line
  each, ordered by account code and then month:

  ```
  MISMATCH 4200 2026-02 spread=57.75 A=455.00 B=512.75 C=-
  ```

  Every amount on that line has two decimal places. A system with no postings in
  that combination is written as a single `-`.
- The last line is always the count:

  ```
  mismatches=<n>
  ```

- All postings count toward reconciliation, refunds included.
- Exit code 0.

## 4. `validate` — reject malformed rows

```
python -m ledgerkit validate FILE [FILE ...]
```

Checks export files without writing anything. A row is rejected when any of
these is true:

- it does not have the number of fields its header says it should;
- its date field cannot be read as a date in the format that system writes;
- its amount field cannot be read as a number;
- its account code does not match the `[validate] account_code_pattern` setting.

For each rejected row, one `WARNING` goes through the project logger, naming the
file and the line number and saying what was wrong with it. Validation does not
stop at the first bad row; it checks all of them.

One summary line goes to standard output:

```
checked=<rows checked> rejected=<rows rejected>
```

Exit code 2 when one or more rows were rejected, or when a file could not be
read at all. Exit code 0 when everything passed.

## 5. `--config` — settings for one run

```
python -m ledgerkit --config PATH COMMAND ...
```

A global option, given before the subcommand, that makes this run read its
settings from `PATH` instead of the usual place. It works with every subcommand.

Nothing under `config/` is created, edited or deleted, by this option or by
anything else.

---

## Flag names

These names are fixed and are what the operations team's scripts will call:

`--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`.

## Not in scope

- No new subcommands beyond the four above.
- No changes to `version` or `inspect`.
- No new files under `config/`.
- No third party packages.
