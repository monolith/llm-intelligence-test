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
