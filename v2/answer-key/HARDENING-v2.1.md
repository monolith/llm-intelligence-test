# HARDENING v2.1 — record of changes (SECRET)

Written 2026-08-27, after a careful single-pass blind solve by a frontier model scored
**94/100** (A 28, B 10, C 20, D 14, E 10, F 10, G 4, one −2 gullibility deduction). The
owner's target is ~50 for an average model and ~80 for the strongest, so the ceiling had to
come down — **through arbitration difficulty only**, never through obscurity, trick wording,
or items a careful human could not settle from the retellings alone.

Two things were done at once, and they pull in opposite directions:

1. **The eight key defects the judge surfaced were fixed.** Four of them were costing the
   solver points unfairly (D3's collision with its own evidence, A2.4 penalizing obedience,
   A4.7 bundling an epilogue, G2 packing two requirements into one point). Fixing them
   *raises* a good solver's score by roughly 3 points.
2. **The corpus and the key were hardened.** Eight new near-tie pairs, two new abstention
   items, a decoy theory, two more three-retelling chains, an off-by-one trap, and a
   re-bucketed Section E.

So the hardening had to buy back the ~3 points the fixes gave away before it bought anything
at all. See § 4 for the honest arithmetic on where that lands.

Nothing in the constraints was violated: still twelve retellings, every retelling under 1,800
words, every existing verbatim document quote unchanged, the 100-point structure intact, no
item depending on outside knowledge.

---

## 1. Change list

Lever key: **L1** near-ties · **L2** longer chains · **L3** decoy theory · **L4** abstention ·
**L5** Section A trimming · **F#** one of the eight judge-surfaced fixes.

### 1.1 Near-tie conversions (L1) — eight new pairs

Each row converts a fact that stood 3–4 correct against 1 wrong into a **2-vs-2** tie. In
every case the correct value survives in exactly two narrators and the wrong value in exactly
two others, and the breaker is a quoted document, arithmetic, or one narrator's internal
consistency. Verified by grep after the edits: every one of the twenty-two values sits in
exactly the two files named.

| Pair | Fact | Wrong now carried by | Breaker | Files edited | old → new |
|---|---|---|---|---|---|
| **NT-4** | Viaduct length **540 ft** | r11, r12 | arithmetic: 120 + 300 + 120, both components and total in r02 and r09 | r11, r12 | r11: "the long shadow of the viaduct lying across" → "the long shadow of the viaduct — **six hundred feet of it, ninety-seven feet up** — lying across". r12: "…took a year and a half to build." → "…to build. **It is six hundred feet long and it stands ninety-seven feet above the water.**" |
| **NT-5** | Movement rule **1 in / 300 ft / 40°** | r02, r09 | D2 quoted verbatim in r04 and r07; and only 40 yields the +6°F the night book records 61 times | r02 | "for forty degrees… an inch for every forty degrees" → "for **fifty** degrees… an inch for every **fifty** degrees" |
| **NT-6** | Record low **−11°F** | r04, r11 | r06 the keeper, and r07 "from the depositor's own index sheet" | r11 | "…in the winter of 1918." → "…in the winter of 1918, **which was the hardest winter the valley has on paper: thirteen below zero up at Kettle Bench**, and nothing since has come near it." |
| **NT-7** | Dorsey Tice = Warren's **son** | r01, r12 | Dorsey's own testimony ("my father", "he took me out on the deck") + r10 | r12 | "whose son Dorsey keeps the store today" → "whose **nephew** Dorsey keeps the store today" |
| **NT-8** | Judd = Ruth's **first cousin once removed** | r01, r04 | derivation: r03/r07/r10/r12 give every link; r10 states the conclusion and names the courtesy title as the cause of the error | r01 | added: "**She was his grand-niece, they told me**, come to look at his book, and he let her have it." |
| **NT-9** | Adela born **1874** | r07, r10 | arithmetic inside a wrong-value carrier: r10's own "died in 1959, at eighty-five" | r07 | "the granddaughter of the writer of the field book." → "…of the field book, **Adela Rennick, born 1876 and died 1959**." |
| **NT-10** | **5** silent qualifying nights → **66** | r06, r09 | D7 verbatim in r07; r03 its author | r04, r09 | r04: "**Five** further nights answered both conditions and produced nothing at all." → "Further nights answered both conditions and produced nothing at all, and his own summing at the back of the book gives the count of them." r09 ¶14: added "— **eight such nights** within the depot record, as the writer has it at second hand —" |
| **NT-11** | **34** boom winters / **9** blank | r08, r12 | D7 verbatim in r07; r03 its author. The wrong pair closes against 43 (30 + 13), so arithmetic alone will not break it | r08, r12 | r08: added "**Thirty winters she spoke in and thirteen she never opened her mouth at all** — thirty and thirteen, and there is your forty-three." r12: added "**In thirty of those winters** the bridge spoke at least once; **in thirteen** of them it never spoke at all." |

