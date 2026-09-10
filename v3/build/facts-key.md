# Planted facts F1 to F10

Ten facts phase 2 needs and `SPEC.md` does not contain. Nine are planted in the
repository the model reads in phase 1; the tenth arrives as the phase-1 spec
update (turn T5) and is nowhere in the repository at all.

Line numbers are for `fixture/`, which is what the model receives.
`reference/` differs only where the solution had to change a file.

The probe strings under each fact are for grepping a handover document, a set of
notes, or a plugin's saved state, to tell whether the fact crossed the session
cut. None of them occur in `SPEC.md`; a document that contains them got them from
the code or from the T5 update. A machine readable copy of every probe list is in
the JSON block at the end of this file.

---

## F1 — System B amounts are integer cents

**Planted:** `fixture/ledgerkit/parsers/system_b.py:85-98`, the docstring of
`to_major_units`, at the bottom of the module. Reinforced by
`fixture/samples/system_b_export.csv`, whose amount column holds values like
`25440` and `-8825` with no decimal point, and by
`fixture/ledgerkit/parsers/system_b.py:11` where the sample line in the module
docstring shows `25440`.

**Value:** the Borough `amount` column is whole cents, never dollars. `25440` is
`254.40`. `-8825` is a refund of `88.25`. Ardent and Calder both write decimal
dollars. The helper `to_major_units(raw)` already does the conversion and is
called by nothing in the fixture.

**Hidden tests:** `test_ingest_reads_system_b_amounts_as_dollars` (primary),
`test_ingest_keeps_refund_rows`, `test_reconcile_flags_exactly_the_disagreements`,
`test_reconcile_tolerance_flag_widens_the_window`,
`test_report_by_account_totals_round_half_to_even`,
`test_report_by_account_counts_refunds_by_default`, `test_report_by_month_totals`.
Treating the column as dollars fails eight of the twenty feature tests.

**Probes:** `to_major_units`, `minor units`, `integer cents`, `254.40`

---

## F2 — System C dates are day first

**Planted:** `fixture/ledgerkit/parsers/system_c.py:70-74`, the comment above the
field split in `read_rows`. Inferable without it from
`fixture/samples/system_c_export.csv`, which holds dates such as `27/02/2026`
and `31/01/2026` whose first component cannot be a month.

**Value:** Calder writes `txn_date` as `dd/mm/yyyy`. Ardent (`posted_on`) and
Borough (`value_date`) both write ISO `yyyy-mm-dd`. The trap is the ambiguous
rows: `C-0418` is `03/02/2026`, which is 3 February 2026 and not 2 March, and a
reader that tries month-first and falls back to day-first only on failure gets
those rows wrong silently while the later-in-the-month rows look fine.

**Hidden tests:** `test_ingest_reads_system_c_dates_day_first` (primary),
`test_reconcile_flags_exactly_the_disagreements`,
`test_reconcile_tolerance_flag_widens_the_window`, `test_report_by_month_totals`.

**Probes:** `dd/mm/yyyy`, `day-first`, `day first`, `2026-02-03`

---

## F3 — `utils/cache.py` is a decoy

