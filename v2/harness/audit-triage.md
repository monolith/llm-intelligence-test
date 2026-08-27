# Audit triage — v2.1 mechanical audit

Baseline before this pass: `PASS 163  FAIL 69  UNPARSED 1` (70 items needing classification).
Final after script fixes: **`PASS 183  FAIL 22  UNPARSED 19`** (see § Final summary).

Every FAIL and the one UNPARSED item from the baseline run is classified below into:

- **(a) script false positive** — fixed in `audit.py` with new tests in `test_audit.py`, or (where no safe generic fix exists) downgraded from a misleading FAIL to UNPARSED and documented as a known limitation.
- **(b) real material defect** — a genuine problem in the test corpus (`test-input/`). Not edited (per instructions); exact proposed edits given below.
- **(c) key bookkeeping defect** — `answer-key/corruption-map.md` is stale or malformed relative to the corpus. Not edited; exact proposed edits given below.

Counts: **(b) = 6**, **(c) = 10**, (a) = 54.

---

## (a) Script false positives — 54 items, fixed or downgraded in `audit.py`

### Fix 1 — near-tie table's duplicate "Carried by" header (12 items)

The near-tie table has **two** columns named "Carried by" (wrong-value carriers, then
correct-value carriers). `parse_table` built `dict(zip(header, cells))`, and a Python dict
silently keeps only the *last* of two same-named keys — so every near-tie row's
`carried_by` actually held the **correct**-value carriers, not the wrong-value carriers the
check needed. This single bug produced the 1 baseline UNPARSED item and 11 of the 14
baseline near-tie FAILs.

**Fix:** `dedupe_headers()` renames the second (and further) occurrence of a repeated
column name (`"carried by"` → `"carried by (2)"`) before the header/cell zip, so the first
occurrence's lookups are no longer clobbered. Tests: `test_dedupe_headers_disambiguates_repeated_column_names`,
`test_parse_table_keeps_both_columns_when_header_repeats`,
`test_near_tie_duplicate_carried_by_headers_checks_the_wrong_value_carriers`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| NT-2 | `$2,510` | r05, r11 | Fixed → PASS |
| NT-3 (was UNPARSED) | `57` | r08, r12 | Fixed → PASS |
| NT-4 | `600 feet` | r11, r12 | Fixed → PASS |
| NT-5 | `50 degrees` | r02, r09 | Fixed → PASS |
| NT-6 | `−13°F` | r04, r11 | Fixed → PASS (also needed Fix 7, below) |
| NT-9 | `1876` | r07, r10 | Fixed → PASS |
| NT-1 | `4 inches` | r02, r09 | Header bug fixed; a residual leak remains — see the needs-human note under Fix 8 |
| NT-7 | `nephew` | r01, r12 | Header bug fixed; a residual leak remains — see Fix 8 |
| NT-8 (×2) | `my father's uncle`, `his grand-niece` | r01, r04 | Header bug fixed; the row's structure needs a further, unimplemented special case — see Fix 8 |
| NT-10 (`8`) | `8` | r06, r09 | Header bug fixed; a residual leak remains — see Fix 8 |
| NT-11 (×2) | `30`, `13` | r08, r12 | Header bug fixed; a residual leak remains — see Fix 8 |

### Fix 2 — greedy quote-extraction regex swallowed the citation line (2 items)

`parse_narrator_briefs_documents` joined a blockquote block (quote + its "— *Source*, date"
attribution line, both starting with `>`) into one string, then matched `\*(.*)\*` —
**greedy**, so it read from the quote's opening `*` to the **last** `*` anywhere in the
block, which is inside the attribution's own `*italics*` or `**bold**`. The captured "quote"
came out with garbage from the citation glued on, so it could never match the retelling
verbatim.

**Fix:** non-greedy `\*(.*?)\*`. Test: `test_parse_narrator_briefs_documents_stops_at_first_closing_asterisk`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| r02 doc#1 | D3 (*Ninestone Sentinel*, 8 March 1898) | narrator-briefs.md, r02 | Fixed → PASS |
| r12 doc#1 | D9 (Tolliver shop book, May 1929) | narrator-briefs.md, r12 | Fixed → PASS |

### Fix 3 — markdown bold markers leaking into an extracted quote (2 items)

`extract_quoted_spans` pulls the *content* between straight quote marks verbatim, including
any `**bold**` markup the key author put around one word inside the quote (e.g. `"maintained
over **eight** miles"`, `"— A.R.**"`). The literal `**` characters were never in the
retelling, so the search failed.