NT-1 (Sheet 11 = 3 in) and NT-2 ($2,150) are unchanged from v2.0. NT-3 (61 nights) remains
document-plus-majority and is labelled as such; converting it would have required stripping
61 out of r04's derivation, which would gut her talk.

One further fact was made 2-vs-1 rather than 2-vs-2 (**L5**): the death test, 190 / 7,
previously uncontested. r08 now garbles it — "better than a third of the burying in this town
came inside the week" — against r03 the counter and r12.

### 1.2 Longer chains and traps (L2)

| Item | What it now requires | Files edited | old → new |
|---|---|---|---|
| **C5(b)** — fall from quarry to viaduct | Three retellings: mileposts (r02), grade 2.2 % (r02, r09), and the **nine miles** now stated only by **r03, the date-unreliable narrator** — against r09's "eight miles," printed in the same sentence as its own mileposts 31 and 22. Plus the 5,280 ft conversion. r09's figure yields 929.28 ft. | r02, r09 | r02: "two and two-tenths percent, **and there were nine miles of it**" → "…percent, and it held at that the whole way"; and "Two and two-tenths percent **for nine miles**" → "…**held all that distance**". r09 ¶3: "maintained over **nine** miles" → "over **eight** miles" |
| **C3** — the night book's averages | Three retellings plus two documents: 61 (D7, r03, r04, r06), 34/9 (D7, r03 — contested by r08 + r12), 5/66 (D7, r03 — contested by r06 + r09), and the March 1954 rebuild (r02, r07, r09, r11, r12 — **r03 wrong at 1953**). The solver must keep r03's counts and discard his years. | key only | C3(d) now also requires **fixing the span of the count** (1911/12–1953/54) from the 17 Jan 1912 onset, the 9 Feb 1954 last night, and 1954 − 1912 + 1 = 43. r03's 1913 yields 42 |
| **B4** — Dorsey's father and January 1936 | Three retellings: r08's own parentage (against NT-7), D1's "W.T." in r04/r07 plus r02/r10 naming Warren Tice resident engineer, Judd as Adela's nephew in r03/r10, and the wager year from r08/r12 — **keeping r03's wager figures while discarding his 1937** | key only | significance point now explicitly requires the correct year |
| **C1** | unchanged in structure, but now runs through two near-ties (NT-1 and NT-5) instead of one | key only | diagnostics table added: 4 in alone → −94; 50° alone → −84/−34/−14; both → −134/−34/−14 |

**Off-by-one and unit traps the key resolves explicitly:** r09's eight miles against its own
mileposts; the miles→feet conversion; the 43-winter span; and the **two roads to 69** (61 + 8
from NT-10, or 66 + 3 from folding in the post-rebuild nights) — the key distinguishes them,
because the first loses C3(b) and the second loses C3(d) and trips A06.

### 1.3 The decoy theory (L3)

**The claim.** The deck renewed in August 1909 was forty tons heavier; the added dead load,
not the re-seating, is what made the bearing bind.

**Why it is a good decoy.** It fits the onset date, the cessation (new bearings in 1954), the
cold, the rapid fall, the single report, and the silence after a release. It is offered by
the corpus's two most authoritative-sounding voices on engineering matters, in both cases
flagged as opinion, and never hedged.

**Seeded in two narrators.**