**Planted:** `fixture/ledgerkit/utils/cache.py:3` ("Use for speed on large
files.") and `:37` (`cached_text`). The module docstring recommends it for the
exact situation ingest is in, and `SPEC.md` says nothing against it.

**Value:** the cache key is the absolute path of the file and nothing else, so a
file that changes between two runs is served from the first run's copy. Using it
anywhere in the reading path makes ingest return stale rows. The correct answer
is not to use it at all.

**Hidden tests:** `test_the_read_cache_is_not_imported` (constraint),
`test_ingest_reflects_a_changed_input_file` (feature).

**Probes:** `utils/cache`, `cached_text`, `.ledgerkit-cache`, `stale`

---

## F4 — `normalize()` drops refunds unless told not to

**Planted:** `fixture/ledgerkit/core/normalize.py:29` (the signature
`keep_refunds: bool = False`), `:36-40` (the docstring paragraph), `:46` (the
drop itself) and `:51` (an `INFO` log that is below the default `WARNING` level,
so the drop leaves no trace on a normal run).

**Value:** `normalize(records)` silently discards every posting with a negative
amount. `normalize(records, keep_refunds=True)` keeps them. The five refunds in
the samples are `A-10019` (-125.00), `A-10023` (-151.75), `A-10037` (-42.00),
`A-10041` (-31.20) and `B-2221` (-88.25). Ingest must pass `keep_refunds=True`,
or `out/records.csv` holds 115 rows instead of 120.

**Hidden tests:** `test_ingest_keeps_refund_rows` (primary),
`test_ingest_keeps_every_posting`,
`test_report_by_account_counts_refunds_by_default`, `test_report_by_month_totals`,
`test_reconcile_flags_exactly_the_disagreements`.

**Probes:** `keep_refunds`, `keep_refunds=True`, `silently drop`, `normalize()`

---

## F5 — logging goes through `ledgerkit.log.get_logger`

**Planted:** `fixture/docs/CONVENTIONS.md:41-59` ("Logging" and "Program
output"), and `fixture/ledgerkit/log.py` itself, which is the only module in the
package that imports `logging`. Every other module in the fixture opens with
`_log = get_logger(__name__)`.

**Value:** warnings go through `get_logger(__name__)`, never `print`, never
`logging.getLogger`, never the root logger. The handler writes to standard error
with the format `LEDGERKIT %(levelname)s %(name)s: %(message)s`, so a warning
`validate` raises reads `LEDGERKIT WARNING ledgerkit.<module>: ...`. `print` is
allowed in exactly one function, `cli.emit`.

**Hidden tests:** `test_validate_warns_through_the_project_logger` (feature,
primary), `test_no_print_outside_the_cli_output_function` (constraint),
`test_logging_goes_through_the_project_logger` (constraint).

**Probes:** `get_logger`, `ledgerkit.log`, `LEDGERKIT WARNING`

---

## F6 — settings override goes through the environment

**Planted:** `fixture/docs/CONVENTIONS.md:66-84` ("Configuration"),
`fixture/ledgerkit/config.py:29` (`CONFIG_ENV_VAR = "LEDGERKIT_CONFIG"`), `:59`
(`config_path`) and `:85` (`load_settings`, which takes no arguments).

**Value:** settings come from `config/settings.toml`. `config/` must not be
edited or added to. A run that needs different settings sets the
`LEDGERKIT_CONFIG` environment variable to another TOML file; the loader already
supports it and layers it over the checked-in file, so an override file only
needs the keys it changes. `SPEC.md` asks for a `--config PATH` flag and does not
say how it should work; the flag sets that variable.

**Hidden tests:** `test_config_flag_and_environment_variable_both_select_settings`
(feature, primary), `test_config_directory_is_untouched` (constraint).

**Probes:** `LEDGERKIT_CONFIG`, `load_settings`, `environment variable`

---

## F7 — the pointer to `legacy_parser.py` is stale

**Planted:** `fixture/ledgerkit/parsers/system_a.py:70-74`, the error raised on a
System A line containing a quote character: "this reader does not handle quoted
fields; see legacy_parser.py for quoted fields". `fixture/ledgerkit/legacy_parser.py:15`
is `split_quoted`, which the message sends you to.

**Value:** the message is out of date. `legacy_parser.split_quoted` splits on
every delimiter including the ones inside a quoted field and peels quote
characters off the pieces, so `A-10001`'s memo, `Rebill, "Q1 true-up", carrier`,
comes back as three mangled fields and every System A row after it is off by two
columns. The right helper is `fixture/ledgerkit/core/fields.py:21`,
`split_record`, which the other readers already use; the standard library `csv`
module is equally correct.

**Hidden tests:** `test_the_legacy_parser_is_not_used` (constraint, primary),
`test_ingest_preserves_a_quoted_description`, `test_records_file_stays_comma_separated`.
Using `split_quoted` breaks System A parsing outright and takes nineteen of the
thirty tests with it.

**Probes:** `legacy_parser`, `split_quoted`, `split_record`, `core/fields`

---

## F8 — account 5200 appears twice in the map and the last entry wins

**Planted:** `fixture/ledgerkit/mapping.py:14` (the module docstring table, which
says 5200 is "Warehouse Labor" and is stale), `:35` (the first dict entry, also
"Warehouse Labor"), `:40-45` (the comment explaining that the later key wins) and
`:46` (the entry that actually takes effect).

**Value:** account 5200 is **Contract Labor**. "Warehouse Labor" is the old name;
it survives in the docstring table and in the earlier dict entry, and Python
keeps the later of two identical keys in a dict literal, so `ACCOUNT_NAMES["5200"]`
is "Contract Labor". Any implementer who reads the docstring table, or retypes
the map, gets the wrong name.

**Hidden tests:** `test_ingest_names_account_5200_from_the_live_map` (primary).

**Probes:** `Contract Labor`, `Warehouse Labor`, `duplicate key`, `last entry wins`

---

## F9 — report totals round half to even

**Planted:** `fixture/docs/CONVENTIONS.md:15-33` ("Rounding").

**Value:** a total that lands exactly on a half goes to the nearest even value,
not upward. 2.50 shows as 2 and 3.50 shows as 4. With `[report] decimals = 0`,
account 4100 totals 6248.50 and must print `6248`; account 5200 totals 1747.50
and must print `1748`; the month 2026-02 totals 8456.50 and must print `8456`.
Half-up rounding gives 6249 and 8457 and is the failure this fact prevents.
`decimal.Decimal.quantize` uses this mode by default; `ROUND_HALF_UP` and
`math.floor(x + 0.5)` do not.

**Hidden tests:** `test_report_by_account_totals_round_half_to_even` (primary),
`test_report_by_month_totals`.

**Probes:** `half to even`, `ROUND_HALF_EVEN`, `banker`, `6248`

---

## F10 — the spec update delivered at turn T5

**Planted:** nowhere in the repository. It arrives as the fifth phase-1 user turn
in `phase1-turns.json` (`"kind": "update"`) and contradicts `SPEC.md`, which
still describes the old behaviour at `fixture/SPEC.md` sections 2.

**Value:** two changes to `report` and to nothing else.

1. The report's columns are separated by `;`, not `,`. The header line becomes
   `account_code;account_name;total` and `month;total`. The normalized records
   file `out/records.csv` stays an ordinary comma separated CSV; the change is
   scoped to what `report` prints.
2. Refunds are counted in report totals by default. `SPEC.md` says they are left
   out unless `--include-refunds` is given; after the update they are always in,
   and the flag stays accepted. With refunds in, account 5100 totals 3400, 6100
   totals 3577 and 8800 totals 315; with refunds out they are 3765, 3619 and 346.

**Hidden tests:** `test_report_by_account_uses_the_semicolon_delimiter`
(change 1), `test_report_by_account_counts_refunds_by_default` (change 2),
`test_report_by_month_totals` (both), `test_records_file_stays_comma_separated`
(the scope of change 1).

**Probes:** `semicolon`, `refunds by default`, `no longer excluded`, `spec update`

---

## Probe strings, machine readable

```json
{
  "F1": ["to_major_units", "minor units", "integer cents", "254.40"],
  "F2": ["dd/mm/yyyy", "day-first", "day first", "2026-02-03"],
  "F3": ["utils/cache", "cached_text", ".ledgerkit-cache", "stale"],
  "F4": ["keep_refunds", "keep_refunds=True", "silently drop", "normalize()"],
  "F5": ["get_logger", "ledgerkit.log", "LEDGERKIT WARNING"],
  "F6": ["LEDGERKIT_CONFIG", "load_settings", "environment variable"],
  "F7": ["legacy_parser", "split_quoted", "split_record", "core/fields"],
  "F8": ["Contract Labor", "Warehouse Labor", "duplicate key", "last entry wins"],
  "F9": ["half to even", "ROUND_HALF_EVEN", "banker", "6248"],
  "F10": ["semicolon", "refunds by default", "no longer excluded", "spec update"]
}
```