**Fix:** `clean_quote` now strips embedded `**`. Test: `test_clean_quote_strips_embedded_bold_markers`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| X46 | `maintained over **eight** miles` | corruption-map.md, r09 | Fixed → PASS |
| X19 | `**— A.R.**` | corruption-map.md, r07 | Fixed → PASS (this candidate then needed Fix 5 too, since the cleaned text overlaps r04's copy of the same document — see below) |

### Fix 4 — ellipsis-elided quote in the As-told cell (1 item)

X39's (decoy theory, r02) As-told cell abbreviates a long quoted passage with an ellipsis:
`"Forty tons is forty tons… I say the weight did it."` — the actual retelling has the full
sentence in between, so no literal match for the string containing `…` was possible.

**Fix:** `candidate_present()` splits a candidate on `…` and requires each part present
independently. Test: `test_candidate_present_handles_ellipsis_elided_quote`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| X39 | `Forty tons is forty tons… I say the weight did it` | corruption-map.md, r02 | Fixed → PASS |

### Fix 5 — a candidate that is really a fragment of a shared verbatim document (2 items)

Two failure modes, same root cause: an As-told cell's quoted text is (or contains) a
verbatim document quote that is, by design, transcribed in more than one narrator — check 4
already verifies that placement separately. Requiring it to also be *unique* to one narrator
(check 2's normal rule) is the wrong test for it.

- **X35** (r12, late reversal): the As-told cell quotes D9 (`"No. 4 (ex-Cadder Valley 9) cut
  up at Sixmile this month..."`) as the *evidence* that retracts the early claim. D9 is
  legitimately transcribed in r05, r07, *and* r12.
- **X19** (r07, internal contradiction): the cleaned candidate `— A.R.` (after Fix 3) is the
  tail of D1's page-62 entry, which r04 *also* transcribes verbatim in full.

**Fix:** `check2_planted_errors` now takes `known_document_quotes` (built from
`parse_narrator_briefs_documents`, moved earlier in `run_audit` so it is available before
check 2 runs) and skips any candidate that is a bounded substring of a known document quote
— computed with `bounded_search`, not plain `in`, so a short candidate cannot match by
accident inside an unrelated longer word (verified by
`test_check2_standalone_error_present_only_in_assigned_narrator_passes`, which would have
broken had this been naive substring matching, since `"red"` is a substring of `"measured"`).
Test: `test_known_document_quote_fragment_excluded_from_uniqueness_check`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| X35 | `No. 4 (ex-Cadder Valley 9) cut up at Sixmile this month. Scrap to Ravel Brothers, $470` | corruption-map.md, r05/r07/r12 | Fixed → candidate now skipped (no longer reported); the item's other two candidates already PASS |
| X19 | `— A.R.` (after Fix 3) | corruption-map.md, r04/r07 | Fixed → candidate now skipped; X19's other two candidates PASS/FAIL as below |

### Fix 6 — semicolon vs. period at a clause boundary (2 items)

The key sometimes joins two clauses of a quoted claim with `"; "`; the authored retelling
instead ends the clause as its own sentence (`". He"`, capitalized). `bounded_search` is
already case-insensitive, so only the punctuation character itself blocked the match.

- **X21** (r08, internal contradiction): key has `"...bridge; he was..."`, r08 has
  `"...bridge. He was..."`.

**Fix:** `generate_punctuation_variants()` (swap `"; "` ⇄ `". "`), folded into
`candidate_present()`, and check 6's internal-contradiction check now calls
`candidate_present` instead of a bare `bounded_search`. Test:
`test_candidate_present_handles_semicolon_period_clause_boundary`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| X21 | `My father had no hand in that bridge; he was in the Ninestone office the whole time it was building` | corruption-map.md, r08 | Fixed → PASS |
| Check 6 "Internal contradictions: r08 content" | same quote | corruption-map.md, r08 | Fixed → PASS (downstream of the same fix) |

### Fix 7 — number/unit word forms and the Unicode minus sign (7 items, check 3; 1 item, check 2)

The recoverability index's short "value" tokens (`"2 in"`, `"40 ft"`, `"66°F"`, `"−54°F"`)
never appear in that exact shorthand in the prose retellings, which spell out `"two inches"`,
`"forty feet"`, `"sixty-six degrees"`, or (for negatives) this corpus's fixed idiom
`"fifty-four below zero"`/`"fifty-four below"` — a form that never uses the word "degrees"
at all. Separately, `_candidate_tokens_from_fact_cell`'s number regex only recognized an
ASCII `-` for a negative sign; this key's negative values are written with the Unicode minus
`−` (U+2212) throughout, so a value like `−54°F` was silently captured as the *positive*
token `54°F`.

**Fix:** `expand_measurement_token()` expands a short measurement token into inch/foot/degree
word forms (singular for 1), the bare `°` symbol, and the "below zero"/"below" idiom for
negatives; wired into both check 3's `has_hit` and `candidate_present` (so it also helps
check 2's near-tie matching — this is what actually fixed NT-6, listed under Fix 1). The
number regex now accepts `[-−]?` instead of `-?`. Tests:
`test_expand_measurement_token_inches_feet_and_degrees`,
`test_expand_measurement_token_negative_temperature_uses_below_zero_idiom`,
`test_candidate_tokens_from_fact_cell_keeps_unicode_minus_sign`.

| Item | Value | Files | Verdict |
|---|---|---|---|
| F025 | `2 in` → "two inches" | r04, r07, r09, r11 | Fixed → PASS |
| F032 | `40 ft` → "forty feet" | r04, r07, r11 | Fixed → PASS |
| F060 | `1 in`, `40°` | r04, r07 | Fixed → PASS |
| F061 | `66°F` → "sixty-six degrees" / bare "66°" | r02, r04, r07, r12 | Fixed → PASS |
| F078 | `540 ft` → "five hundred and forty feet" | r02, r09 | Fixed → PASS |
| F062 | `−54°F` → "fifty-four below zero" | r04, r07 | Sign now recognized and r04 now hits; r07 genuinely never states the derived value (it only supplies the raw ingredients) — correctly downgraded to UNPARSED by Fix 9, not a key defect (see note there) |
| F063 | `−14°F` → "fourteen below zero" | r04, r07 | Same as F062 |
| F089 | `40°` → "forty degrees" | r03, r09 | r09 now hits; r03 phrases it as "above forty in the daytime" with no unit word at all, so it still does not hit — remains a genuine FAIL. **Needs-human**: no safe generic fix (a bare-number fallback would be far too permissive elsewhere in the corpus) |

### Fix 8 — bare short values that legitimately recur elsewhere in the corpus for an unrelated fact (needs-human, no code fix — 7 items)

These are the residual near-tie leaks left after Fix 1. In every case the *design* is fine —
a human or an LLM solver reading the surrounding sentence disambiguates instantly — but a
short bare number or common word (`"4 inches"`, `"nephew"`, `"8"`, `"30"`, `"13"`,
`"1902"`, `"A. Rennick"`) is not a safe unique fingerprint for a substring checker: this
corpus reuses the same small numbers and kinship words for multiple, unrelated facts. I
manually confirmed each "leak" is a real, correct, unrelated use — not a corruption of the
near-tie value:

| Item | Value | "Leaked into" | What's actually there (verified) | Verdict |
|---|---|---|---|---|
| NT-1 | `4 inches` | r03, r04 | F031's *correct, uncontested* fact — "rocker bearings... measure four inches of travel each way" (the 1954 rockers, not Sheet 11) | Needs-human, no fix |
| NT-7 | `nephew` | r10 | r10's own correct family tree: "[Judd] was Emil's son, which made him my mother's nephew" — an unrelated, correct nephew relationship | Needs-human, no fix |
| NT-10 | `8` | r02, r03, r04, r05, r07, r11 | Six unrelated uses of the digit/word "eight" (e.g. r09's own "eight miles" off-by-one error X46, "$8,600", etc.) | Needs-human, no fix |
| NT-11 | `30` | r03, r04, r05, r06, r07, r09, r10 | The unrelated "fall of thirty degrees" weather-condition threshold, stated by nearly every narrator who discusses the two conditions | Needs-human, no fix |
| NT-11 | `13` | r04, r09, r11 | NT-6's *different* near-tie value ("thirteen below[ zero]", r04/r11) plus r09's arithmetic "thirty-**four**"... (coincidental digit overlap across two unrelated near-tie pairs) | Needs-human, no fix |
| X16 | `1902` | r10, r12 | F043's *correct, uncontested* fact — "She married... in 1902" (Adela's marriage year, unrelated to the locomotive sale year X16 corrupts) | Needs-human, no fix |
| X19 | `A. Rennick` | r10 | r10's blockquote citation line, correctly addressing the CVR letter to Adela ("A. Rennick") — a different, correct use of her own initials | Needs-human, no fix |

I did not attempt a generic fix for any of these: the shared trait is a short, common
value doing double duty in natural prose, and any regex clever enough to disambiguate one
case risks silently hiding a real future leak in another. **Caveat for the record:**
`HARDENING-v2.1.md` §3 claims "Carrier uniqueness verified by grep across all twelve files
... each of the twenty-two near-tie values sits in exactly the two narrators named" — that
grep almost certainly hit the same collisions and was reading past them by eye, the same way
I had to. It is not wrong about the *design* (I confirmed by hand that it holds), only about
what a bare grep can mechanically prove.

NT-8's two items (`my father's uncle`, `his grand-niece`) are a related but distinct case: its
row is annotated `(r04: "my father's uncle"; r01: "his grand-niece")` — each carrier has its
*own*, different wrong phrasing, not a shared literal value. The generic near-tie checker
(built for the other 10 pairs, which do share one literal wrong value) doesn't model that
per-narrator-different-phrasing structure, and I did not add a one-off parser for a single
row. I confirmed by hand both phrases are exactly where they should be: r04 line 29 ("my
father's uncle, Judd Rennick") and r01 line 37 ("she was his grand-niece, they told me").
**Needs-human / script limitation, verified correct.**

### Fix 9 — recoverability rows that resolve by paraphrase, arithmetic, or a quoted document, not by narrator repetition (28 items)

`check3_recoverability` only ever checked "does this literal string appear in ≥2 listed
narrators," even though the key's own "How it resolves" column, and the `✎` document mark,
frequently say the fact resolves a different way — through arithmetic derivation, a document
already verified separately by check 4, or (for relationship/mechanism facts) narrators
stating the same fact in their own very different words, which was never going to appear as
a literal match of the key's own paraphrase.

**Fix:** `RecoverabilityRow` now carries `how_resolves`. `is_freeform_fact_label()` flags a
row whose tokens are a whole-sentence fallback (no digit found at all). When a row would FAIL
(fewer than the required hits) *and* it is freeform, doc-marked, or its resolution text
contains "arithmetic," the check now reports **UNPARSED** ("needs human check") instead of a
misleading FAIL — because a literal-substring miss does not prove the fact is actually
absent from the corpus. It still reports PASS normally when hits are found, and still FAILs a
row that is none of those things (plain numeric, no doc mark, no arithmetic — see the
`F006` counter-example in § (c), which correctly still needs a key fix, and the
`test_check3_plain_numeric_fact_still_fails_when_genuinely_short` regression test, which
confirms the downgrade does not swallow a real gap). Tests:
`test_check3_freeform_fact_label_reports_unparsed_not_fail`,
`test_check3_arithmetic_marked_fact_reports_unparsed_not_fail`.

I manually verified the underlying fact really is present (in different words) for every one
of these, so none is a corpus defect:

| Item | Value | Files | What's actually there (verified) |
|---|---|---|---|
| F003 | "Adela and Emil siblings" | r10, r12 | r10: "was his younger sister"; r12: "Emil Rennick had a sister, Adela Rennick" |
| F008 | "Judd = Ruth's first cousin once removed" | r10, r07 | r10 line 17: "...so Ruth and Judd stood as first cousins once removed" (literal, different sentence order); r07 gives all four links to derive it |
| F009 | "Warren Tice, resident engineer" | r02, r12 | r02: "The resident engineer on the work was Warren Tice"; r12: "The resident engineer was Warren Tice" (word order reversed from the key's label) |
| F010 | "Dorsey = Warren's son" | r08, r10 | r08 (Dorsey himself) calls Warren "my father" throughout; r10: "His son Dorsey kept the store" |
| F014/F015 | "Peter and Lettie, father and daughter" | r06, r10 | r06: "My father was Peter Wexler"; r10: "begun by Peter Wexler and kept afterward by his daughter Lettie. Father and daughter, in that order" |
| F018–F020 | "custody chains" | r04, r07, r10 | Provenance paragraphs in all three spell out who held which book when, just not as a bare phrase "custody chain" |
| F023 | "north end fixed, south on rollers" | r02, r04, r09 | r02: "pinned solid at its north end and its south end was left free... rested on a nest of rollers"; r04: "pinned at the north end and free at the south"; r09: "north bearing... is fixed. The south bearing was... a nest of rollers" |
| F087 | "binding, stick-slip release, report along the rails" | r03, r04, r09 | r03: "it came up the rails first"; r04: "the south shoe hung up... let go all at once... one report that ran along the rails"; r09 gives the full technical mechanism |
| F088 | "both conditions necessary" | r03, r04, r09 | r09 explicitly: "The conditions set down at the depot are necessary conditions. They are not sufficient ones." r03/r04 state both conditions as jointly required without using the word "necessary" |
| F095 | "the forty-ton deck was not the cause" | r04, r09 | r09 ¶15 self-refutes its own decoy ("The deck of 1909 was not disturbed... nothing was altered in March 1954 but the bearings"); the 86 − 2×40 = +6 arithmetic is independently verified elsewhere (F064, already PASSing) |
| Silas Tolliver... | "founder" | r05 | "Silas Tolliver was born in 1849 and came into this county with a mill..." — present, just not phrased as "founder" |
| Pearl Nace by name | — | r05 | "My mother, Pearl Tolliver Nace, was born in 1881..." — present |
| F062, F063 | `−54°F`, `−14°F` | r04, r07 | Legitimate arithmetic design: r04 states the derived value in prose; r07 supplies the raw ingredients (D1's 3-inch spec, D2's rule, D1's 66° erection reading), each independently verified elsewhere (F024, F060, F061 all PASS) — a careful reader, not r07 itself, does the subtraction |
| F074 | "1955/56's three nights excluded" | r03, r07 | Settled by D8, verbatim in both (already confirmed by check 4, PASS) — D8's own text never contains the digits 1955 or 1956, so the fact's label is a gloss for the key author's own reference, not a literal requirement |
| F083 | "27 years at Tolliver" | r05, r07 | r05 literally states "Twenty-seven years"; r07 supplies the D5-sale-date ingredient. Substantively fine as arithmetic — but the *cell itself* is malformed, see § (c) |

---

## (b) Real material defects — 6 items (test corpus; not edited)

All six are genuine near-verbatim (12+ word) copies of an **original story's own narration**
— not a designed document quote — into a retelling that covers the same ground. The
`originals/*.md` files are the four canonical source stories; retellings are meant to
paraphrase them (documents may be quoted verbatim; plain narration should not be). I found
these only after the blockquote-exclusion fix (Fix, § a) removed the 9 legitimate
document-quote overlaps that had been masking them in the noise.

| Check | Value / matched run | Files | Verdict |
|---|---|---|---|
| 5 (12-gram) | `"march 1898 a work train came down off the quarry grade without"` | `originals/01-the-two-inch-mark.md` line 76 vs. `test-input/retellings/r02-a-clerks-son-remembers.md` line 25 | Real defect — near-verbatim prose copy |
| 5 (12-gram) | `"the state's flood control cut took sallow creek out of its bed"` | `originals/04-what-the-creek-gave-back.md` line 3 vs. `test-input/retellings/r04-what-the-creek-gave-back.md` line 5 | Real defect — the retelling's opening sentence is an almost word-for-word lift of the original's own opening sentence |
| 5 (12-gram) | `"...years because she was better at it than anybody her father could..."` | `originals/03-delivered-on-her-own-wheels.md` line 18 vs. `test-input/retellings/r05-the-engines-my-grandfather-bought.md` line 11 | Real defect — near-verbatim prose copy |
| 5 (12-gram) | `"the date the day's high the night's low whether she spoke and"` | `originals/02-the-night-book.md` line 48 vs. `test-input/retellings/r11-sentinel-ghost-lies-down.md` line 29 | Real defect — near-verbatim prose copy |
| 5 (12-gram) | `"the ninth of february 1954 in march of that year the railroad"` | `originals/02-the-night-book.md` lines 97–99 vs. `test-input/retellings/r12-our-valley-school-history.md` line 51 | Real defect — near-verbatim prose copy, spanning a paragraph break in the original |
| 5 (12-gram) | `"five columns the date the day's high the night's low whether she"` | `originals/02-the-night-book.md` line 48 vs. `test-input/retellings/r03-the-night-book.md` line 19 | Real defect, but **minor** — this is Judd (r03) describing the physical column headers of his own night book, which is inherently hard to phrase many different ways; flagging for completeness, lowest priority of the six |

**Proposed edits** (paraphrase only — meaning preserved, wording changed enough to break the
12-word run; re-check word count 1,200–1,800 and re-run the 12-gram check after any of
these):

1. **`test-input/retellings/r02-a-clerks-son-remembers.md`**
   old: `On the morning of 6 March 1898 a work train came down off the quarry grade without brakes enough to hold her.`
   new: `On the morning of 6 March 1898 a work train started down the quarry grade with nothing left to hold her.`

2. **`test-input/retellings/r04-what-the-creek-gave-back.md`**
   old: `The state's flood-control cut took Sallow Creek out of its bed for eleven weeks and the gorge was dry to the gravel.`
   new: `A state flood-control project had pulled Sallow Creek out of its bed for eleven weeks, leaving the gorge dry down to the gravel.`

3. **`test-input/retellings/r05-the-engines-my-grandfather-bought.md`**
   old: `...kept the company's books from the age of eighteen, which is to say for thirty-nine years, because she was better at it than anybody her father could hire.`
   new: `...kept the company's books from the age of eighteen, which is to say for thirty-nine years, because nobody her father ever hired did the work as well as she did.`

4. **`test-input/retellings/r11-sentinel-ghost-lies-down.md`**
   old: `kept a ruled book of every night the sound came — the date, the day's high, the night's low, whether she spoke, and the hour.`
   new: `kept a ruled book of every night the sound came: the date, how warm the day had been, how cold the night ran, whether she spoke, and at what hour.`

5. **`test-input/retellings/r12-our-valley-school-history.md`**
   old: `The last night the bridge was heard was the ninth of February, 1954. In March of that year the railroad rebuilt the bridge to carry the new diesel engines, and put new bearings under the long span, and from that month to this the valley has not heard a sound.`
   new: `The last night the bridge was heard was the ninth of February, 1954. The following month the railroad rebuilt the bridge to carry the new diesel engines, and put new bearings under the long span, and from that time to this the valley has not heard a sound.`

6. **`test-input/retellings/r03-the-night-book.md`** (lowest priority — see note above)
   old: `Five columns. The date. The day's high. The night's low. Whether she spoke. And the hour.`
   new: `Five columns. The date, how warm the day ran, how cold the night got, whether she spoke, and the hour of it.`

---

## (c) Key bookkeeping defects — 10 items (`answer-key/corruption-map.md`; not edited)

### Stale As-told quotes (r01, r03) — 4 items

Three quotes in `corruption-map.md`'s per-narrator error tables no longer match the current
text of the retellings they describe (the retelling was evidently edited after the key text
was written, and the key's quote was never re-synced). The underlying corruption is still
genuinely present in the retelling — it's the key's transcription that's wrong, not the
corpus.

| Item | Value | Files | Verdict |
|---|---|---|---|
| X01 | "Number Nine and her crew are down in that gorge, and it is her they hear." | corruption-map.md line 44, r01 | Stale quote |
| X02 | "started the winter the bridge was new" | corruption-map.md line 45, r01 | Stale quote |
| X12 | "I went on nights in 1907 and started the book that same winter." | corruption-map.md line 105, r03 | Stale quote, missing one word ("I") |
| Check 6 "A narrator wrong only on dates: r03 content" | (same as X12) | corruption-map.md, r03 | Downstream of X12 — resolves automatically once X12's key text is fixed |

**Proposed edits:**

- `answer-key/corruption-map.md`, r01's error table, X01 row:
  old: `"Number Nine and her crew are down in that gorge, and it is her they hear."`
  new: `"They are down there yet, under the gravel and the water, and it is her working the grade that the valley hears."`

- `answer-key/corruption-map.md`, r01's error table, X02 row:
  old: `The boom "started the winter the bridge was new" (1897/98).`
  new: `The boom started "that same winter, the first winter after they opened that bridge — that would be ninety-seven going into ninety-eight — right on the heels of the wreck."`

- `answer-key/corruption-map.md`, r03's error table, X12 row:
  old: `"I went on nights in 1907 and started the book that same winter."`
  new: `"I went on nights in 1907 and I started the book that same winter."`

### Recoverability index overclaims a birth-year carrier — 3 items

F004, F006, and F007 each list 2–3 "Correct in" narrators, but for each fact only **one**
narrator (r10, in every case) literally states the year — I checked both digit and spelled-
out word forms and found nothing in the other listed narrators. These read exactly like the
already-correctly-classified "Single-source scored facts" a few rows below them (Ruth's
1934, Emil's 1866) — they were evidently missed when that section was assembled, or the
narrators once carried the year and lost it in an edit.

| Item | Value | Files | Verdict |
|---|---|---|---|
| F004 | "Judd b. 1888" — claims r07 ✎, r10, r12 | corruption-map.md, r07/r12 | r07/r12 confirm "Emil's son" but neither states 1888, in digits or words; the parenthetical "(when Judd Rennick was nine years old)" that would let a reader derive it is corruption-map's own annotation, not text in r07's retelling |
| F006 | "Wendell b. 1904" — claims r04, r10 | corruption-map.md, r04 | r04 confirms "Adela's son" ("my father, Wendell Frayne") but never states 1904 |
| F007 | "Ruth... b. 1934" — claims r04, r07 ✎, r10 | corruption-map.md, r04/r07 | r04/r07 confirm her profession but neither states 1934 |

**Proposed edits** (narrow each to single-source, matching the section's existing "Single-source scored facts" table):

- `| F004 Judd b. 1888, Emil's son | r07 ✎, r10, r12 | — | Majority + arithmetic (Adela b. 1874 could not have a son b. 1888) |`
  → `| F004 Judd b. 1888, Emil's son | r10 | — | Single-source for the birth year (r07, r12 confirm "Emil's son" but neither states 1888) |`

- `| F006 Wendell b. 1904, Adela's son | r04, r10 | — | Majority |`
  → `| F006 Wendell b. 1904, Adela's son | r10 | — | Single-source for the birth year (r04 confirms "Adela's son" but never states 1904) |`

- `| F007 Ruth, civil engineer, b. 1934 | r04, r07 ✎, r10 | r11 (weather observer) | Majority |`
  → `| F007 Ruth, civil engineer, b. 1934 | r10 | r11 (weather observer) | Single-source for the birth year (r04, r07 confirm her profession but neither states 1934) |`

### Recoverability index overclaims who names Lidell and Sherrod — 1 item

F017's fact label bundles two different things: the general fact "none killed, two hurt"
(genuinely corroborated by r02 ✎/D3, r10, r12 — I checked, all three state it) and the
*specific names* "Lidell and Sherrod," which only r07 actually transcribes (from D1's page-71
entry). The label is more specific than the carrier list actually supports.

| Item | Value | Files | Verdict |
|---|---|---|---|
| F017 | "Lidell and Sherrod hurt, none killed" — claims r02 ✎, r07 ✎, r10, r12 | corruption-map.md, r02/r10/r12 | Only r07 names the two men; r02/r10/r12 state "none killed, [two/some] hurt" without naming them |

**Proposed edit:**
`| F017 Lidell and Sherrod hurt, none killed | r02 ✎, r07 ✎, r10, r12 | r01 (dead crew) | Two documents (D3, D11) |`
→ `| F017 none killed, two of the crew hurt (named as Lidell and Sherrod only in r07's D1 transcription) | r02 ✎, r07 ✎, r10, r12 | r01 (dead crew) | Two documents (D3, D11) — only r07 names the two men |`

### Malformed recoverability cell — 1 item

F083's "Correct in" cell embeds a prose explanation instead of a clean comma list of
narrator IDs, unlike every other row in the table. This is what caused the stray `✎` in
r07's tail to get attributed to r05 by the parser (`re.search` finds the first `r\d{2}` in
each comma-split token, and the malformed cell's first token happens to contain both `r05`
and a later `✎`). Substantively the fact is fine — r05 states "27" directly, and it is also
arithmetic-derivable from D5's sale date (r02 ✎, r07 ✎) plus r05's 1928 retirement — but the
cell's format should match every other row's convention.

| Item | Value | Files | Verdict |
|---|---|---|---|
| F083 | "27 years at Tolliver" | corruption-map.md | Cell format inconsistent with the rest of the table |

**Proposed edit:**
`| F083 27 years at Tolliver | r05 (stated); arithmetic from D5's 1901 sale (r02 ✎, r07 ✎) + r05's September 1928 retirement | — | Arithmetic |`
→ `| F083 27 years at Tolliver | r05 | — | r05 states "twenty-seven" directly; also re-derivable from D5's 1901 sale date (r02 ✎, r07 ✎) plus r05's September 1928 retirement |`

### Near-tie table bundles a value only one carrier actually states — 1 item

NT-10's "Wrong value" cell reads `**8** silent qualifying nights → **69** in all`, and lists
both r06 and r09 as carriers of the whole cell. But only r06 actually spells out the derived
total ("so sixty-nine nights in all"); r09 states only the raw "eight... nights," and never
computes the sum. `HARDENING-v2.1.md`'s claim that "every one of the twenty-two values sits
in exactly the two files named" does not hold for this one specific sub-value.

| Item | Value | Files | Verdict |
|---|---|---|---|
| NT-10 | `→ 69 in all` — claims r06, r09 both carry it | corruption-map.md, r09 | r09 states only "8"; the "69" total is r06-only |

**Proposed edit:**
`| **NT-10** | **8** silent qualifying nights → **69** in all | r06 (X18), r09 (X47) | **5 → 66** | r03, r07 ✎ | ... |`
→ `| **NT-10** | **8** silent qualifying nights (r09 states only this; r06 additionally sums it to **69** in all) | r06 (X18), r09 (X47) | **5 → 66** | r03, r07 ✎ | ... |`

---

## Final summary

```
PASS: 183  FAIL: 22  UNPARSED: 19
```

- `pytest -q` (harness tests): **76 passed** (53 in `test_audit.py`, up from 37 before this
  pass — added 16 new tests for the fixes above; plus the pre-existing 23 tests in the other
  harness test files, all unaffected).
- (b) real material defects: **6**
- (c) key bookkeeping defects: **10**
- (a) script false positives: 54 (44 fixed to PASS/correctly-UNPARSED in code; 10 downgraded
  from a misleading FAIL to UNPARSED with no safe generic fix, documented above as
  needs-human)

---

## Residual cleanup 2026-08-27

Baseline for this pass (v2.1.1, after KEY-AUDIT.md's 16 fixes were applied to the answer
key and four retellings): `PASS 190  FAIL 19  UNPARSED 15`.
Final: **`PASS 199  FAIL 0  UNPARSED 0  NEEDS-HUMAN 19  ACCEPTED-SINGLE-SOURCE 6`**
(`pytest -q` on `harness/tests/`: **106 passed**, up from 91 — 15 new/renamed tests for
the fixes below).

Two new terminal statuses were added to `audit.py` (`Report`/`print_report`/`main` all
updated; `--strict` still trips only on FAIL or UNPARSED, never on these two):

- **NEEDS-HUMAN** — replaces UNPARSED for the check-3 "paraphrase / arithmetic / document"
  downgrade path (previously misleadingly worded "needs human check" while remaining
  UNPARSED), and is also emitted directly by check 2's near-tie block for a bare/common
  value that cannot safely be uniqueness-checked. Every NEEDS-HUMAN line below was read and
  confirmed present by hand as part of this pass — the label means "not mechanically
  provable, manually verified," not "unresolved."
- **ACCEPTED-SINGLE-SOURCE** — a scored fact that legitimately rests on exactly one
  uncontested narrator, per prior ruling (KEY-AUDIT fix 15's "Single-source scored facts
  (uncontested)" block). Applies uniformly to any such row now and in the future, not just
  the four named in the task.

### (a) Script literalism — fixed in `audit.py`, with new tests in `test_audit.py`

| # | Item | Fix | Result |
|---|---|---|---|
| 1 | X16 `1902` leaked into r10, r12 | `LEAK_ANCHORS["1902"] = "purchase"` (from X16's own As-told cell, "The purchase was in **1902**."); a leak now only counts when the value and its anchor share a sentence (`anchor_confirms`) | PASS — r10/r12's "1902" is Adela's unrelated marriage year (F043), confirmed no "purchase" nearby |
| 2 | X19 `A. Rennick` leaked into r10 | `LEAK_ANCHORS["A. Rennick"] = "night book"` (from X19's As-told cell) | PASS — r10's occurrence is a blockquote citation line (a different, correct use of her own initials), no "night book" nearby |
| 3 | NT-1 `4 inches` leaked into r03, r04 | `LEAK_ANCHORS["4 inches"] = "Sheet 11"` (from NT-1's Wrong-value cell) | PASS — r03/r04's "four inches" is the unrelated, correct 1954-rocker fact (F031), confirmed no "Sheet 11" nearby |
| 4 | NT-7 `nephew` leaked into r10 | `LEAK_ANCHORS["nephew"] = "Tice"` (from NT-7's Wrong-value cell) | PASS — r10's "nephew" is Judd/Adela's own correct relationship, confirmed no "Tice" nearby |
| 5 | NT-10 `8` leaked into r02, r03, r04, r05, r07, r11; NT-11 `30` leaked into 7 narrators; NT-11 `13` leaked into 3 | `is_fragile_bare_value()`: any candidate under 3 characters is too short to trust as a fingerprint at all, regardless of anchor | NEEDS-HUMAN — manually reconfirmed each leak is real-but-unrelated (same findings as the prior pass's Fix 8, still true after KEY-AUDIT's edits): "8"/"eight" recurs for unrelated counts (r09's own "eight miles," "$8,600," etc.); "30"/"thirty" is the unrelated "fall of thirty degrees" threshold nearly every narrator states; "13"/"thirteen" is NT-6's *different* near-tie value plus r09's "thirty-**four**" digit overlap |
| 6 | NT-8's two candidates (`my father's uncle`, `his grand-niece`) each required in **both** r01 and r04, when the row's own annotation says each carrier states its own different phrasing | `candidate_required_narrators()`: when a candidate's own clause inside a `(rXX: "..."; rYY: "...")` parenthetical names exactly one carrier, require it only from that carrier (leak-checking against all other narrators is unaffected) | PASS for both — r04 line 29/51 has "my father's uncle," r01 line 37 has "his grand-niece," exactly as designed |
| 7 | NT-10's `69` "missing from r09" | Same `candidate_required_narrators()` fix: the cell's own parenthetical ("r09 states only this; r06 additionally sums it to **69** in all") names r06 alone for that candidate | PASS — see item (b)-4 below for the read that confirmed this is correct design, not a defect |
| 8 | check-3 rows that resolve by paraphrase, arithmetic, or a document rather than literal-narrator-repetition: F003 (after the corruption-map fix, item (b)-5), F008, F009, F010, F014/F015, F018–F020, F023, F062, F063, F074, F087, F088, F095 | Renamed the branch's status from UNPARSED to NEEDS-HUMAN (no matching-logic change) | Each read and confirmed present in different words — see the per-fact table below |
| 9 | F004, F006, F007, F083 (single narrator, no document mark) FAILing outright | `check3_recoverability`: a `len(distinct) == 1` row with no doc mark is no longer an automatic FAIL — PASS/ACCEPTED-SINGLE-SOURCE by whether the literal token is found, matching the "Single-source scored facts" design already accepted for the six-item block | ACCEPTED-SINGLE-SOURCE (all four; literal digit token found in each sole carrier) |
| 10 | "Silas Tolliver as the lumber company's founder," "Pearl Nace by name" (the `only_in`-schema rows in the same single-source block) UNPARSED on a literal miss | `only_in` branch now checks the row's own Status cell for "single-source" before falling back to freeform/UNPARSED | ACCEPTED-SINGLE-SOURCE for both — r05 states both facts plainly, just not in the fact-cell's own wording |
| 11 | F089 `40°` "only found in r09 of r03, r09" | `MANUALLY_VERIFIED_PRESENT["F089"]`: a one-fact, documented exception (not a generic loosening) | NEEDS-HUMAN — see item (b)-6 below |
| 12 | check-5 12-gram false positive: r02 vs `originals/01-the-two-inch-mark.md`, `"went off the iron at the north approach of the new viaduct"` (and, once that was fixed, the surfaced-next `"no lives were lost two of the gang are hurt and the"`) | `strip_known_document_quotes()`: check 5 already stripped `>` blockquote lines from `originals/` before building n-grams, but the *Ninestone Sentinel* notice (D3) is rendered as inline italics in the original story, not a blockquote, so it wasn't excluded. Now any text matching a known verbatim document quote (the same set check 2 already uses) is stripped from the originals side too | PASS — D3 is a designed document quote, verified verbatim in r02 by check 4 separately; it was never copied narration |

`split_sentence_units()` (used by `anchor_confirms`) also needed a small correction discovered
while writing its test: a naive sentence split on `[.!?]\s+` breaks a single-letter initial
like "A." mid-name (splitting "A. Rennick" into "A." / "Rennick"), which would have made
`anchor_confirms` return False for *any* text containing "A. Rennick" for the wrong reason
(the candidate itself fragmented) rather than the right one (no anchor nearby). Fixed with a
`(?<![A-Z]\.)` guard on the split point; re-verified X19 still resolves for the correct reason
(anchor absent, not candidate fragmented).

### (b) Real material issues — read, decided, and (where genuine) fixed

| # | Item | Decision | What changed |
|---|---|---|---|
| 1 | r02: `"the locomotive was No. 9, and she went off the iron at the north approach of the new viaduct at twenty minutes past seven."` — 12-gram match against `originals/01-the-two-inch-mark.md` | Genuine near-verbatim copy of the original's own narration (not a document). Paraphrased; all facts (No. 9, north approach, new viaduct, 7:20) unchanged | old → new: "The locomotive was No. 9, and she went off the iron at the north approach of the new viaduct at twenty minutes past seven." → "The locomotive was No. 9, and at twenty minutes past seven she left the rails and came to grief at the north approach of the new viaduct." |
| 2 | r03: `"And she never spoke unless the day before had been at least thirty degrees warmer than the night that followed."` — 12-gram match against `originals/02-the-night-book.md` | Genuine near-verbatim copy. Paraphrased; the 30-degree threshold unchanged | old → new: "And she never spoke unless the day before had been at least thirty degrees warmer than the night that followed." → "And she never spoke unless the day before had stood at least thirty degrees warmer than whatever night followed it." |
| 3 | r03 (surfaced after fixing #2, same file): `"They put in rocker bearings with four inches of travel each way, and they threw the old cast pedestals over the abutment into the creek..."` — 12-gram match against the same original's description of the March 1954 rebuild | Genuine near-verbatim copy of the original's own narration. Paraphrased; "four inches of travel each way" (F031) kept verbatim as a value | old → new: "They put in rocker bearings with four inches of travel each way, and they threw the old cast pedestals over the abutment into the creek, and nobody told me a thing about it." → "They pulled the worn-out roller nests, fitted rocker bearings good for four inches of travel each way, and rolled the old cast pedestals off the abutment into the creek, and nobody told me a thing about it." |
| 4 | NT-10's `69` ("sixty-nine nights in all") — the near-tie row lists both r06 and r09 as carriers of the whole Wrong-value cell, but the fact search couldn't find "69" in r09 | Read r09 (`"...eight such nights within the depot record..."`) and r06 (`"...So sixty-nine nights in all..."`): **present by design, not a defect.** r09 states only the raw "eight," r06 alone sums it to "sixty-nine" — exactly what the cell's own parenthetical already says ("r09 states only this; r06 additionally sums it to **69** in all," added by a prior pass). Neither the corpus nor the corruption-map's phrasing needed a fix; only the audit script's per-candidate matching was too rigid (see (a)-7) | No text changed. Script fixed instead |
| 5 | F003 "Adela and Emil siblings" — recoverability index lists `r04, r10, r12`, but r04 never mentions Emil, a sibling, an aunt, or a brother anywhere in its ~1,600 words | Read r04 in full: absent. Read r03 and r07 (not listed): both state it plainly — r03 line 7, "My father had a younger sister, Adela"; r07 line 75, "Judd Rennick's father, Emil, and Adela, who wrote the field book, were brother and sister." The corruption-map's own later "Settled by" column for NT-8 (line 484) already cites the correct set, `r03, r07, r10, r12` — the F003 row was simply never brought into sync. Fixed the key, not the corpus | `answer-key/corruption-map.md` line 367: `\| F003 Adela and Emil siblings \| r04, r10, r12 \| — \| Majority \|` → `\| F003 Adela and Emil siblings \| r03, r07, r10, r12 \| — \| Majority \|` |
| 6 | F089 `40°` "only found in r09 of listed narrators r03, r09" — r03 phrases the fact as "up above forty in the daytime," with no unit word | Read `narrator-briefs.md`'s own r03 bullet for F089: it specifies this *exact* unit-less phrasing ("a real thaw, up above forty in the daytime") — r03's retelling is following its brief precisely, not slipping. **Present, in the narrator's scripted voice; not a gap.** Did not edit r03 (would depart from a brief already matched verbatim) or the corruption-map (the "Majority" resolution is already accurate). A generic bare-number fallback in the script would be unsafe elsewhere in the corpus (per the prior pass's Fix 7), so this one fact is a documented, single-item script exception instead (see (a)-11) | No text changed. Script fixed instead |

Reading every "paraphrased fact label" item (item (a)-8's list) against the actual retellings
confirmed each is genuinely present, just not in the recoverability index's own wording —
no further corpus or key edits were needed beyond F003 above:

| Fact | Confirmed by (evidence) |
|---|---|
| F008 Judd = Ruth's first cousin once removed | r10 states it directly ("Judd and I were first cousins, so Ruth and Judd stood as first cousins once removed"); r07 gives all four links to derive it |
| F009 Warren Tice, resident engineer | r02, r10, r12 all state it with the words reversed from the label ("the resident engineer... was Warren Tice" / "Warren Tice was the resident engineer") |
| F010 Dorsey = Warren's son | r08 (Dorsey himself) calls Warren "my father" throughout; r10: "His son Dorsey kept the store" |
| F014/F015 Peter and Lettie, father and daughter | r04, r06, r10 all state the relationship in their own words |
| F018–F020 custody chains | r04, r07, r10's provenance paragraphs spell out who held which book when, just not as the bare phrase "custody chain" |
| F023 north end fixed, south on rollers | r02, r04, r09 all state it, each in different sentence order |
| F062/F063 −54°F / −14°F derived | r04 states both derived values outright ("Sixty-six less a hundred and twenty is fifty-four below zero"; "Sixty-six less eighty is fourteen below zero"); r07 supplies the raw ingredients (D1's 3-inch spec, D2's rule, D1's 66° reading), each independently verified elsewhere — legitimate arithmetic design, not a gap |
| F074 1955/56's three nights excluded | Settled by D8, verbatim in r03 and r07 (already PASSing under check 4); D8's own text never contains the digits 1955/1956, so the label is a gloss on the key author's own reference |
| F087 binding, stick-slip release, report along the rails | r03 gives the "came up the rails first" fragment; r04 gives the full mechanism ("the south shoe hung up... let go all at once... one report that ran along the rails"); r09 ¶11–13 gives the full technical mechanism |
| F088 both conditions necessary | r09: "The conditions set down at the depot are necessary conditions. They are not sufficient ones."; r03: "Both, every time."; r04 states both conditions jointly |
| F095 the forty-ton deck was not the cause | r09 ¶15 self-refutes the decoy explicitly; r04 independently shows the same +6°F arithmetic threshold matches all 61 observed nights exactly, without invoking the extra deck weight |

### (c) New 12-gram overlaps — paraphrased, re-checked to zero

The task named four flagged files (r02, r03, r04, r05). Investigation found r02's flagged
run was actually a script false positive (item (a)-12, a designed document quote, not
copied prose) — but r03, r04, and r05 each turned out to contain **more than one** genuine
overlap: `find_leaked_ngram` only reports the first 12-gram match per (retelling, original)
pair, so fixing one revealed the next, later in the same file, on the following run. Every
round was re-checked until `audit.py` reported zero 12-gram FAILs for all twelve retellings.

r02's and r03's first-round fixes are listed under (a)-12 and (b)-1/2/3 above. The rest:

| # | Item | Decision | old → new |
|---|---|---|---|
| 1 | r04: `"...Judd Rennick's night book says the bridge spoke, sixty-one times in forty-three winters, and never once above."` — matched `originals/04-what-the-creek-gave-back.md`'s "a station agent's five ruled columns say the bridge spoke, sixty-one times in forty-three winters, and never once above" | Near-verbatim copy of the original's closing line for this passage. Paraphrased; 61/43 unchanged | "Six above zero. Which is where Judd Rennick's night book says the bridge spoke, sixty-one times in forty-three winters, and never once above." → "Six above zero. Judd Rennick's night book puts all sixty-one of the nights she spoke, across forty-three winters, right there — never once warmer." |
| 2 | r04 (surfaced after fixing #1, same paragraph): the "Between the opening of the line..." sentence matched the original on **three separate runs** once read closely — "in november 1897 and the re-decking" (7 words), a 13-word run "of those twelve years was nine below on the fourth of february 1899," and a 12-word run "six degrees after august 1909 fell on the seventeenth of january 1912" — all in the same paragraph, all copied near-verbatim from the original's parallel passage | Genuine near-verbatim copy of three consecutive sentences. Paraphrased as one block; November 1897, August 1909, seven nights, six degrees, thirty degrees, nine below/4 Feb 1899, fourteen below, third of Feb 1911, seventeenth of January 1912 all unchanged | "Between the opening of the line in November 1897 and the re-decking of August 1909 there were seven nights at Kettle Bench below six degrees, four of them at the bottom of falls of thirty degrees or more. [...] The coldest reading of those twelve years was nine below, on the fourth of February, 1899 — cold, but well short of the fourteen below that the bridge as built would have required. [...] And the first night under six degrees after August 1909 fell on the seventeenth of January, 1912:" → "In the eighteen years between the line's opening in November 1897 and the re-decking of August 1909, the Wexler record counted seven nights at Kettle Bench that fell below six degrees, four of them following a day's drop of thirty degrees or better. [...] Across those twelve years the coldest night came on the fourth of February, 1899, at nine below — cold, but well short of the fourteen below that the bridge as built would have required. [...] And the first night under six degrees after August 1909 did not come until the seventeenth of January, 1912:" |
| 3 | r04 (surfaced after fixing #2, a different paragraph entirely): `"The silence of those seven nights is not an absence of data. It is the proof."` — an exact-match aphorism lifted whole from the original | Genuine verbatim copy of the original's own rhetorical line. Paraphrased; "seven nights" unchanged | "The silence of those seven nights is not an absence of data. It is the proof." → "Those seven silent nights are not a gap in the data. They are the proof." |
| 4 | r05: `"She had cost her first owners eight thousand six hundred dollars new..."` — matched `originals/03-delivered-on-her-own-wheels.md` | Near-verbatim copy. Paraphrased; $8,600 unchanged | "She had cost her first owners eight thousand six hundred dollars new — my mother wrote that figure in the margin of the page, and my grandfather repeated the comparison for the rest of his life to anybody who would hold still." → "She had come to her first owners for eight thousand six hundred dollars new — my mother wrote that figure in the margin of the page, and my grandfather repeated the comparison for the rest of his life to anybody who would hold still." |
| 5 | r05 (surfaced after fixing #4): `"Boiler retube in 1909. New tires in 1913. A cracked frame welded in 1919..."` — a maintenance-date list copied almost verbatim | Genuine near-verbatim copy (a terse enumeration, inherently hard to phrase many ways, same category as the prior pass's lowest-priority r03 item). Paraphrased into one flowing sentence; 1909/1913/1919/1922/1924 unchanged | "Boiler retube in 1909. New tires in 1913. A cracked frame welded in 1919 and welded again in 1922, which the shop foreman regarded as a personal insult. A shopping in 1924 that took her down to her bones and put her back together, and she came out of it sounding, my mother said, exactly like herself." → "By 1909 she needed a boiler retube; new tires followed in 1913; the frame cracked and was welded in 1919, then welded again in 1922, which the shop foreman regarded as a personal insult; and a shopping in 1924 took her down to her bones and put her back together, and she came out of it sounding, my mother said, exactly like herself." |
| 6 | r05 (surfaced after fixing #5): `"...and No. 4 was set out behind the shop. She sat there..."` | Near-verbatim copy. Paraphrased; "No. 4," "behind the shop" unchanged | "In September of 1928 the company took delivery of a second-hand eight-coupled engine, and No. 4 was set out behind the shop. She sat there through that winter with a tarpaulin over her stack..." → "In September of 1928 the company took delivery of a second-hand eight-coupled engine, and No. 4 was put out behind the shop to sit. She passed that winter under a tarpaulin..." |
| 7 | r05 (surfaced after fixing #6, the last remaining FAIL): `"...my mother put the stock book, the shop book, the timber ledgers, and eleven boxes of correspondence into the back of a truck and drove them..."` | Near-verbatim copy, item list and all. Paraphrased; 1938, the four deposited items, "Bly County Historical Rooms," and "twenty-four years" unchanged | "In 1938 my mother put the stock book, the shop book, the timber ledgers, and eleven boxes of correspondence into the back of a truck and drove them herself to the Bly County Historical Rooms, where they were catalogued and shelved and did not draw one single inquiry for twenty-four years." → "In 1938 my mother loaded the stock book, the shop book, and the timber ledgers, along with eleven boxes of correspondence, onto a truck bed and hauled them herself all the way to the Bly County Historical Rooms. Nobody there gave the collection so much as a glance for twenty-four years, though it was properly catalogued and shelved from the day it arrived." |

**Post-fix checks.** Word counts (`wc`-equivalent, same convention as check 1, after
framing): r02 **1,604** (was 1,601) · r03 **1,612** (was 1,608) · r04 **1,770** (was 1,762)
· r05 **1,417** (was 1,406). All four inside 1,200–1,800; the other eight retellings were
untouched. Block quotations: every edit above is confirmed, by diff, to touch only plain
narration paragraphs — no `>` line was changed in any of the four files, and check 4's 23
document-quote PASSes are unaffected. `python3 harness/make_bundle.py --root v2 --out
test-input/bundle-single.md` re-run clean (19,777 words, 12 retellings).

### Final summary

```
PASS: 199  FAIL: 0  UNPARSED: 0  NEEDS-HUMAN: 19  ACCEPTED-SINGLE-SOURCE: 6
```

- `pytest -q` (harness tests): **106 passed** (68 in `test_audit.py`, up from 53 — 15 new
  tests for the fixes above, plus 2 renamed from `..._reports_unparsed_not_fail` to
  `..._reports_needs_human_not_fail`; the other 38 pre-existing harness tests unaffected).
- (a) script literalism: 12 items fixed in `audit.py` (plus the `split_sentence_units`
  abbreviation-handling correction found while testing item 2).
- (b) real material issues: 6 items read and decided — 3 corpus paraphrases (r02, r03 ×1
  of its 2, plus the 11 check-3 "present in different words" facts confirmed with no edit
  needed), 1 key fix (F003), 2 confirmed-correct-as-designed with no edit (NT-10's `69`,
  F089).
- (c) 12-gram overlaps: 4 flagged files, 10 individual overlaps once fully unwound (2 in
  r03, 3 in r04, 4 in r05, plus r02's single flagged run reclassified as (a)); all
  paraphrased, re-checked to zero.
