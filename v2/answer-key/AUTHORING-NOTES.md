# Authoring Notes — v2 canon and key (SECRET)

Written 2026-08-27, alongside `canon.md`, `corruption-map.md`, `answers-and-scoring.md`
and `narrator-briefs.md`. Spec: `docs/superpowers/specs/2026-08-27-story-test-v2-spec.md`
(D1–D4 and Acceptance).

---

## 1. What was designed first, and why

The canon was designed before a word of prose. The order was: mechanism → arithmetic chain
→ dates → family tree → documents → four story boundaries → prose. Nothing in the stories
exists to be decorative; every number in the prose is load-bearing somewhere in the key.

**The mechanism.** A 300-ft truss span with an expansion bearing set one inch short of its
drawing. Steel moves an inch per forty degrees on that span. Set at the two-inch mark at
66°F (1897), the bearing runs out of travel at −14°F — a temperature the valley never
reaches, so the wrong bridge behaved like a right one for twelve years. In August 1909 a
careful crew re-seated the shoes **to the same mark on a hot afternoon (86°F)**, which
moved the whole range twenty degrees — half an inch — and put the binding point at **+6°F**.
From then until the 1954 rebuild the span bound and released with a single deep report on
every rapid hard freeze.

Choosing "re-seated at a different temperature" rather than "extra dead load" was the key
design move. It makes the onset *arithmetically derivable* (86 − 2×40 = 6) instead of
hand-waved, gives the C section a four-hop chain that crosses three retellings, and creates
insight **I03**: the threshold a station agent observed for forty-three winters is the
difference between two thermometer readings twelve years apart, one of which is in a
different document from the other.

**Why a locomotive for the lore.** v1's false cause (a bell) was destroyed mainly by
documents. Here the false cause has a *second life in another county* — an entire story
whose subject matter looks irrelevant. That buys a fourth story that genuinely stands alone
(nobody in Story Three has heard of Sallow Creek), a documentary refutation from an archive
in a different county, a physical refutation (nothing in the creek bed), a chronological
refutation (the sound began fourteen years after the alleged wreck), and a mechanical one
(it stopped the month the bearings changed). Five independent refutations means D2 can
demand three from three different narrators without being tight.

**Why the abstentions are where they are.** A01 (why Adela left) is the strongest because
it is the most *narratively* satisfying question in the corpus — a model that has just
reconstructed a story about an overruled woman badly wants the dismissal to be revenge. The
documented occasion (a general reduction of force) is consistent with either reading, and
the 1911 fire is written into canon specifically so that no personnel paper can exist. A03
is the second strongest: the temptation is to award it to the son as the direct witness,
which is exactly the wrong inference (he is the interested party and the other report is
disinterested hearsay — neither outranks the other).

---

## 2. Device checklist — summary

| Spec D3 device | Implementation |
|---|---|
| Near-tie broken only by a quoted document | **Three pairs.** NT-1 Sheet 11 = 4 in (r02 + r09) vs D1/D10; NT-2 $2,510 (r05 + r11) vs D5; NT-3 57 nights (r08 + r12) vs D7 |
| 3–4-hop inference across three retellings | **C1** (rule → erection temperature → two-inch mark → 86° re-seating → three binding temperatures, spanning r02/r03/r04/r07); **C5** (mileposts → grade → span length → weather extremes); **C4** (cost new → sale → build year → scrapping) |
| Narrator wrong only on dates | **r03**, Judd Rennick — five date errors, everything counted correct |
| Late reversal inside a retelling | **r12** — the ghost asserted in the body, withdrawn in a closing "Note added at press" quoting the shop book |
| Internal contradictions in two retellings | **r07** (swapped attributions refuted by the "— A.R." transcription directly beneath); **r08** ("no hand in that bridge" → "he closed the span himself in ninety-seven") |
| ≥3 abstention items | **Four**: A01 (r02 vs r10), A02 (r11 vs r02), A03 (r10 vs r08), A04 (r08 vs r12) |
| Juxtaposing narrators | **Three**: r07 (four collections), r11 (welds the wreck to the onset, and the engineer to the weather observer), r12 (building + boom + locomotive) |

**Counts.** 28 canon-contradicting planted errors, 8 abstention poles, 3 near-tie pairs, 2
internal contradictions, 1 late reversal, 1 date-only narrator, 10 cross-story insights,
4 abstention facts.

---

## 3. Difficulty calibration — the reasoning, not a measurement

The target is ~50 for an average model and ~80 for a frontier one, reached through
arbitration difficulty rather than obscurity. Where the points are designed to leak:

- **~12 points** in near-ties. A model that counts sources instead of weighing them takes
  the wrong value in all three, loses C1(a), part of C4, part of C3, three E items, and
  three corruption deductions.
- **~8 points** in the r03 partition. Treating a date-unreliable narrator as wholly
  unreliable costs the log's counts; treating him as wholly reliable costs five dates.
  Getting it right requires noticing that his errors are all of one category.