- **r02**, after the re-decking paragraph: *"Forty tons is forty tons. A nest of rollers under
  a bridge was never meant to carry what that new deck put upon it, and the noise the Falls
  made so much of began somewhere about that time and not before it. I say the weight did it.
  I have no drawing to show you and I do not need one…"*
- **r09**, appended to ¶10: *"…It is at least as probable that the added dead load, rather
  than any question of travel, was what brought the bearing to bind; and the date at which
  the local tradition is said to begin is consistent with the re-decking and with nothing
  else in the record."*

**Refuted by one document and one arithmetic fact**, exactly as specified:

- **Record.** r09 ¶15, three paragraphs later and unconnected by its author: *"The deck of
  1909 was not disturbed in that work and stands over the span today; nothing was altered in
  March 1954 but the bearings themselves."* A load cause therefore predicts the sound
  continuing after March 1954. It stopped that month and never returned.
- **Arithmetic.** 86 − (2 × 40) = +6°F, matching 61 logged nights and never once exceeded.
  Added dead load fixes no temperature at all, and cannot say why the number moved from −14
  to +6 rather than anywhere else.

**Scored** at **F7** (names the competing explanation and rejects it) and **F8** (gives a
reason that actually defeats it — either refutation earns the point; "unnecessary" without
evidence does not). To keep this fair rather than a gotcha, `questions.md` F1 now says the
theory "must also **name the competing explanation that the sources themselves offer for the
onset, and say why it fails**."

To make room, F was re-cut from eleven candidate items to ten: old F1 + F2 merged (names the
bearing **and** the one-inch shortfall) and old F3 + F4 merged (binds and releases in one
stroke **and** the report runs along the rails).

### 1.4 Abstention: four items → six (L4)

Both new items are **dressed as ordinary factual questions** — a start year and a count —
and both have an apparent majority answer that dissolves on inspection.

**A05 — In what year was the Kettle Bench weather record begun?**
r06, the keeper, says **1884** and supports it twice from her own text. r04 and r07 both give
**1 January 1894** — and both now say where they got it. The 2-vs-1 majority is an illusion:
both 1894 sources cite Lettie Wexler, who is r06. One witness contradicting herself, and no
page of the record earlier than 1894 quoted anywhere.
*Files:* r04 — "…every day — since the first of January, 1894." → "…every day. **Miss Wexler
puts the beginning of it at the first of January, 1894, and I have used her date.**" r07 Item
3 — "kept at the Wexler farm… **from 1 January 1894**." → "…at the Wexler farm… **The
depositor's own index sheet gives the beginning of the record as 1 January 1894, and I have
entered that date on the authority of the sheet, having no other.**"
*Consequence:* 1884 is **removed from the corruption-deduction list** (it is a pole now, not
an error), the A4.6 checklist no longer requires the start year, and asserting **either**
year triggers the gullibility deduction.

**A06 — How many nights met both conditions in the two winters after the March 1954 rebuild?**
D8 gives **three** for the *second* winter (1955/56) and asserts silence for *both*; it gives
no figure for 1954/55, and nothing else in the corpus does. r09 and r12 both state three as
the two-winter total.
*Files:* r09 ¶15 — added "**Three nights in the two winters following the work are reported to
have answered both conditions**, no sound being heard upon any of them." r12 ch. IV — added
"**Three nights in the two winters that followed answered every condition the book lays
down**, and the bridge said nothing on any of them."
*Consequence:* A2.8 now requires "three qualifying nights **recorded for the second winter
(1955/56)**." Stating three as a two-winter total loses A2.8 **and** takes −2.

**A01 rebalanced with a thirteenth document (also fix F1).** In v2.0 the key told the grader
that D4's "reduced entire" was genuine evidence against the punitive reading while still
requiring abstention — an unfair item, and the one the 94 run was penalized on. The corpus now
carries a counterweight, **D13**, a printed CVR notice of 20 July 1901 folded inside the
reduction letter: *"Notice. Re-engaged from the 1st August next for the Ashby extension:
J. Corliss, rodman; F. Wain, chainman. — Cadder Valley Railroad, 20 July 1901."* Two of the
same party taken back, and she not among them. It removes "reduced entire, and nothing else"
as a settling argument without supplying a motive — both re-engaged posts were field posts,
and the road never employed a computer again.
*Files:* r07 (the document plus three flat, non-inferential curator observations); r02 (reads
it as proof of the grudge: "…and I have never needed anybody to explain that to me"); r10
(raises it himself and answers it: "That is true and it proves nothing").
*Key:* D3 item 3 now requires the notice; the grader note is rewritten so that **both**
readings — retaliation and "the reduction settles it" — score 0 and take −2.

