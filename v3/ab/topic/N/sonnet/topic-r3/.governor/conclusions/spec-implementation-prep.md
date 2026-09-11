# ledgerkit SPEC.md implementation prep

## Context

Repo `ledgerkit` has `version`/`inspect` implemented; SPEC.md specifies five
more things: `ingest`, `report`, `reconcile`, `validate`, and a `--config`
global flag. Nothing for these five is written yet. This session read the
whole repo (parsers, core, config, cli, tests, samples) plus SPEC.md and
docs/CONVENTIONS.md, and got two verbal amendments to SPEC.md from the user.
No code has been written yet — this is pre-implementation research.

House rules for this repo (all sessions): no `print` outside `ledgerkit.cli.emit`;
full type annotations on every public function's params and return; never
edit anything under `config/`; log via `ledgerkit.log.get_logger`; no new
dependencies; never import `ledgerkit.utils.cache`; never use
`ledgerkit.legacy_parser`; CLI flag names must match SPEC.md exactly
(`--out`, `--by`, `--records`, `--include-refunds`, `--tolerance`, `--config`).

## Outcome

Produced a full map of what SPEC.md's five features require and where the
existing code will fight the spec if used naively. Verified findings against
the file contents (paths below), not just SPEC prose.

### Per-system export differences (verified in parsers/system_{a,b,c}.py + samples/)
- **A (Ardent)**: `#`-comment preamble, then header, then rows; `posted_on` ISO
  date; `amount` plain decimal dollars, sign = refund; `memo` column is
  **quoted and may contain commas/embedded quotes**.
- **B (Borough)**: header + rows only, no comments; `value_date` ISO date;
  `amount` is **integer cents**, not dollars (`system_b.to_major_units`
  divides by 100 — must be used, don't `Decimal(raw)` directly); `descr`
  never quoted, never contains a comma; every row repeats `sys=B`.
- **C (Calder)**: banner + header + rows + `== N rows ==` trailer (trailer
  mismatch is a logged warning, not an error); `txn_date` is **day-first**
  `DD/MM/YYYY` (not ISO, not month-first) — reader hands it through
  unparsed on purpose; `gross_amount` plain decimal dollars like A.

### Traps for the implementer (all verified against current source)
1. `ledgerkit/parsers/system_a.py:70-74` raises `LedgerParseError` on any line
   containing `"`. `samples/system_a_export.csv` line 6 has a quoted,
   comma-containing memo. **`ingest` cannot read the shipped sample file
   until `system_a.py` is fixed** to use `ledgerkit/core/fields.split_record`
   (already quote-aware) instead of `line.split(",")` + the quote guard.
   `legacy_parser.py` is the tempting fix here — it is forbidden; don't use it.
2. `core/normalize.py:normalize()` defaults to `keep_refunds=False` (drops
   negative-amount rows). Maps cleanly onto `report`'s refund handling
   (see amendment below) and onto `reconcile` (always `keep_refunds=True`,
   spec says refunds always count there) — but `ingest` must force
   `keep_refunds=True` unconditionally, since SPEC says every posting must
   appear, nothing filtered.
3. `normalize()`'s `_clean` collapses internal whitespace in `description`
   and strips `record_id`. This is in tension with SPEC's "description
   preserved exactly" — flagged, not yet resolved; decide deliberately when
   writing `ingest`, don't let it happen as a side effect.
4. `validate` cannot reuse `read_rows()` as-is: all three readers raise and
   stop at the *first* malformed row. SPEC requires checking every row and
   reporting every reject with exit code 2 if any file has a reject or is
   unreadable. Needs its own per-line loop (reuse `core.fields.split_record`
   for shape) rather than the readers' raise-on-first-error paths.
5. `--config PATH` is a global flag with no argument to `load_settings()` —
   `config.py`'s only I/O hook is the `LEDGERKIT_CONFIG` env var. The CLI
   must set that env var from `--config` before any handler calls
   `load_settings()`, and must never touch `config/` itself.
6. `Record.sort_key` (date, system, record_id) already matches `ingest`'s
   required output order — `normalize()`'s sort can be reused as-is there.

### SPEC.md amendments from the user (override the written spec text — SPEC.md itself was not edited)
- `report`'s `--by account`/`--by month` output uses **`;` as the field
  separator**, not `,`. This applies only to `report`'s printed output —
  `ingest`'s normalized CSV file stays comma-separated; unaffected.
- `report` totals now **include refunds by default**. `--include-refunds`
  stays in the frozen flag-name list but becomes effectively a no-op (kept
  for ops-script compatibility, since passing it now matches the new
  default). No new "exclude refunds" flag was requested — do not invent one.
- Contradicted: the original SPEC.md text ("comma separated", "refunds left
  out of totals without `--include-refunds`") is superseded by the above for
  `report` specifically. Do not implement `report` per the literal SPEC.md
  wording for these two points.

## Lessons

- Don't trust a parser module's "handles quoting" claim from its docstring
  alone — `system_a.py`'s own module docstring says memo is quoted, but its
  `read_rows` actively rejects quoted lines. Verify against the actual
  guard/exception, not just the prose.
- `core/normalize.normalize(keep_refunds=...)` is designed to sit under
  exactly one call site's semantics at a time; reusing it for both `ingest`
  and `report`/`reconcile` needs a different `keep_refunds` value at each
  call site, not one shared default.

## Next steps

- Implement `ingest`: fix `system_a.py` quoting first, then build the four
  commands per SPEC.md as amended above, keeping all house rules.
- When writing `report`, use `;` separator and default-include refunds per
  the amendment, not the SPEC.md text.
- Resolve the description-whitespace tension (item 3 above) explicitly when
  writing `ingest` — decide whether to bypass `_clean`'s collapsing or accept
  it, and note the decision in the PR.