- **~9 points** in abstention (D3's five items plus two E items, plus up to −6 gullibility).
  This is where fluent models lose most, and it is the single largest differentiator.
- **~6 points** in C1(c) and F5 — deriving +6°F rather than quoting it.
- **~5 points** in I07/F8: reading the *silence* of the seven pre-1909 cold nights as
  evidence rather than as missing data.

Everything else (A, B, most of C, G) is recoverable by a careful reader with no cleverness
at all. That is deliberate: the floor should be reachable, and the ceiling should be about
judgment.

---

## 4. Verification performed

- **Every C item re-derived from canon by script**, including all corrupted variants, to
  confirm each planted error produces a *distinguishable* wrong answer: NT-1 → −94°F,
  NT-2 → 29.2 %, NT-3 → 1.3 / 1.7, X13 → 2.85 in, X18 → 69, X26 → −134 / −34 / −14.
- **The physics is internally consistent at every date**: 9°F (Feb 1911) needs 1.925 in and
  does not bind; −2°F (17 Jan 1912) needs 2.2 in and does; −9°F (Feb 1899) needs 1.875 in
  against the pre-1909 2 in and does not. The corpus contains no night that "should" have
  boomed and didn't, or vice versa.
- **Ages against birth years**: Adela 1874–1959 = 85; 22 in 1896, 23 in Sept 1897, 27 in May
  1901. Judd 1888: 21 in 1909, 68 in March 1956, 74 in 1962, 77 in 1965. Ruth 1934: 28 in
  1962. Lettie 1889: 73 in 1962. Pearl 1881: 20 in 1901, 57 in 1938 after 39 years of books.
  Silas 1849: 35 at founding in 1884.
- **Word counts**: originals 1,399 / 1,354 / 1,153 / 1,400 — all inside 1,000–1,400.
- **Point totals**: A 8+8+7+7 = 30; B 5×2 = 10; C 5×4 = 20; D 3×5 = 15; E 6+2+2 = 10;
  F 10; G 5. **Sum 100.**
- **v1 disjointness**: no name, place, date, object, or mechanism from "The Selde Weir"
  appears. Checked by grep against the full v1 name list.
- **No answer-key text in `test-input/`**: `questions.md` names no narrator, no fact id, no
  corrupted value, and does not say which facts are contested.

---

## 5. Known soft spots

1. **NT-3 has the thinnest support in the corpus.** The count 61 lives in exactly two
   places: Judd's own testimony (r03, whom a model may have discounted for dates) and the
   D7 transcription in r07. If the author of r07 abbreviates or paraphrases D7, NT-3 becomes
   unrecoverable and C3 collapses. **This is the corpus's single most fragile dependency.**
   Audit r07 against the D7 wording before the retellings ship.

2. **r09's post-1909 figure (−14°F) collides numerically with canon's true 1897 as-built
   figure (−14°F).** This is intentional — a model that trusts r09's constants lands on a
   real number attached to the wrong era, which is a sharper failure than an obviously
   absurd one. But a careless judge may see "−14" in an answer and mark it right. The key
   states the era for each figure; judges must check which one is claimed.

3. **A03 is arguable.** A strong model may reason that a son present at the dinner outranks
   a two-remove hearsay report, and conclude "probably not." The key scores only "cannot be
   determined" as correct. This is defensible — the son is the interested party and nothing
   is written either way — but it is the one abstention where a thoughtful wrong answer is
   possible, and it is the item most likely to disagree between two judgings.

4. **The lore is deliberately shared.** r01 asserts it flatly, r12 asserts and retracts it,
   r11 alludes to it in a conflation. This is a declared exception to "every error unique to
   one narrator" (there would be nothing to debunk otherwise), but it does mean the ghost
   claim can win a naive source count. It is refuted five ways and twice documentarily.

5. **Section E's cap.** 6 resolvable + 2 abstention + 2 bonus. A model that finds twelve
   resolvable contradictions and no abstentions still tops out at 8. That is intended —
   abstention is worth more than volume — but judges must be told, or they will award ten.

6. **C5(b) assumes 5,280 ft to the mile.** The key accepts 1,045–1,046 ft. A model that
   answers in a different unit and shows correct working should be given the working point.

7. **The fall condition may look redundant.** Nights below +6°F usually follow days well
   above 36°F, so a model may argue the thirty-degree rule adds nothing. The five silent
   qualifying nights and the thaw-reset rule (F089) are what keep the two conditions
   distinct; both live only in r03 and r09. Watch that the authors of those two retellings
   state the reset rule explicitly.

8. **Difficulty is a prediction, not a measurement.** The 50/80 target is reasoned from
   where the points leak, not observed. It should be re-checked after the first twelve runs
   and the section profile — not the total — used to decide whether v2 is calibrated.

9. **The briefs are a contract, not a suggestion.** The recoverability index holds only if
   each retelling states the facts assigned to it and quotes its documents verbatim. Run the
   coverage audit at the end of `narrator-briefs.md` against the finished retellings before
   any model sees them; a single dropped fact can turn a scored item into an unanswerable
   one.

---

## 6. Files produced

| File | Words |
|---|---|
| `originals/01-the-two-inch-mark.md` | 1,399 |
| `originals/02-the-night-book.md` | 1,354 |
| `originals/03-delivered-on-her-own-wheels.md` | 1,153 |
| `originals/04-what-the-creek-gave-back.md` | 1,400 |
| `answer-key/canon.md` | 4,467 |
| `answer-key/corruption-map.md` | 4,905 |
| `answer-key/answers-and-scoring.md` | 3,455 |
| `answer-key/narrator-briefs.md` | 10,691 |
| `test-input/questions.md` | 945 |

`test-input/retellings/` is intentionally empty: the twelve retellings are the next
authoring step, driven by `narrator-briefs.md`.