**Gullibility maximum raised from −8 to −12** (six items at −2).

### 1.5 Section A trimmed and re-pointed (L5)

| Item | Was | Now | Why |
|---|---|---|---|
| A1.1 | Adela's role — uncontested by every narrator | role **plus b. 1874** | replaces a universal-agreement fact with a 2-vs-2 (NT-9) |
| A1.2 | 540 / 97 / April 1896, uncontested | same, but **540 is now contested 2-vs-2** (NT-4) | as above |
| A1.6 | rule contested 3-vs-1 | contested **2-vs-2** (NT-5) | as above |
| A1.7 | bundled the 1898 runaway **and** the 1901 sale — the sale is scored again at A3.3 | the **14 November 1897 opening** and the runaway; the sale lives only in A3 | fix F2: removes the double-count the judge flagged |
| A2.4 | required the answer to carry the false lore, while `questions.md` told solvers to drop rejected facts | the **A2 question now asks what the valley believed and where the belief came from**; the item credits the belief wherever it appears in Section A | fix F3: stopped penalizing obedience |
| A2.6 | 61 / 34 / 9 / 5 / 66, one contested figure | **three** contested figures (NT-3, NT-10, NT-11) in one item | L1 |
| A2.7 | 190 / 7 uncontested | contested by r08 | L5 |
| A2.8 | "three silent qualifying nights in 1955/56" | "**three** qualifying nights **recorded for the second winter (1955/56)**" | L4 / A06 |
| A4.1 | gated on "(b. 1934)" | birth year explicitly not required | fix F5 |
| A4.6 | gated on "kept from 1 January 1894" | start year explicitly not required | fix F5 + A05 |
| A4.7 | bundled the photostats **and** the 1963/1967/1969 deposits | photostats only; deposits scored in **B5** | fix F4 |

### 1.6 The eight judge-surfaced defects — disposition

| # | Defect | Fixed how |
|---|---|---|
| 1 | D3/A01: the key required abstention while telling the grader the evidence pointed one way | **D13** added to the corpus; both readings now score 0 and −2; grader note rewritten |
| 2 | No Section A scope rule; A1.7 double-counted the sale | Scope rule stated in the key **and** in `questions.md`; the sale removed from A1.7 |
| 3 | A2.4 penalized keeping refuted lore out of a factual narrative | A2's question now asks for the belief explicitly |
| 4 | A4.7 bundled the survey's finding with a post-survey epilogue | Deposits moved to B5 |
| 5 | Compound items with unmarked load-bearing parts (κ risk) | New "How to read a checklist item" section: **bold gates the point, unbolded parentheticals do not**; every load-bearing sub-fact bolded |
| 6 | E row 11 (1884 vs 1894) was the key's weakest "resolvable" call | Promoted to **abstention item A05**, with the corpus edited so both 1894 sources name the 1884 witness as their authority |
| 7 | The Section E cap made the section insensitive | E re-bucketed: **E-a ordinary conflicts max 3 · E-b near-ties correctly broken max 3 · E-c abstentions max 3 · E-d self-refutation +1**. Near-tie credit requires saying *two narrators carry the wrong value* and naming the breaker |
| 8 | G2 packed "four strands" and "the family link" into one point under a 120-word cap | Split: G2 = the four record-strands, G3 = names Adela, Judd and Ruth (kinship words not required); G4 now carries both ends of the arc |

---

## 2. New device counts

