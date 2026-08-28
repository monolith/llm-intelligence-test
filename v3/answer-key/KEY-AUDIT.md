# KEY-AUDIT — v3 answer key audited against the test input

**Scope.** Every scored item in `answers-and-scoring.md` (A 50 · B 8 · C 14 · D 10 · E 8 · F 6 · G 4)
plus the two deduction rules, checked against `test-input/questions.md` and the twenty-four
retellings only. `originals/` was not read. `corruption-map.md` and `canon.md` were used as the
claims under test, not as evidence. The six `author-checks/` files were consulted last and are
reconciled in § Author-check reconciliation.

**Verdict counts: ✅ 84 · ⚠️ 23 · ❌ 8** (115 rows). **23 required fixes.**

Legend — ✅ derivable from the retellings, correctly attributed, no defensible rival answer.
⚠️ the answer stands but the key misstates its support, gates on something single-source, or sits
on a boundary a careful solver could draw elsewhere. ❌ the key is wrong about the corpus, or the
corpus does not support the keyed answer against its rivals.

---

## Section A — Reconstruction (50 items)

| id | pts | verdict | evidence |
|---|---|---|---|
| A1.1 | 1 | ✅ | r02 §1 "In 1889 the farmers of the Larrow Valley met at Larrow Green"; §2 "creamery was built at Larrow Green in 1891"; r12 §I "In 1889 the farmers of this valley met"; §"In 1891 the creamery was built". "to 1911" only r02 ("held the office until 1911"), unbolded. |
| A1.2 | 1 | ✅ | D1 verbatim in r02 §3, r07 Item 1, r12 §II — three transcriptions, identical. |
| A1.3 | 1 | ✅ | Stated outright by r22 ¶3 "Under payment by weight nothing that follows in this report would have cost any man a dollar"; r13 "it makes the test the whole of the bargain"; r12 §II "the sentence on which the whole trouble … turned". |
| A1.4 | 1 | ✅ | r02 §4 (Loomis 1901–1940, Teague 1905, Sill buttermaker); r05 "from 1905 to 1945"; r14 "Forty-one years I have stood at that churn". |
| A1.5 | 1 | ✅ | Son: r02 §4 "son of the late president", r18 §II, r23 "the son, whatever is said at Ashlin". 1913: r02 §4, r08 "It is thirteen years this spring, since 1913", r06 1913 entry "New manager at the Association this year". Wrong value in exactly two (r01, r12) = NT-17. |
| A1.6 | 1 | ⚠️ | Facts fine — D7 verbatim in r05, r07 Item 6, r12's closing note; r23 paraphrases it. **But** the same ledger line also gates A7.6 and A8.6, and Section A rule 5 forbids scoring a fact twice; a solver that files the line under S7 or S8 (where r05 and r12 themselves put it) loses this point on filing, not knowledge. See fix 15. |
| A2.1 | 1 | ✅ | 4 May 1896 in D3 (r03, r07 Item 3), r13, r22 ¶4. Borrowed of Larrow Green: D3 ✎ twice, r14 "I made up an outfit for them out of my own glass", r24 1 May 1897 entry, r23. Seven miles: r02, r05, r13, r21, r22. |
| A2.2 | 1 | ✅ | r03's letter (weigh, composite jar, charge to the mark, acid, tester, read in percent off the neck); r11 §II; r05; r19; r21. |
| A2.3 | 1 | ✅ | D2 verbatim in r07 Item 2 and r20; r07's gloss "in use at the station from 1 May 1897"; r20 "put that outfit into use … on the first of May, 1897"; r24 "*May 1, 1897.* A. says the station's own glass came up". Wrong value in exactly two (r11, r23) = NT-10. |
| A2.4 | 1 | ✅ | D2's five lines transcribed identically by r07 and r20; total also in r04 "seventy-seven dollars and ninety-three cents". Recomputed: 25.20+31.68+0.90+18.00+2.15 = **77.93**; 72×0.35 = 25.20; 144×0.22 = 31.68. |
| A2.5 | 1 | ⚠️ | The two figures are in D5 (r03, r07 Item 3) — but D5 *is* A3.3. Two Section-A points are gated on one leaf, against the key's own rule 5, and a solver that discusses the summary leaf once (under the test book, where it lives) loses A2.5. See fix 14. |
| A2.6 | 1 | ✅ | r11 §II third consequence: "the pipette is not checked against anything, because … the pipette is the standard … It can be caught only by a burette brought in from outside". "none in the county" is unbolded and is not in the corpus; r06 supplies the equivalent ("most plants have never had it done"). |
| A3.1 | 1 | ✅ | Twenty-nine seasons 1896–1924: D9 ✎ (r03, r13 restates), r03 "from 1896 through 1924", r13's exhibit 1 "4 May 1896 to 31 December 1924", r22 ¶4, r24 preface. 30 Apr 1925: r03, r13, r18, r22 ¶10, r24. Wrong start in exactly two (r01, r17) = NT-13. |
| A3.2 | 1 | ✅ | r03's statement and letter: five columns, "drawn a line through it and put my letters against the line", "never written a figure over a figure"; r07 Item 3 "columns for date, patron, pounds and test. One hand throughout". |
| A3.3 | 1 | ⚠️ | D5 verbatim in r03 and r07. Sound in itself; the ⚠️ is the duplication with A2.5 (fix 14). |
| A3.4 | 1 | ✅ | D4 ✎ (r03); nine weeks in r03, r04, r09, r11 §IV, r22 ¶6; r24 "*May 8, 1911.* A. home cross about a broken measure". Recomputed 8 May→10 Jul = 23+30+10 = **63 days = 9 weeks**. Wrong value in exactly two (r05, r16) = NT-12. |
| A3.5 | 1 | ⚠️ | Fact secure (r03 "My wife Orra is Emmet Brant's sister"; r09; r17; r18; r01; r24). Boundary risk: canon files this insight as I05 = S3+S4, and r09 and r17 tell it from the Hessel Bottom side, so a solver filing it under A4 loses it under rule 3. |
| A3.6 | 1 | ⚠️ | D9 ✎ (r03, r07 Item 8 by description, r13 restates it accurately); 1919 circular in r01, r03, r09, r23, r24, r06, r08. Boundary risk: the statement was made *to the board* and r13 reports it inside the arbitration; a solver filing it under A7 loses it. |
| A3.7 | 1 | ✅ | Death 1934 under the imputation: r18 §IV, r24's last leaf, r01, r21. Custody: r18 §V and r07 Item 3 provenance (impounded March 1925 → office 1925–1959 → Rooms 1959), r04. |
| A4.1 | 1 | ✅ | Six farms: r09, r15's report, r16, r17, r19, r21; Brant largest: r09, r02, r17, r18. Wrong value unique to r02 (seven). |
| A4.2 | 1 | ✅ | 1 Jan 1897 in r07 Item 4 ✎, r13's exhibit 3, r18 §V. Scales agreeing: D10 ✎ (r07, r09), r09 "his weight and the station's weight came out the same", r17. |
| A4.3 | 1 | ❌ | The 1902 complaint is well carried (r03, r09, r12, r14, r15, r16, r22). The parenthetical is wrong on two counts: 3.78 is **not** single-source (r14 "that ran 3.78" **and** r22 ¶5 "three seventy-eight"), and the corpus states the Ostrey-Hollow-vs-Larrow-Green gap three incompatible ways — 3.78 vs 3.61 = **0.17** (r14+r22), "nineteen hundredths … under what … Larrow Green" (r09), and "about three-quarters of a point better" (r07 Item 16). None of the three is catalogued. See fixes 10, 11, 12, 13. |
| A4.4 | 1 | ✅ | D15 ✎ in r15 and r07 Item 11; Grigg named in r09, r12, r15, r24, r22 ¶9. The finding is reported as a finding by r09 ("reported that the wet hay … thins the cream") and r12. |
| A4.5 | 1 | ✅ | D10 ✎ (r07, r09), restated by r17. Proportionality: r04 "A herd whose milk was recorded at 4.56 was short 0.24 … A herd recorded at 3.42 was short 0.18"; the 4.56 is placed on the Vose Jerseys only by r08. Recomputed: 3.42/0.95 = 3.60, 3.60−3.42 = **0.18**; 4.56/0.95 = 4.80, 4.80−4.56 = **0.24**. |
| A4.6 | 1 | ✅ | r18 §V ("Roy lent it to Ivy in 1958 — lent, and I want the word"), r07 Item 4 provenance, r09's 1958 postscript, r17 "he lent it. He did not leave it to her." |
| A5.1 | 1 | ✅ | Vessey County / Redlow Ridge / Jerome Cudd: r09, r10, r12 §V, r18. 1914 in r09 and r12; wrong value unique to r10 (1913). |
| A5.2 | 1 | ✅ | r10 "From 1915, four men off Hessel Bottom hauled … in the summer flush … the rest of the year they went down to your station"; r09; r17. Reasons: r10 (cheese paid better, flush market, shorter pull). |
| A5.3 | 1 | ⚠️ | "his own test book" ✓ (r10, r04, r07 Item 13, r18) and "never compared it with anybody's" ✓ (r10). But **"his own glassware" is bolded and single-source** — only r10 ("with his own glassware that he bought new"). See fix 21. |
| A5.4 | 1 | ✅ | Sixteen seasons 1915–1930: r10's sixteen-row table and "The last of those summers was 1930", r09. The 0.19 differential is stated by r04 and derivable: r10's sixteen seasons average **3.7981 ≈ 3.80** against D5's 3.61. Wrong season count unique to r04 (fourteen). |
| A5.5 | 1 | ✅ | r10 supplies both limbs ("Good milk off wet ground, whatever they say over the ridge"; "A cheesemaker knows watered milk inside a day … Cheese is a witness"); r22 ¶7–8 draws the inference. |
| A5.6 | 1 | ✅ | Daughter: r10 throughout ("My father, Jerome Cudd"), r07 Item 13, r12 §V, r18. The 1958 copying: r10's letter and table, r04, r18. "1941–1962" is unbolded — 1962 appears nowhere for Rosalie. Wrong value in exactly two (r04, r19) = NT-21. |
| A6.1 | 1 | ⚠️ | Notebook a year ✓ (r06's twenty-eight books, r18 §V). 1908–1936 ✓ but **not from the narrators the key names** (see E-a #8). "**related to and employed by nobody**" is bolded and single-source — only r18 §II. See fixes 2, 21. |
| A6.2 | 1 | ⚠️ | The readings are there (r06: no added water at Ostrey Hollow in 1912, 1919, 1920, 1922, 1923, 1924, 1925, 1928, 1934, 1936; D6 "as always here"; r22 ¶7 "at every visit from 1908 forward"). **"fifteen years" is in no source** — the span is 1908–1936. See fix 16. |
| A6.3 | 1 | ✅ | D6 ✎ (r06 dated entry, r07 Item 9), r11 §III "in June of 1923", r22 ¶11, r02 §8 "in June of 1923". Wrong value in exactly two (r08, r12) = NT-11; broken by D16's 28 June order (r20, r07 Item 10, r19). |
| A6.4 | 1 | ✅ | D6's own closing clause "I did not weigh what it has cost them", plus r06's covering note ("I did not put down what I thought about it") and r22 ¶11. |
| A6.5 | 1 | ❌ | 28 June / 2 July ✓ (r20 ✎, r07 Item 10, r19); "in use that July" ✓ (r06 Oct 1923 entry, r20, r24). **But "the station's average was 3.80 in 1924" is stated correctly by r03 alone**, against r08's 3.90 *and* r22 ¶11's "three eighty-five". r04 and r06 — the carriers the key names — do not state it: r06's 1924 entry reads only "tests improved". A one-against-two split on a bolded gate. Derivable (3.61÷0.95, D5's 1896, the 1911 interval), but the key's stated support is false. See fix 1. |
| A6.6 | 1 | ✅ | Crate to the loft: r04, r21, r17, r18 §V, r22 ¶12. Notebooks: r07 Item 9 provenance ("state dairy office … 1936; … College at Farland in 1947"), r18 §V, r04. |
| A7.1 | 1 | ⚠️ | January 1925 petition ✓ (r02 §6, r12, r13, r22 ¶10, r24, r05). The framing "credited 3.61 for twenty-five years were credited 3.80" inherits the A6.5 defect: only r03 gives 1924 = 3.80. |
| A7.2 | 1 | ✅ | r02 §6 (17 Mar–4 May, Frick, Ashlin); r13 (three sessions, second and third in the station's own weigh room); r21 ("three sittings … two of them … in the weigh room"); r24 April 1925 entry; r22 ¶10. |
| A7.3 | 1 | ✅ | r13 names all three and who put each (Vose / Teague / the 1908 report read in); r22 ¶7–9 the same three; "none accepted" in D8 ✎. |
| A7.4 | 1 | ✅ | r13's reprinted exhibit list (four books, incl. "The circuit notebook of the state dairy inspector for the year 1923") **and** r23 ("What passed across my desk to that board was four things … And the state inspector's notebook"). Not single-source — see fix 13. |
| A7.5 | 1 | ✅ | D8 ✎ (r02 §6, r07 Item 7); dismissal 30 Apr in r13, r18, r22, r24, r03. Wrong award in exactly two (r01, r21) = NT-9. |
| A7.6 | 1 | ⚠️ | Arithmetic sound (3,800 ÷ 19,000 = 0.20 exactly; D8 "charged to the station account"; D7 "Carried to the general account"). Boundary/duplication risk shared with A1.6 and A8.6 — fix 15. |
| A8.1 | 1 | ✅ | Granddaughter: r04 ("Ansel Keddie … was my grandfather"), r18 §I, r21 "Then the granddaughter came back", r22's closing correction. Vaught: r11's byline, r19, r04. Wrong value in exactly two (r19, r22) = NT-18. |
| A8.2 | 1 | ✅ | r04 "Five sets of records were needed and no two of them had ever been in one room before last year", enumerated. |
| A8.3 | 1 | ✅ | Feb 1958 / station loft / nine: r04, r17, r21 ("there were nine of them left in it"), r22 ¶12, r18 §V, r19 (loft). Wrong count in exactly two (r12, r19) = NT-16; D13 lists exactly nine readings. |
| A8.4 | 1 | ✅ | D13 ✎ twice (r04, r07 Item 14). Recomputed: 17.6−16.72 = **0.88**; 16.72÷17.6 = **0.95** exact. Wrong value in exactly two (r11, r19) = NT-1. |
| A8.5 | 1 | ✅ | D14 ✎ three times (r04, r07 Item 15, r11 §VII) — "from the first of May, 1897, to the twelfth of June, 1923 … low by one part in twenty". Recomputed: 3.61÷0.95 = **3.80**; 3.80−3.61 = **0.19**; 0.19÷3.80 = **0.05**. |
| A8.6 | 1 | ✅ | 40,000,000 in r02 §7, r04, r07 Item 6, r23, r11; 25¢ in r02, r04, r09, r23; 76,000 in D14 ✎ ×3 and r07's gloss. Recomputed: 40,000,000×0.0019 = **76,000**; ×$0.25 = **$19,000**. Ledger identity: D7's 3,040 lb/yr × 25 = **76,000**; and 57,760 = 1,600,000×3.61 %, 60,800 = 1,600,000×3.80 % — the entry is exact and by itself breaks NT-5 (44 M would give 1,760,000/yr). |
| A8.7 | 1 | ✅ | r04 "thirty-five years … thirty-three years … dead twenty-four years"; r19 same two; r11 and r22 date the bulletin October 1958; r24's editorial note ("twenty-four years after his death"). |

**Section A: ✅ 38 · ⚠️ 10 · ❌ 2**

---

## Section B — Relationships (8 points, 8 gates)

| id | pts | verdict | evidence |
|---|---|---|---|
| B1 answer | 1 | ✅ | r04, r18, r21, r22's closing note. |
| B1 derivation | 1 | ✅ | r18 §I "My daughter is Ivy … which makes her my father's granddaughter"; r04 "My father, Duncan Keddie … was his son"; r24 (Duncan is Ansel and Orra's boy). |
| B2 answer + derivation | 1 | ✅ | r18 §II sets out the full chain; r09 and r17 give it independently; r12's 1959 footnote confirms. Wrong value in exactly two (r01, r21) = NT-19. |
| B2 abstention (A08) | 1 | ⚠️ | Poles present and flat (r17 "a half sister, by his father's second wife" vs r09 "full brother and sister, same mother and same father"); nothing settles it; the answer is unchanged either way. **But the key's stated ground — "the Ostrey Hollow register burned in 1912" — appears in no retelling.** The corpus's actual ground is r24's preface ("The pages covering her girlhood and her family before 1889 were not preserved"). See fix 7. |
| B3 father | 1 | ⚠️ | Answer secure. The key's tie-breaker is overstated: r02's "Selby Vose, son of the late president" is her own §4 prose, not a quotation from the minute book. r18 and r23 both name and reject the nephew story. See fix 20. |
| B3 significance | 1 | ✅ | D1's last clause ✎ ×3; r22 ¶3 and r12 §II draw the consequence; r08 supplies his own 4.56 and his authorship of the circular; r04 supplies the 0.24/0.18 proportionality. |
| B4 cannot settle | 1 | ✅ | r01 "first cousins. Everybody knew that", r21 "cousins of some sort … I could not draw you the line on paper", against r18 §III's flat denial. No document either way. |
| B4 what is established | 1 | ❌ | Two of the four bullets the key lists are not in the corpus: the burned church register, and (by implication) any documentary silence about it. A solver answering from the retellings cannot state them. See fix 7. |

**Section B: ✅ 5 · ⚠️ 2 · ❌ 1**

---

## Section C — Math (14 points). Every value recomputed from retelling-stated figures.

| id | pts | verdict | recomputation from the retellings |
|---|---|---|---|
| C1(a) | 1 | ✅ | D13 (r04, r07): 16.72 ÷ 17.6 = **0.95** exactly (17.6 × 0.95 = 16.72). Short 0.88 = 5 %. |
| C1(b) | 1 | ✅ | D5 (r03, r07): 3.61 ÷ 0.95 = **3.80**; 3.80 − 3.61 = **0.19**. Cross-checked by r10's sixteen seasons (mean 3.798) and D11's four 1919 figures (15.20 ÷ 4 = 3.80). |
| C1(c) | 1 | ✅ | 40,000,000 (r02, r04, r07, r23) × 0.0019 = **76,000 lb**; D14 states it. |
| C1(d) | 1 | ✅ | 76,000 × $0.25 (r02, r09, r23) = **$19,000**; 3,800 ÷ 19,000 = **0.20 = one fifth**. Diagnostics re-verified: 16.27/17.6 = 0.9244; 3.61/0.9244 = 3.905; gap 0.295; 40 M × 0.00295 = 118,000. 3.16/0.95 = 3.326. 44 M × 0.0019 = 83,600. 76,000 × 0.27 = 20,520. 3,800/19,600 = 19.39 %. All as printed. |
| C2(a) | 1 | ✅ | D10 (r07, r09; restated r17): 200,000 × 3.42 % = **6,840 lb**. |
| C2(b) | 1 | ✅ | 3.42 ÷ 0.95 = **3.60**; 200,000 × 3.60 % = **7,200**; 7,200 − 6,840 = **360 lb**. |
| C2(c) | 1 | ✅ | 360 × $0.24 (r09, single-source and uncontested) = **$86.40**; the $90.00 alternative at 25¢ is correctly conditioned. |
| C3(a) | 1 | ✅ | 40,000,000 × 3.61 % = **1,444,000 lb** (r04 states it; r07 Item 6 implies it). |
| C3(b) | 1 | ✅ | 40,000,000 × 3.80 % = **1,520,000 lb** (r04 states it). |
| C3(c) | 1 | ✅ | 76,000 ÷ 1,520,000 = **5.00 %**; 76,000 ÷ 1,444,000 = **5.2632 %**. Both denominators are printed by r04 and by r07 Item 6 ("each is right of its own denominator and of no other"). Wrong framing in exactly two (r05, r11) = NT-20. |
| C4(a) | 1 | ✅ | D2's own lines: 25.20 + 31.68 + 0.90 + 18.00 + 2.15 = **$77.93**. r20 prints the total 77.93 and then writes "Seventy-seven dollars and thirty-nine cents" one line below — the tie-breaker works exactly as designed. |
| C4(b) | 1 | ✅ | 6 doz. = **72** (D2 ✎ ×2, plus r04 and r19); 17.6 − 16.72 = **0.88 c.c.** Wrong count in exactly two (r11, r21) = NT-15. |
| C5(a) | 1 | ⚠️ | Recomputed: 1 May 1897 → 1 May 1923 = 26 years; 1 May → 12 June = 30 + 12 = **42 days = 6 weeks**; 1898–1922 inclusive = **25** full years. Sound. The gate should accept exact equivalents ("26 years and 42 days", "26 years 1 month 11 days"), which the key does not say. See fix 18. |
| C5(b) | 1 | ✅ | Genuine abstention: r14 "about nine hundred thousand" vs r23 "a good eleven hundred thousand"; r07's closing note states the gap plainly ("is not in the ledgers and is nowhere else"). Not derivable — the ledger's station column begins with 1897 (r07 Item 6) and the 1896 figure is a test average, not an intake. |

**Section C: ✅ 13 · ⚠️ 1 · ❌ 0**

---

## Section D — Logic (10 points)

| id | pts | verdict | evidence |
|---|---|---|---|
| D1.1 | 1 | ✅ | D4 ✎ (r03); r11 §IV "**One variable changed**"; r04 "one object changed"; r22 ¶6. |
| D1.2 | 1 | ✅ | r11 §IV and r04 both enumerate six or seven held constants. |
| D1.3 | 1 | ✅ | 3.80 → 3.61 on 10 July: D5 ✎ and D4 ✎; nine weeks in r03, r04, r09, r11, r22. |
| D1.4 | 1 | ⚠️ | The "does not tell us whose measure was borrowed" limb collides with A06: r06's own 1911 entry places his visit in **June**, a month after the 8 May breakage, which makes r09's "the state man left his own measure that June" impossible. A solver that says so is reasoning correctly and may read it as a partial settlement. See fix 22. |
| D2.1 | 1 | ✅ | At least six independent reasons available across ≥6 narrators: the ledger surplus (r05 ✎, r07 ✎, r12 ✎, r14, r23), the 1911 interval (r03 ✎, r04, r09, r11, r22, r24), Strawn's clean visits (r06 ✎, r22), Alder Corners (r10 ✎, r09), the 1924 rise under the same tester (r03, r06, r08), Brant's two scales (r09 ✎, r17, r07 ✎). |
| D2.2 | 1 | ✅ | Four of the six survive the removal of the 1958 measurement, as the key says. |
| D2.3 (A09) | 1 | ✅ | Poles flat and unsupported: r05 "I put it to Mr. Vose in 1916 and was told to let it alone" vs r23 "Teague never asked anybody anything in forty years". No minute, no paper. |
| D3.1 (A03) | 1 | ✅ | r05 "Mr. Vose knew what that account was doing. He signed the sheet every year" vs r23 "He read the totals and he never read the lines above them." Neither cites a document. |
| D3.2 | 1 | ❌ | The bolded gate "**nothing in his hand anywhere uses the words glass, pipette or measure**" is **false of the corpus**: r08 line 19 reads "The rise of 1924 is the **measure** of it." The author-check for r05–r08 records this as a forced brief conflict. A solver that word-searches finds it and reports the key's claim as untrue. See fix 8. |
| D3.3 | 1 | ⚠️ | "no statement by Vose on the point survives" is loose: r08 **is** a surviving statement by Vose that addresses the condemnation directly ("I decline to build a mystery on a piece of housekeeping"). It does not bear on pre-June-1923 knowledge, which is what the key means, but the wording should say so. See fix 8. |

**Section D: ✅ 7 · ⚠️ 2 · ❌ 1**

---

## Section E — Contradictions (8 points; 21 gates audited)

### E-a, the sixteen listed conflicts

| # | verdict | evidence |
|---|---|---|
| 1 | ⚠️ | Wrong value correct (r01, r17); right value in r03 ✎, r07 ✎, r13, r22. **This row is also NT-13**, so a solver can be paid twice for one conflict (E-a and E-b). See fix 6. |
| 2 | ⚠️ | r15's covering letter "the whole of 1908 — every month of that year" against his own report's "January, February and March" ✓. **r09 is not a Jan–Mar carrier** — he says only "sampled the Bottom herds through the winter". Correct carriers are D15 in r15 and r07 Item 11. Fix 5. |
| 3 | ❌ | Neither named carrier states the figure: r04 never gives a 1924 average; r06's 1924 entry says only "tests improved". Only **r03** gives 3.80, against **two** wrong values (r08 3.90, r22 3.85 — the second uncatalogued for F061). "Majority" is the wrong method; there is no majority. Fix 1. |
| 4 | ✅ | 3.90/3.80 aside, this row (fat at 27¢) resolves by 19,000 ÷ 76,000 = $0.25 and by r02, r09, r23. |
| 5 | ⚠️ | Correct; but the key credits only r07 and D10's series. **r13's exhibit list ("begun 1 January 1897") and r18 §V also carry it.** Fix 4. |
| 6 | ✅ | Seven farms unique to r02; six in r09, r15's report, r16, r17, r19, r21. |
| 7 | ✅ | r18 §I "born in eighteen sixty-eight" against §IV "She was eighty-two when she died in 1948" (= 1866); r24's preface independently gives 1866. |
| 8 | ❌ | **Neither r07 nor r23 states Strawn's start year.** The correct carriers are r04 ("from 1908") and r22 ¶7 ("from 1908 forward"). Fix 2. |
| 9 | ✅ | r07 Item 5 "found in the Association office at Ashlin" against r04, r17, r18, r21, r22 (the loft) and r07's own Item 5 heading naming the crate. |
| 10 | ✅ | r20 "The house sold nothing into Ordell County before 1900" four paragraphs above her own 14 April 1897 invoice. |
| 11 | ✅ | r07 Items 3 and 4 headed "kept by E. Brant" / "kept by A. Keddie" directly above D3 (signed A. Keddie) and D10 (Brant's own scale). |
| 12 | ✅ | r05 "The station-gain line was my own device; I began it when I came in 1905" directly above "That is the entry for 1898". |
| 13 | ✅ | r24 "to eleven families" against r01, r03, r09, r14, r17 (nine). |
| 14 | ✅ | r04's "fourteen seasons" against r10's sixteen-row table ending 1930 and r09. |
| 15 | ❌ | **r18 gives no year for Selby's managership.** The correct carriers are r02 §4 and r08 ("since 1913"), with r06's 1913 entry corroborating. Fix 3. |
| 16 | ✅ | r19's weld against r02 §6, r13, r15 (two bodies, 1908 and 1925). |

### E-b, E-c, E-d

| gate | verdict | evidence |
|---|---|---|
| E-b (22 near-tie pairs) | ✅ | All twenty-two verified by grep: each wrong value is carried by **exactly two** narrators and no more, and each correct value by ≥2 or by a quoted document. Every stated breaker works from the retellings alone — including the three sharpest: D13's nine readings none below 16.70 (NT-1); D16's "order of the 28th ultimo" acknowledged 2 July, which cannot answer a 12 July condemnation (NT-11); and r20 printing "Total — 77.93" one line above "Seventy-seven dollars and thirty-nine cents" (NT-14). |
| E-c A04 | ✅ | r19 "put off … knowingly, and the firm's silence in 1923 is the proof" vs r20 "The mold had been reground … an accident"; r20 herself records that the works books burned in 1931, so no record exists either way. |
| E-c A06 | ⚠️ | Poles present (r04, r09). But **r06's 1911 entry dates his visit to June**, after the 8 May breakage — which refutes r09's pole outright and leaves r04's as the only surviving account. Abstention still correct (one unsupported memory is not a record), but the key should say so, or a grader will mark down a solver that reasons well. Fix 22. |
| E-c A10 | ❌ | r02 (1892) and r12 (1891) are memory; **r15's 1893 sits inside the block-quoted 1908 report** — "Since the meeting of 1893, when payment by test came in among us". The test tells solvers a quoted document outranks a memory, so the corpus points to 1893 as settled. r07 Item 1 and r22 ¶3 both state that the by-laws carry no date, but a document beats them. Fix 9. |
| E-d | ✅ | All eight self-refutations verified in the text: r03 (Ashlin vs D3), r05 (1905 vs the 1898 entry; theft vs his own surplus), r07 (Items 3/4 vs D3 and D10), r11 (16.27 cascade vs the D14 paragraph it reprints), r13 ("every physical appliance" vs a four-book list), r15 (whole of 1908 vs three months), r18 (1868 vs eighty-two in 1948), r20 (nothing before 1900 vs the 1897 invoice). Bonus, uncatalogued: r11 §III's "first of May, 1898" against the D14 paragraph it prints in §VII ("from the first of May, 1897"). |

**Section E: ✅ 13 · ⚠️ 4 · ❌ 4**

---

## Section F — Theory (6 points)

| id | verdict | evidence |
|---|---|---|
| F1 | ⚠️ | Cause, size and onset all secure (D13, D5, D2, D14 ✎). **The cessation limb — "the 1924 average 3.80" — rests on r03 alone** against r08's 3.90 and r22's 3.85; derivable but not carried. Fix 1. |
| F2 | ✅ | Named by r08 and r14. Defeaters all present: r06's lactometer entries and D6's "as always here"; r10's D11 and her cheese-vat argument; r09's two agreeing scales; and the arithmetic 5 % × 1,600,000 = **80,000 lb a year** (1,600,000 in r02, r04, r23; r23 adds "it did not vary greatly"). |
| F3 | ✅ | Named by r05 and r21 (and asserted unwithdrawn by r01). Defeated by D7 ✎ ×3 — the cream arrived **heavy** by 3,040 lb a year in the accuser's own hand — by the 1911 interval, and by the 1924 rise under the same tester (r03: he tested through 1924). r12's own closing note performs the refutation. |
| F4 | ✅ | Named by r15 and r16. Defeated by D12 ✎ ×3 (0.05 winter, nothing in summer), by r10's sixteen seasons off the same ground, and by flatness in every month (r03, r09, r17, r22). Recomputed: 0.19 ÷ 0.05 = **3.8×** too small. |
| F5 (A07) | ⚠️ | Poles present (r13 vs r02 §8) and r13 self-refutes. **But the corpus leans hard negative** — r02 "I took every word down and it is not there", r18 "stayed there until Ivy found it", r21 "Nobody ever gave it a thought", r17 "without one soul thinking about it" — against one generic sentence. Abstention is still right, but the key should say a negative *lean* that declines to decide is credited. Fix 23. |
| F6 (A05) | ✅ | r18 §IV ("something in the glass") vs r13 ("the patrons were at fault"), over r03's declared silence ("I cannot tell you why the figures are what they are"). Both single, interested, private-speech recollections. Nothing else in Keddie's hand but the question mark. |

**Section F: ✅ 4 · ⚠️ 2 · ❌ 0**

---

## Section G — Summary (4 points)

| id | verdict | evidence |
|---|---|---|
| G1 | ✅ | Matches the question's "at most 150 words". |
| G2 | ⚠️ | The item says "at least five of **the eight** record series" and then lists **nine**. Fix 17. |
| G3 | ✅ | Both names are unavoidable from r04, r18, r19, r21, r22. |
| G4 | ✅ | Every element of the arc is documented; the "no absorbed corruption" test is well defined by the flagged-values list (subject to fix 19). |

**Section G: ✅ 3 · ⚠️ 1 · ❌ 0**

---

## Deductions

| rule | verdict | evidence |
|---|---|---|
| Corruption −1 | ⚠️ | All 33 listed values verified present and correctly attributed. But the list reads as the operative enumeration and **omits ten catalogued planted errors that the key scores elsewhere**: r06's 1907 circuit (E-a 8), r23's 1911 / 1922 / 1924 (E-a 15), r17's 1899 / 1921 / 1926, r04's fourteen seasons (E-a 14), r19's welding of 1908 to 1925 (E-a 16), r22's 3.85 for 1924. Fix 19. |
| Gullibility −2, max −20 | ✅ | Ten abstention items, all reachable from the questions (A01 via B4; A02 via C5b; A03 via D3; A05 and A07 via F1's subsidiaries; A08 via B2; A09 via D2; A04, A06, A10 via E1's open sweep). The "leans one way while declining" clause is stated clearly and applies to all ten. |

**Deductions: ✅ 1 · ⚠️ 1**

---

## Section A — partition analysis

**Is the eight-story partition recoverable cue-lessly?** Yes, and the mechanism is clean: **each of
the eight stories has exactly one narrator whose entire slice is that story and nothing else.**

| story | sole-slice narrator | second narrator | boundary signal in the text |
|---|---|---|---|
| S1 Association / Article VII | **r02** (numbered sections 1–8, all institutional) | r05, r23, r12 §I–II | r02 opens at 1889 and never goes up the valley; her §8 defines her own limits |
| S2 the crate from Tarnet | **r20** (the supplier's chapter, 1897 order → 1923 replacement → 1931 fire) | r14 (the borrowed 1896 outfit), r07 Items 2 & 5 | r20 begins and ends with one lot of glass |
| S3 Keddie and the test book | **r03** (statement + unsent letter, first-hand) | r24, r18 §IV | r03 is the bench, the book, the columns, the 1911 leaf |
| S4 Hessel Bottom | **r09** (the meadow, the six farms, the weigh book) | r17, r15, r16, r24 | r09's sub-headings — the Bottom, the book, the trouble, the family |
| S5 Alder Corners | **r10** (the factory, the ridge, the four men, sixteen seasons) | r12 §V, r09 | r10 never touches Ordell County's own records and says so |
| S6 Strawn's circuit | **r06** (twenty-eight circuit books, 1907/8–1936) | r07 Item 9, r23 | year-by-year entries; nothing outside the circuit |
| S7 the arbitration | **r13** (petition → sessions → exhibits → award) | r02 §6, r05, r08, r21, r23 | r13's own headings enumerate the story |
| S8 the nine pipettes | **r04** (the crate, the burette, the arithmetic, Bulletin 471) | r11, r19, r22, r18 §V | r04 opens with the five record series and closes with the crate on the table |

The five juxtaposing narrators (r07, r11, r12, r19, r22) cross all eight and supply no boundaries;
they are the noise the partition has to survive, and it does. A solver that reads for *whose story
is this* rather than *what happened* will land on or very near the intended eight.

**But the partition is not uniquely determined**, and the v3 scope rule ("credit never travels")
makes that expensive. These facts sit fairly in two stories, and each gates a point:

| fact | keyed to | could fairly sit in | why |
|---|---|---|---|
| D5's summary leaf (1896 3.80 / 1898 3.61) | **A2.5 and A3.3 — both** | S2 or S3 | one leaf, two points; against the key's own rule 5 |
| the "station gain" ledger line | **A1.6, A7.6, A8.6 — three** | S1, S7 or S8 | r05 and r12 tell it as arbitration matter; r04 and D14 as 1958 matter |
| Keddie's marriage to Orra Brant | A3.5 | S3 or S4 | canon files it as I05 = S3+S4; r09 and r17 tell it from the meadow |
| Keddie's 17 Mar 1925 statement | A3.6 | S3 or S7 | it was made to the board; r13 reports it inside the hearing |
| the 1919 circular | A3.6 | S3, S4, S6 or S7 | r09 receives it, r06 answers it, r08 defends it |
| the 1911 interval | A3.4 | S3 or S8 | r11 §IV and r04 both present it as the proof, not as bench history |
| the crate's journey to the loft | A6.6 | S2, S6 or S8 | it is the crate's end, the inspector's act, and the 1958 find |
| the 1897 invoice | A2.3 / A2.4 | S2 or S8 | r19 and r04 use it as "the price of the trouble" |
| the Alder Corners comparison as refutation | A5.5 | S5 or S4 | it kills a theory that lives in S4 |
| the 1908 committee | A4.4 | S4 or a solver's own "bog hay" story (r15 + r16 + D12) | a defensible eighth story in its own right |
| Article VII's effect | A1.3 | S1 or S7 | r13 and r22 both open the arbitration with it |
| the 1924 rise | A6.5 / A7.1 | S6 or S7 | the condemnation's consequence and the petition's cause |
| Brant's weigh book | A4.2 | S4 or S8 | one of Ivy's five record series |
| the proportional loss / Vose Jerseys | A4.5 | S4 or S7 | canon files it as I08 = S4+S7 |

**Verdict.** The eight-way partition *is* recoverable from the retellings alone — each story has
exactly one narrator devoted to it and to nothing else, and those eight narrators between them
draw all eight boundaries — but the partition is not uniquely determined: fourteen scored facts,
including two (D5's leaf and the station-gain line) that the key itself gates twice and three times
over, sit defensibly in two or three stories, so under the strict "credit never travels" rule a
well-reconstructed answer can lose five to eight Section A points on filing rather than knowledge.

---

## Global checks

| check | result |
|---|---|
| **Internal contradictions (8)** | ✅ All eight verified in the text (r03, r05, r07, r11, r13, r15, r18, r20) — see E-d above. A ninth, uncatalogued, exists in r11 (§III "first of May, 1898" vs the D14 paragraph it prints in §VII); harmless, and it strengthens NT-10. |
| **Late reversals (r12, r22)** | ✅ r12's "NOTE ADDED WHILE IN PRESS" prints D7 and withdraws the theft paragraph verbatim as briefed. r22's closing note prints D12, withdraws the bog-hay concession ("Five hundredths in winter and nothing in summer will not carry nineteen hundredths in July"), **and** self-corrects great-niece → granddaughter. Both work. |
| **Date-unreliable narrators (r17, r23)** | ✅ r17: five date errors (1895, 1899, 1921, 1926, 1900), every quantity and relationship right (200,000 / 3.42 / six farms / 0.19 / four men / second cousins / nine families). r23: four date errors (1898, 1911, 1922, 1924), every figure right ($3,800 / 40,000,000 / 1,600,000 / 25¢ / the ledger wording / Selby as son / the four exhibits). The category partition is clean in both. |
| **Decoy theories** | ✅ All three seeded in exactly two narrators (watering r08+r14; theft r05+r21, with r01 as unwithdrawn lore and r12 as the withdrawn body claim; bog hay r15+r16) and each refuted by a quoted document **and** by arithmetic — D6/D11 + 80,000 lb a year; D7 + a thief cannot make a surplus; D12 + 0.19 flat in twelve months. |
| **Juxtapositions** | ✅ Five (r07, r11, r12, r19, r22). r19's weld of the 1908 committee to the 1925 board and r07's swapped catalogue attributions are the two that actually mislead; both are refuted on the same page. |
| **Word counts 1,000–1,500** | ⚠️ On prose only (title line, italic framing note and r10's figure table excluded — the convention the r09–r12 and r17–r20 author checks use) **every file is inside the band**, 1,365–1,499. On whole-file `wc -w` (the convention the r01–r08 checks use) **seven exceed 1,500**: r10 1,607, r12 1,554, r11 1,547, r09 1,542, r23 1,531, r24 1,521, r22 1,504. The two conventions are used inconsistently across the author checks. Fix 16b. |
| **Answer-key ids or phrasing in the test input** | ✅ Clean. No F-id, X-id, NT-id, A01–A10 id or D-document id appears in `questions.md` or in any retelling; no retelling uses the words corruption, abstention, near-tie, decoy or canon; no retelling mentions "eight stories". (Note, internal only: the key uses **D1–D3** for both Section D questions and documents D1–D3 — e.g. A1.2 cites "F042, D1" meaning the by-laws while "D1" is also the 1911-interval question. Worth disambiguating.) |
| **Must-not-mention breaches** | ⚠️ One, and it is the flagged one: r08 is forbidden the words glass, pipette and measure "anywhere, in any connection" and uses **measure** once, in the briefed X30 sentence "The rise of 1924 is the measure of it." All other prohibition lists check clean by grep (r01, r10, r16, r17, r19, r21, r24). Fix 8. |
| **The canon 0.19 / 0.17 gap** | ❌ Real and propagated. Canon F098a puts Larrow Green at 3.78 against the station's recorded 3.61 — a visible gap of **0.17** — while F076 puts the true shortfall at **0.19**. The narrator briefs merge the two: r09's brief instructs "The gap **between the Hollow and Larrow Green** was **nineteen hundredths of a point** (F076)", and r09 says exactly that. r22 ¶5 prints 3.61, 3.78 and "nineteen hundredths" in three consecutive sentences. r07 Item 16 was briefed to give the comparison without the figure and gives "**about three-quarters of a point better**" — 0.75, which matches neither 0.17 nor 0.19 and would put Larrow Green at 4.36. So the corpus states one comparison three incompatible ways, none catalogued, and a solver that does the subtraction finds an uncatalogued contradiction in the corpus's documentary anchor. Fixes 10, 11, 12. |

---

## Required fixes

Twenty-three. Ordered by severity.

**1. The 1924 average has one correct carrier and two wrong ones.** (A6.5 ❌, E-a #3 ❌, A7.1, F1)
- File `test-input/retellings/r06-extracts-from-the-circuit-books.md` —
  old: `**1924.** Ostrey Hollow. Scales true, no added water, tests improved.`
  new: `**1924.** Ostrey Hollow. Scales true, no added water, tests improved. Their book gives the year at 3.80.`
- File `answer-key/answers-and-scoring.md`, E-a table row 3 —
  old: `| 3 | The 1924 average | 3.90 (r08) / **3.80** (r03, r04, r06) | Majority |`
  new: `| 3 | The 1924 average | 3.90 (r08), 3.85 (r22) / **3.80** (r03, r06) | Arithmetic — 3.61 ÷ 0.95, confirmed by D5's 1896 season and by the 1911 interval; there is no majority |`
- File `answer-key/corruption-map.md`, recoverability row F103 —
  old: `| F103 cessation: 3.80 from 1924 | r03, r06, r04 | r08 (3.90) | Majority |`
  new: `| F103 cessation: 3.80 from 1924 | r03, r06 | r08 (3.90), r22 (3.85) | Arithmetic + D5 |`

**2. Strawn's first circuit — wrong carriers named.** (A6.1 ⚠️, E-a #8 ❌)
- `answers-and-scoring.md`, E-a row 8 — old: `1907 (r06) / **1908** (r07, r23)` → new: `1907 (r06) / **1908** (r04, r22)`.
- `corruption-map.md`, F013 row — old: `| F013 Strawn, circuit 1908–1936, unrelated to all | r06, r07, r23 |` → new: `| F013 Strawn, circuit 1908–1936, unrelated to all | r04, r22 (the 1908 start); r06, r07, r18 (the retirement and the notebooks) |`.

**3. Selby Vose's start as manager — wrong carrier named.** (E-a #15 ❌)
- `answers-and-scoring.md`, E-a row 15 — old: `1911 (r23) / **1913** (r02, r18)` → new: `1911 (r23) / **1913** (r02, r08; r06's 1913 entry notes a new manager)`.
- `corruption-map.md`, F009 row — old: `r02, r18, r23` → new: `r02, r18, r23 (the son); r02, r08, r06 (the 1913 date)`.

**4. Weigh-book start — two correct carriers uncredited.** (E-a #5 ⚠️)
- `answers-and-scoring.md`, E-a row 5 — old: `**1 Jan 1897** (r07, D10's series)` → new: `**1 Jan 1897** (r07 ✎, r13's exhibit list, r18)`.

**5. The 1908 sampling — r09 is not a Jan–Mar carrier.** (E-a #2 ⚠️)
- `answers-and-scoring.md`, E-a row 2 — old: `**Jan–Mar only** (D15, r07, r09)` → new: `**Jan–Mar only** (D15 as printed by r15 and r07)`.

**6. E-a row 1 is also NT-13 — double credit possible.** (E-a #1 ⚠️)
- `answers-and-scoring.md`, after the E-a table, add: `Row 1 is also NT-13. A solver that notices the pair earns E-b credit for it; a solver that merely resolves it earns E-a credit. Never both.`

**7. The burned church register is not in the corpus.** (B4 ❌, B2 ⚠️)
- `answers-and-scoring.md`, B4 — old: `two narrators assert a cousinship from talk and one denies it flatly; the Ostrey Hollow church register burned in 1912; no document names or denies a link; and a family member's denial is not a record.`
  new: `two narrators assert a cousinship from talk and one denies it flatly; no document in the corpus names or denies a link; and a family member's denial is not a record.`
- `answers-and-scoring.md`, B2 — old: `(the Ostrey Hollow register burned in 1912; r17 says half, r09 says full, neither cites anything)`
  new: `(r17 says half, r09 says full, neither cites anything, and r24's editor states that the pages covering her girlhood and her family before 1889 were not preserved)`.
- `canon.md` §8 rows A01 and A08: mark the burned register as background not present in the test input.

**8. The "glass, pipette or measure" claim is false of r08.** (D3.2 ❌, D3.3 ⚠️)
- `answers-and-scoring.md`, D3.2 — old: `**and nothing in his hand anywhere uses the words glass, pipette or measure**`
  new: `**and nothing in his hand anywhere names the station's glassware** — he calls it "the station's testing apparatus" and never once says glass or pipette`.
- `answers-and-scoring.md`, D3.3 — old: `**no statement by Vose on the point survives**`
  new: `**no statement by Vose survives on what he knew before June 1923** — his 1926 address speaks only of the condemnation after the fact`.

**9. A10's third pole sits inside a quoted document, which settles it.** (E-c A10 ❌)
- File `test-input/retellings/r15-grigg-committee-report.md`, inside the block-quoted 1908 report —
  old: `Since the meeting of 1893, when payment by test came in among us and the pound of butter fat took the place of the pound of milk as the measure of a man's month, a difference of this kind is no longer a matter of opinion.`
  new: `Since payment by test came in among us and the pound of butter fat took the place of the pound of milk as the measure of a man's month, a difference of this kind is no longer a matter of opinion.`
  and in the covering letter, after `I have never in my life been given a duty I liked less.`, add:
  `Payment by test came in with the 1893 meeting, as I have always understood it, and from that year a difference of this kind stopped being a matter of opinion and became a matter of money.`

**10. r07's Larrow Green comparison is arithmetically impossible.** (A4.3 ❌)
- File `test-input/retellings/r07-accession-notes.md`, Item 16 —
  old: `the Larrow Green average runs about three-quarters of a point better.`
  new: `the Larrow Green average runs a little under two tenths of a point better.`

**11. r09 attaches the 0.19 true shortfall to the Larrow Green comparison.** (A4.3 ❌)
- File `test-input/retellings/r09-my-fathers-book.md` —
  old: `Our milk at the Hollow ran nineteen hundredths of a point under what the same class of milk was making down at Larrow Green.`
  new: `Our milk at the Hollow ran under what the same class of milk was making down at Larrow Green, and the figures we were paid on ran nineteen hundredths of a point under what that milk actually was.`

**12. A4.3's parenthetical misstates the record.** (A4.3 ❌)
- `answers-and-scoring.md`, A4.3 — old: `(Larrow Green's own average of about 3.78 against the station's 3.61 is context and does not gate the point: the figure is single-source.)`
  new: `(Larrow Green's own average of about 3.78 against the station's 3.61 — carried by r14 and r22 — is context and does not gate the point. Note that the visible gap it produces, 0.17, is **not** the 0.19 true shortfall; a solver that distinguishes them is right to.)`

**13. The single-source table is wrong on two of its five rows.**
- `corruption-map.md` § Single-source scored facts: delete the row `| Larrow Green's own 3.78 average | r14 | … |` (r22 ¶5 carries it) and the row `| The four exhibits before the board | r13 | … |` (r23 lists all four); change `Five scored facts appear correctly in only **one** narrator` → `Three scored facts appear correctly in only **one** narrator`, and change the following paragraph `Three of the five sit in narrators carrying a decoy theory (r08, r14) or four near-tie values (r21)` → `Two of the three sit in narrators carrying a decoy theory (r08) or four near-tie values (r21)`.

**14. A2.5 and A3.3 score the same leaf twice.** (A2.5 ⚠️, A3.3 ⚠️)
- `answers-and-scoring.md`, A2.5 — old: `**The 1896 season averaged 3.80 on the borrowed glass; the first full year on the station's own glass, 1898, averaged 3.61, and it stayed at 3.61 for twenty-five years.** Both figures required.`
  new: `**The step is at the change of glassware:** the season on borrowed glass averaged **3.80** and the first full year on the station's own glass averaged **3.61**, with nothing on the farms changing. Both figures required, and the point is credited only where the solver ties them to the 1897 crate; the summary leaf as a document is scored at A3.3.`

**15. The station-gain line is gated three times.** (A1.6, A7.6, A8.6 ⚠️)
- `answers-and-scoring.md`, Scope rule (Section A), after clause 5, add:
  `6. Three items turn on one record — A1.6 (the line's existence, shape and 1898 origin), A7.6 (the account the award was charged to), A8.6 (the identity of its total with 76,000 lb). Each is credited on its own aspect only, and because the ledger belongs to S1, S7 and S8 alike, credit for these three travels among A1, A7 and A8. The same allowance applies to A2.5 and A3.3.`

**16. "Fifteen years" of lactometer readings is in no source.** (A6.2 ⚠️)
- `answers-and-scoring.md`, A6.2 — old: `across fifteen years including 1919 and after` → new: `across the whole circuit, 1908 to 1936, including 1919 and after`.
- `answers-and-scoring.md`, D2 valid-reasons paragraph — old: `**Strawn's fifteen years of clean visits**` → new: `**Strawn's clean lactometer visits from 1908 to 1936**`.
- `answers-and-scoring.md`, F2 — old: `fifteen years of Strawn's lactometer readings` → new: `Strawn's lactometer readings on every visit from 1908`.
- **16b.** `answer-key/AUTHORING-NOTES.md`: state one word-count convention — `Word counts are prose only: the title line, the italic framing note and r10's figure table are excluded. On that basis every retelling is 1,365–1,499 words.` — and note that whole-file counts run 4–107 words over for r09, r10, r11, r12, r22, r23, r24.

**17. G2 lists nine items for "eight record series".** (G2 ⚠️)
- `answers-and-scoring.md`, G2 — old: `Names **at least five of the eight record series**:` → new: `Names **at least five of the nine record series**:`.

**18. C5(a) should accept equivalent exact spans.** (C5a ⚠️)
- `answers-and-scoring.md`, C5(a) — after `**26 years and 6 weeks**`, add: `(accept any exact equivalent: 26 years and 42 days, or 26 years 1 month 11 days)`.

**19. The corruption-deduction list reads as exhaustive and is not.**
- `answers-and-scoring.md`, after the block-quoted list of flagged values, add:
  `This list is not exhaustive. **Any** value catalogued as a planted error in `corruption-map.md` and asserted as fact takes the deduction — including Strawn's circuit begun in **1907**, Selby Vose manager from **1911**, the condemnation reaching the office in **1922**, the award made in **1924**, the crate from Tarnet in **1899**, the condemnation in **1921**, the hearing in **1926**, the Alder Corners overlap of **fourteen seasons**, a **1924 average of 3.85**, and the **1908 committee sitting again in 1925**.`

**20. NT-17's breaker is overstated.** (B3 ⚠️)
- `corruption-map.md`, NT-17 row — old: `The minute book (r02) records "Selby Vose, son of the late president"` → new: `r02, who kept the minute book for forty years, calls him "son of the late president" in her own account`.

**21. Two bolded gates rest on a single narrator.** (A5.3 ⚠️, A6.1 ⚠️)
- `answers-and-scoring.md`, A5.3 — old: `Cudd tested with **his own glassware** and kept **his own test book**` → new: `Cudd tested on his own bench with his own glassware and kept **his own test book**`.
- `answers-and-scoring.md`, A6.1 — old: `and was **related to and employed by nobody in the valley**` → new: `and was related to and employed by nobody in the valley (r18 only; uncontested)`.

**22. A06's negative pole is refuted on dates; say so.** (D1.4 ⚠️, E-c A06 ⚠️)
- `answers-and-scoring.md`, E-c row A06, append to the Correct cell:
  `Note for the grader: r06's own 1911 entry dates his visit to **June**, a month after the 8 May breakage, so r09's pole is impossible on the dates. That eliminates one account without establishing the other; a solver that says so and still declines to name the lender is a correct abstention, and a solver that treats the elimination as a settlement is not.`

**23. A07's negative lean should be explicitly creditable.** (F5 ⚠️)
- `answers-and-scoring.md`, F5, append:
  `A solver that leans negative on r02's "I took every word down and it is not there", r18's "stayed there until Ivy found it" and r21's "Nobody ever gave it a thought", while explicitly declining to decide, is a correct abstention and takes no deduction.`

---

## Author-check reconciliation

The six `author-checks/` files were read only after the audit above was complete. Reconciling the
deviations they record:

| author-recorded deviation | audit finding |
|---|---|
| **r09's postscript dating** (1955 piece must carry the 1958 loan) | ✅ Resolved cleanly: `*Postscript, 1958.*` records the loan and Hazel's reversion only. 1955 + "three years afterward" = 1958, consistent. No scored item affected. |
| **r13's "later shown" rewording** (a 1946 memoir cannot cite a 1958 bulletin) | ✅ Correct decision. The 67,000 lb is carried as "The patrons' own reckoning … and nothing was ever brought forward to disturb that figure" — same value, no hedge, no anachronism. NT-6 still functions as a pair with r21. The key does not require the words "later shown". |
| **r08's banned-word collision** ("the measure of it") | ❌ Not resolvable at the retelling; **the key must move.** The author gave the verbatim brief priority, which was right, but D3.2 asserts as scoreable a fact about r08 that is untrue. Fix 8. |
| **r18's 1970 line** (1968 notes must carry a 1970 deposit) | ✅ Resolved by `*Added, 1970.*` within his lifetime (d. 1971). Supports A5.6 and A4.6 without inventing a source. |
| **r19's Rosalie placement** (carry X78 without naming Alder Corners) | ✅ "Mrs. Rosalie Cudd of Vessey County, of the cheese company over the ridge" carries the niece error with no test figures, no seasons and no comparison. NT-21 intact; S5 stays r10's. |
| **r02's crate context** (one clause to make ⌀X09 intelligible) | ✅ The added clause gives June 1923 correctly, making r02 a third correct carrier for NT-11. Net gain, no leak. |
| **r03's nine-sentence statement** (D9 is two sentences) | ✅ Verified by count: the statement block is exactly nine sentences, D9 verbatim as sentences 8–9, the preceding seven introducing no new figure, date, name or document. |
| **r22's two figures** (¶5 correct, ¶11 X90) — flagged by the author "in case the coverage audit assumed r22 would carry only one" | ⚠️ The author was right to flag it, and the consequence is larger than "internal inconsistency by design": placing 3.85 on the **1924** average rather than on the true average makes r22 a **second uncatalogued wrong carrier of F061**, which is what leaves the 1924 figure at one correct carrier against two wrong ones. Fix 1 addresses it. |
| **the 0.19 / 0.17 canon gap** | ❌ **Not flagged anywhere in the author checks.** The r09 check marks F076 "correct"; the r22 check marks ¶5 "correct"; the r07 check marks "about three-quarters of a point better" "correct" and notes only that the figure 3.78 is absent. The defect is upstream in `canon.md` (F098a vs F076) and in the r07 and r09 narrator briefs, which instruct exactly what was written. Fixes 10, 11, 12, 13. |

---

# Fixes applied 2026-08-28

All twenty-three required fixes applied, plus the four controller rulings and the consequential
edits each forced. Line numbers are **post-edit**. Paths are relative to `v3/`.

## The four rulings

**Ruling 1 — Section A scope.** The per-story filing gate is withdrawn: a checklist fact is now
credited wherever it appears inside the eight reconstructions, and credit still never travels in
from B–G. `answers-and-scoring.md` 25–47 (the rule rewritten, five clauses to four). The
checklist was deduped: the one true duplicate — the test book's summary leaf, scored at both A2.5
and A3.3 — is merged into **A3.3** (138–143), and the freed point is spent on a new **A2.5**
(123–127): *the shortfall was flat at 0.19 in every month of the year*, canon **F097/F100**,
carried correctly by r03, r04, r17 and r22 — a distinct fact, scored nowhere else in Section A.
Section A therefore stays at 50 items and the sub-sheet is unchanged (6·6·7·6·6·6·6·7). **No
partition item was added**: the merge freed one point and the offered partition item costs two,
and no second genuine duplicate exists. Instead, the four cases where two or three items rest on
one record — A1.6/A7.6/A8.6, A3.1/A7.5, A6.6/A8.3, A6.5/A7.1 — are enumerated in clause 4 and each
is credited **on its own aspect only**, which is fix 15 in its new form. Consequential:
`narrator-briefs.md` 1085 (the ≥2-carrier check row for A2.5); `corruption-map.md` 595 (the NT-3
consequence row pointed at A2.6 and should always have pointed at the leaf — now A3.3);
`AUTHORING-NOTES.md` 36–41, 114, 137, 168–172, 176–179 (lever 2, § 3 and soft spots S1/S2 restated
against the revised rule). `test-input/questions.md` needed no edit: its Section A note already
said credit is given for what appears *inside this section*, which the revised rule now matches.

**Ruling 2 — the 1924 average.** r06 is the second carrier, per fix 1. One sentence added in his
voice to the 1924 extract — *"Their book gives the year at 3.80."* —
`test-input/retellings/r06-extracts-from-the-circuit-books.md` 44 and `test-input/bundle-single.md`
236. His brief forbade every test average, so the brief moved with him:
`narrator-briefs.md` 290–293 (the 1924 extract now carries the figure) and 302–306 (the
must-not-mention list gains the single exception). Carrier lists corrected at
`answers-and-scoring.md` 408 (E-a row 3), `corruption-map.md` 698 (F103) and 660 (F061).

**Ruling 3 — A10's third pole.** The 1893 date is out of the quoted 1908 report and into Grigg's
own 1919 covering letter, where it is memory: `r15-grigg-committee-report.md` 13 (the new
sentence) and 33 (the clause struck from the quoted report); `bundle-single.md` 733 and 753. D15
itself is untouched. Map updated at `corruption-map.md` 356 (⌀X58 now records that the pole must
stay outside the quoted report or a document would settle A10); brief updated at
`narrator-briefs.md` 674–677.

**Ruling 4 — the 0.17 gap.** Canon is authoritative and now says so: `canon.md` 191 (F098a states
the visible gap as **0.17** and forbids stating the Larrow Green comparison as 0.19). The map
assigns r09 no planted error on the figure, so r09 was corrected to canon rather than catalogued:
`r09-my-fathers-book.md` 23 and 25, four occurrences of *nineteen hundredths* → *seventeen
hundredths* (`bundle-single.md` 422, 424); brief at `narrator-briefs.md` 406–410. The map likewise
assigns r07 no error on "about three-quarters of a point", so it too was corrected to canon (fix
10): `r07-accession-notes.md` 107, `bundle-single.md` 360, brief at `narrator-briefs.md` 331–334.
Consequential: F076's correct carriers become **r04 and r22 ¶5** (`corruption-map.md` 671, and
NT-4 at 569), and F098a's row now separates the figure (r14, r22) from the comparison (r07, r09)
at 645.

## The twenty-three fixes

| # | What | Files and lines |
|---|---|---|
| 1 | The 1924 average has one correct carrier and two wrong ones | `r06…md` 44; `bundle-single.md` 236; `answers-and-scoring.md` 408; `corruption-map.md` 698, and consequentially 660 (F061) and 504 (X90 recorded as a second wrong carrier of F061); `narrator-briefs.md` 290–293, 302–306 |
| 2 | Strawn's first circuit — wrong carriers named | `answers-and-scoring.md` 413; `corruption-map.md` 629; `narrator-briefs.md` 1099 |
| 3 | Selby Vose's start as manager — wrong carrier named | `answers-and-scoring.md` 420; `corruption-map.md` 627 |
| 4 | Weigh-book start — two correct carriers uncredited | `answers-and-scoring.md` 410 |
| 5 | The 1908 sampling — r09 is not a Jan–Mar carrier | `answers-and-scoring.md` 407 |
| 6 | E-a row 1 is also NT-13 — double credit possible | `answers-and-scoring.md` 423–424 |
| 7 | The burned church register is not in the corpus | `answers-and-scoring.md` 267–269 (B2), 281–282 (B4); `canon.md` 100 (F039), 335 (A01), 342 (A08) |
| 8 | The "glass, pipette or measure" claim is false of r08 | `answers-and-scoring.md` 384–386 (D3.2), 388–390 (D3.3); consequentially `canon.md` 337 (A03 carried the same false gate) |
| 9 | A10's third pole sat inside a quoted document | see ruling 3 |
| 10 | r07's Larrow Green comparison was arithmetically impossible | see ruling 4 |
| 11 | r09 attached the true shortfall to the Larrow Green comparison | see ruling 4 — resolved by the ruling's fallback (0.17), not by fix 11's rewrite, which would have had a 1955 farmer state a figure first established in 1958 |
| 12 | A4.3's parenthetical misstated the record | `answers-and-scoring.md` 165–168 |
| 13 | The single-source table is wrong on two of its five rows | `corruption-map.md` 707 (five → three), 711–715 (the 3.78 and four-exhibits rows deleted), 717–720 (paragraph rewritten; the stale A7.4 reference dropped and both facts' second carriers named) |
| 14 | A2.5 and A3.3 score the same leaf twice | `answers-and-scoring.md` 123–127, 138–143 — applied in ruling 1's form (merge, not disambiguation) |
| 15 | The station-gain line is gated three times | `answers-and-scoring.md` 41–47 — applied in ruling 1's form: an enumerated no-double-credit clause, since credit now travels anyway |
| 16 | "Fifteen years" of lactometer readings is in no source | `answers-and-scoring.md` 203–204 (A6.2), 359 (D2), 475 (F2); consequentially `corruption-map.md` 700 (F105) and 731 (device checklist), `narrator-briefs.md` 280–281 (r06's vantage) |
| 16b | One word-count convention | `AUTHORING-NOTES.md` 232–236 |
| 17 | G2 lists nine items for "eight record series" | `answers-and-scoring.md` 508 |
| 18 | C5(a) should accept equivalent exact spans | `answers-and-scoring.md` 324–325 |
| 19 | The corruption-deduction list reads as exhaustive | `answers-and-scoring.md` 73–79 |
| 20 | NT-17's breaker is overstated | `corruption-map.md` 582 |
| 21 | Two bolded gates rest on a single narrator | `answers-and-scoring.md` 186–187 (A5.3), 200–201 (A6.1) |
| 22 | A06's negative pole is refuted on dates | `answers-and-scoring.md` 447 |
| 23 | A07's negative lean should be explicitly creditable | `answers-and-scoring.md` 494–496 |

## Verification

- **Word counts.** Prose only (title line, italic framing note and r10's figure table excluded),
  all twenty-four retellings **1,365–1,499**. The four edited files: r06 1,451 · r07 1,447 · r09
  1,493 · r15 1,425. All inside 1,000–1,500.
- **Score sheet.** Section A = 50 items across eight stories (6·6·7·6·6·6·6·7); A 50 + B 8 + C 14 +
  D 10 + E 8 + F 6 + G 4 = **100**. No point value changed.
- **Block quotes.** All sixteen canon documents were matched against the retellings after editing
  and every one is byte-identical where it stood before. The only block-quoted line touched is the
  body of r15's expanded 1908 report, which is not a canon document; **D15**, the canonical
  paragraph inside it, is untouched.
- **Not applied.** Nothing. `test-input/questions.md` was examined and needed no change (above).