| Device | v2.0 | v2.1 |
|---|---|---|
| Near-tie pairs | 3 (one of them not a true tie) | **11** (NT-3 still document-plus-majority) |
| — broken by a quoted document | 3 | 6 (NT-1, NT-2, NT-5, NT-6, NT-10, NT-11) |
| — broken by arithmetic | 0 | 2 (NT-4, NT-9) |
| — broken by derivation or direct testimony | 0 | 2 (NT-8, NT-7) |
| Abstention items | 4 | **6** |
| Abstention poles | 8 | **15** |
| Planted entries contradicting canon | 28 | **41** (39 fact errors + 2 decoy poles) |
| Decoy theories | 0 | **1**, in two narrators, refuted by one record + one arithmetic fact |
| Internal contradictions | 2 (r07, r08) | **5** (r07, r08, r09 ×2, r03, r10) |
| Verbatim documents | 12 | **13** (D13 added) |
| Three-retelling chains | 3 (C1, C4, C5) | **5** (C1, C3, C4, C5(b), B4) |
| Unit / off-by-one traps | 1 (implicit) | **4**, all resolved explicitly in the key |
| Gullibility maximum | −8 | **−12** |
| Section E buckets | 2 (+bonus) | **4**, each separately capped |

Word counts after editing (cap 1,800): r01 **1,582** · r02 **1,642** · r03 1,638 *(unedited)* ·
r04 **1,795** · r05 1,453 *(unedited)* · r06 1,368 *(unedited)* · r07 **1,626** · r08 **1,425** ·
r09 **1,626** · r10 **1,482** · r11 **1,382** · r12 **1,584**.

r03, r05 and r06 were deliberately left alone: r03 is the date-partition device and any
non-date error in him breaks it; r05 already carries two errors and four of the corpus's six
single-source facts; r06 needed only reclassification, not new text.

---

## 3. Verification performed

- **Every verbatim document quote machine-compared against `canon.md` after the edits.** All
  twenty-two pre-existing block quotes still match exactly. The only unmatched blocks are the
  new D13 slip and r07's Item 4 pedestal card, which was never a D-document.
- **Carrier uniqueness verified by grep across all twelve files.** Each of the twenty-two
  near-tie values sits in exactly the two narrators named; each single-narrator error sits in
  exactly one. Correct values verified present in exactly the two (or four, for NT-3)
  narrators the key names.
- **Every C item re-derived by hand.** C1: 66 − 120 = −54; 66 − 80 = −14; 86 − 80 = +6;
  86 − 66 = 20 (= 6 − (−14)). C2: 38 − 6 = 32, ÷ 4 = 8 h → midnight; 41 − (−3) = 44 ≥ 30.
  C3: 61 ÷ 43 = 1.4186 → 1.4; 61 + 5 = 66; 61 ÷ 34 = 1.7941 → 1.8; span 1911/12–1953/54.
  C4: 1929 − 1889 = 40; 2,150 ÷ 8,600 = 0.25 exactly; 1901 → Sept 1928 = 27.
  C5: 540; 9 × 5,280 = 47,520 × 0.022 = 1,045.44; 112 ÷ 40 = 2.8.
  Wrong-path values recomputed and confirmed distinguishable: −94 / −84 / −134 / −34 / −14 ·
  1.3 / 1.9 / 2.0 · 62 / 65 / 69 · 29.2 % · 600 · 929.28 · 2.85 · 2.24.
- **Recoverability re-checked for every scored fact**: ≥2 narrators, or a document, or
  arithmetic. The six single-source facts are unchanged and none is required by a scored item
  any more except through A3 (four of them rest on r05, which remains the fragility to watch).
- **Point sum**: A 30 (8+8+7+7) · B 10 (5 × 2) · C 20 (5 × 4) · D 15 (3 × 5) ·
  E 10 (3+3+3+1) · F 10 · G 5 = **100**.
- **Leak check on `test-input/`**: no occurrence of "near-tie", "abstention", "corruption",
  "canon", "planted", any `F0nn` id, any `Xnn` id, or `⌀`. The questions name no narrator and
  no contested value.

---

## 4. Expected point leakage, and where it comes from

This is reasoning, not measurement. The reference case is the 94-scoring run, re-scored
against the v2.1 key.

**Start from a corrected ceiling.** The four fairness fixes hand that run back about 3 points
(A2.4 +1, A4.7 +1, G +1), so its uncorrected ceiling is ~97.

| Section | v2.0 | Expected v2.1 | Reasoning |
|---|---|---|---|
| **A** (30) | 28 | **27–28** | +2 from fixes F3/F4. Against that: **A2.8** now fails for that run as written — it said "three qualifying nights in the two winters after," which is exactly A06's assertion (−1 item, and −2 in deductions). A1.1/A1.2/A1.6/A2.6/A2.7 each now gate on a contested value; a careful solver breaks most, but five gated items across eleven pairs make one slip likely (−1). |
| **B** (10) | 10 | **9–10** | B1 now gates on a 2-vs-2 birth year, B3 on a 2-vs-2 kinship, B4 on a 2-vs-2 parentage whose old resolution ("rejected 3-to-1") no longer works. The run resolved all three correctly elsewhere in its sheet, so most likely 10; one slip costs 1. |
| **C** (20) | 20 | **17–19** | C5(b) is the real exposure: the run wrote "stated directly as nine miles by r02, r03 and r09," and r02 no longer says it while r09 now says eight. Taking the technical memo's figure costs 2. C3(d) now also requires fixing the span of the count (−0 to −1). C1 and C5(c) each ride two near-ties. |
| **D** (15) | 14 | **10–15** | D3 is the largest single swing in the test. The run answered "No — the letter says so plainly." With D13 present that is an assertion against contrary evidence: 0 on five checklist items and −2. If the run instead abstains, it takes all 5. Expected value about 12. D2's new item 5 (independence, and one reason standing without the 1962 survey) costs about 0.5. |
| **E** (10) | 10 | **9–10** | The run found ~18 conflicts, flagged its own "two narrators agree on something a document contradicts" list, declined five abstention-shaped questions, and named four self-refutations. It should still fill all four buckets. The re-bucketing bites weaker sheets, not this one. |
| **F** (10) | 10 | **8–10** | F7 and F8 are new. The question now names the requirement, so a strong solver will address it; F8 demands a specific defeater rather than a shrug. Expect one of the two to slip about a third of the time. |
| **G** (5) | 4 | **5** | Fix F8. |
| **Deductions** | −2 | **−3 to −7** | A06 is very likely asserted (the run already phrased it that way): −2. A01 −2 with probability ~0.4. The decoy risks a −1 corruption deduction if half-adopted. Others near zero for this run. |

**Expected total for this particular solver: 84–88, most likely ~86.** For a frontier
single pass that is *less* disciplined about abstention than this run was — and this run was
an outlier, declining five abstention-shaped questions unprompted, three of which the v2.0 key
did not even ask for — expect **78–85**. For an average model, the near-tie density does most
of the work: eleven pairs, each costing an item plus a corruption deduction and several of
them cascading into C, put the expected score at **46–58**.

**Honest assessment: I got roughly 8–11 points of the requested ~15 against the strongest
solver.** The average-model target (~50) looks met with room. The strong-model target (~80)
is approached but probably not reached by this pass; ~86 is my central estimate, not 79. The
remaining gap is discussed in § 5.

**Cascade table — what one swallowed pair now costs**, which is why the leakage is
front-loaded rather than spread:

| Pair swallowed | Items lost |
|---|---|
| NT-5 (50°) | A1.6, C1(a)(b)(c), C5(c), E-b credit, −1 corruption = **~7** |
| NT-1 (4 in) | A1.3, C1(a), E-b, −1 = **~4** |
| NT-10 (8/69) | A2.6, C3(b), usually C3(d), E-b, −1 = **~5** |
| NT-11 (30/13) | A2.6 (if not already lost), C3(c), E-b, −1 = **~4** |
| NT-3 (57) | A2.6, C3(a), C3(c), E-b, −1 = **~5** |
| NT-2 ($2,510) | A3.3, C4(b), E-b, −1 = **~4** |
| NT-4 (600 ft) | A1.2, C5(a), E-b, −1 = **~4** |
| NT-6 (−13) | C5(c), E-b, −1 = **~3** |
| NT-9 (1876) | A1.1, B1, E-b, −1 = **~4** |
| NT-8 (great-uncle) | B3, E-b, −1 = **~4** |
| NT-7 (nephew) | B4 parentage, E-b, −1 = **~3** |

---

## 5. What I chose not to do, and why

1. **I did not convert NT-3 (57 vs 61) into a true 2-vs-2.** Doing so means stripping "sixty-one"
   out of r04 and r06. r04's talk builds its whole punchline on "sixty-one times in forty-three
   winters, and never once above," and r06's independent corroboration is what makes I06 work.
   The cost to the corpus exceeded the gain. NT-11 was planted in the same two narrators
   instead, so r08 and r12 now carry a coherent *set* of wrong totals from the store's talk,
   which is more natural anyway.

2. **I did not give r03 a non-date error.** He is the whole date-partition device; one count
   error in him collapses it. He is the only retelling that was not touched at all, and the
   hardening leans on him instead — the nine-mile distance in C5(b) and the wager figures in
   B4 now come from him, so a solver who discounts him wholesale loses points he cannot get
   anywhere else.

3. **I did not squeeze Section A by adding facts under the 450-word cap.** That would lower
   scores, but by making the test a compression exercise rather than an arbitration one, and
   the judge had already flagged compound items as the biggest threat to inter-grader
   agreement. Bolding the load-bearing parts was the fair version of the same move.

4. **I did not add a seventh abstention item**, though there were candidates (whether Judd was
   ever told what Ruth found; whether the 1909 gang was ever told what the two-inch mark
   meant). Six was the brief, and past six the test starts to reward blanket hedging, which is
   its own failure mode.

5. **I did not raise the corruption deduction above −1 per error, or cap it.** Uncapped −1 is
   already the right shape: it scales with credulity without letting one bad paragraph
   dominate a score.

6. **I did not touch the four story boundaries, the noise corpus, or the harness.** Out of
   scope, and the boundaries are what make the cross-story insights work.

7. **I did not make the ceiling reach 80 by weighting D3 more heavily** (e.g. making the whole
   abstention block worth 20 points). That would hit the target arithmetically, but it changes
   the 100-point structure and it converts the test into an abstention test. If the owner wants
   the last 6 points, the honest options are: (a) raise D from 15 to 18 by moving 3 points out
   of D1/D2 into a fourth abstention-scored logic item; (b) add two more near-tie pairs in
   Section A; or (c) accept ~86 for the very best solvers and re-measure after twelve runs, as
   the authoring notes recommend. **I would pick (c) and re-measure** — the 94 run was one
   sample, its abstention discipline was unusually good, and the section profile matters more
   than the total.

---

## 6. Files changed

| File | Change |
|---|---|
| `test-input/retellings/r01…r12` (9 of 12) | see § 1; r03, r05, r06 untouched |
| `test-input/questions.md` | A2 asks for the belief; Section A scope note; independence line in D2; span-of-count line in C3; near-tie call-out in E1; competing-explanation requirement in F1; a line warning that an apparent majority is not a settlement |
| `answer-key/canon.md` | F029 rewritten (start year now unsettleable); F040a and D13 added; F079 note on the milepost derivation and r09's eight miles; F075 note; **F095** (the decoy is false, with both refutations) and **F096** (post-1954 count unrecoverable); A05 and A06 added to § 8; gullibility maximum |
| `answer-key/corruption-map.md` | design rules 1, 4, 5; r01, r02, r04, r06, r07, r08, r09, r10, r11, r12 error tables; near-tie section rewritten (11 pairs, with breakers and consequences); recoverability index rows; device checklist and totals rewritten |
| `answer-key/answers-and-scoring.md` | full rewrite: checklist-reading rules, Section A scope rule, corruption list, gullibility maximum, A/B/C/D/E/F/G items, E re-bucketed, bands recalibrated |
| `answer-key/narrator-briefs.md` | v2.1 header note; r01, r02, r04, r06, r07, r08, r09, r10, r11, r12 briefs updated to match the retellings; D13 added to r07's quote list; coverage audit rewritten with wrong-value columns and NT markers |
| `answer-key/HARDENING-v2.1.md` | this file |

`answer-key/KEY-AUDIT.md` is left as the record of the v2.0 audit and is now historical: its
fix list was applied before this pass, and several of its rows (E row 3, E row 11, the near-tie
totals) are superseded here.
