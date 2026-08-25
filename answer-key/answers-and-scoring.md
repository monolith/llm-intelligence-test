# Answers & Scoring Key (SECRET — never show to the system under test)

Total: **100 points.** Sections C, E and the checklists in A are objective (exact match /
tolerance stated). A, D, F and G are scored as **yes/no checklists** — each item is worth
1 point and is either present or not; no partial credit, no point bands. B is scored per
the stated criteria. Use a human or an independent judge LLM that is given this key and
the canon, never the system under test, and never a model from the same family as the
system under test.

Why yes/no items: judges given one binary question per item agree with expert human
raters at 87–94%, versus 36–77% when handed a holistic or point-band rubric for the same
material (MultiChallenge, Findings of ACL 2025; MT-Bench-101, ACL 2024). Validate the
judge once: hand-score two runs, compute Cohen's κ per section against the judge, and
report κ — not percent agreement — alongside the scores.

General deductions (apply anywhere): **−1 per planted corruption asserted as fact**
(e.g., "the bell drowned," "Gate 2," "£46," "eleven stumps," "grandson," "1907 onset,"
"drought of 1966," "filled in 120 days," "quarter inch," swapped authorship, "Keel
orchard," "Elsa"). Hedged mentions ("one source wrongly says…") are not penalized —
they earn E1 credit instead. Floor of 0 per section.

## Section A — Reconstruction (30 pts: 10 per story, 1 pt per fact)

**A1 checklist (Story 1):**
1. Ilsa Voss, young Aldercote-born woman, measurer/computer for the Selde Weir Co., mid-1900s
2. She and brother Tomas from the Voss orchard family; Tomas, a carpenter, built the gate shutters
3. Weir: 5 gates × 12 ft; reservoir 1,440M gallons
4. Corven promised 120-day fill; Ilsa corrected to 144 (12−2=10M/day net); actual 147
5. 1905: Gate No. 3 trunnion pin 3⅞ in vs 4 in spec, blowhole
6. Flagged to Corven; overruled (six-week recast delay); recorded in her ledger (p. 47 / signed I.V.)
7. Gate 3 culvert lip (invert) at the 14-ft gauge mark
8. Church bell sold March 1906, £64, Harden foundry, graves fund
9. Ilsa dismissed 1906 over her private duplicate ledger; kept it (later the sole surviving record after the 1921 office fire)
10. Married Henrik Keel, schoolmaster (1908); the ledger stayed with her

**A2 checklist (Story 2):**
1. Aron Keel, Ilsa's son (b. 1909), took the Marrow Bend school ~1929
2. Lore: drowned Aldercote bell tolls for the dead
3. Log: 17 winters, 43 tolling nights
4. Every tolling night: east wind AND gauge below 14 ft
5. 6 further qualifying nights with no tolling (conditions not sufficient)
6. Deaths test: 9 deaths, only 2 coincident → lore debunked
7. Wager: 1 Nov 1930 = 16'6", 3 in/week → sub-14 ~10 Jan; first heard 21 Jan 1931; won
8. Peak winter 1933/34 = 7 nights; first reports winter 1918
9. March 1946 refit (new pins) → permanent silence, incl. 4 qualifying nights the next winter; baffled final entry
10. 1949: inherited Ilsa's deed-box (green ledger + dismissal letter); shelved in the school attic

**A3 checklist (Story 3):**
1. Drought, September 1968; gauge 9'4" record low; lakebed walkable
2. Vera Brandt (b. 1941), botanist; Margit's daughter, Tomas's granddaughter
3. "Glass orchard": preserved stumps of the Voss orchard
4. 9 stumps sectioned; oldest 88 rings, outermost 1906
5. Pinched rings 1893 & 1902 match the ledger's low-flow years (cross-dating)
6. Church bell chamber empty (headstock and wheel only)
7. Found ledger + log together (parish/museum custody after Aron's death, 1966)
8. Connected p. 47 + the 14-ft invert + the log's 14-ft threshold
9. Found the original Gate 3 pin in the culvert mud, worn oval; 1946 pins visibly new
10. Concluded: loose Gate 3 knocking in an air-filled culvert — "no ghost; a hinge"; material deposited at the Harden museum

## Section B — Relationships (10 pts: 2 each)

- **B1.** Sister and brother. (2)
- **B2.** Son. Evidence: R4 (family) says son, b. 1909 of the 1908 marriage; R3's "grandmother" fails arithmetic — Ilsa b. 1880 could not have a grown grandson teaching in 1929. Both the answer (1) and the resolution (1).
- **B3.** First cousins once removed: Aron and Margit were first cousins (children of Ilsa and Tomas); Vera is Margit's daughter. Derivation required for full credit; "cousin" alone = 1.
- **B4.** The Voss family's. R6's "Keel orchard" is the archivist's own flagged guess; R4 (family authority) and the derivation (Ilsa/Tomas raised in it, née Voss) settle it. (2)
- **B5.** Ilsa kept the ledger from 1906 → deed-box to Aron at her death (1949) → school attic beside his log → after Aron's death (1966) into the parish chest → found by Vera (1968) → Harden museum. 4+ links correct = 2; 3 links = 1.

## Section C — Math (20 pts: 4 each; exact match unless stated)

- **C1.** 1,440 ÷ (12 − 2) = **144 days**; actual **147**. (Working 2, both numbers 2.)
- **C2.** **⅛ inch** (3⅞ vs 4), = **3.125%** (accept 3.1%). Must reject the ¼-in claim via document/majority. (Fraction 1, % 1, resolution 2.)
- **C3.** 16'6" − 14' = 30 in; 30 ÷ 3 = 10 weeks from 1 Nov 1930 → **~10 January 1931** (accept 8–12 Jan). (Working 2, date 2.)
- **C4.** 1906 − 88 + 1 = **1819**. (Accept 1818 with explicit off-by-one/planting-year reasoning; bare 1818 = 2.)
- **C5.** (a) 43 ÷ 17 = **2.5** (accept 2.5–2.53). (b) 43 + 6 = **49**. (2 each.)

## Section D — Logic (15 pts: 5 yes/no items per question, 1 pt each)

**D1 checklist:**
1. States that both conditions were necessary (or "consistent with necessary")
2. Grounds necessity in the log count: all 43 tolling nights had both conditions
3. States that the conditions were not sufficient
4. Grounds insufficiency in the counterexample: 6 qualifying nights with no tolling
5. Keeps "necessary" and "sufficient" distinct as concepts (does not conflate or reverse them)

**D2 checklist** (valid reasons: documentary — bell sold 11 Mar 1906 for £64, before the
tolling era [R6, R4]; physical — chamber empty in the drought survey [R4, R6]; mechanical —
tolling ceased immediately after a gate refit, which no submerged bell would care about
[R3, R5, R1]; hydrological — 1918 onset tracks draw-down crossing 14 ft [R5]):
1. First valid, distinct reason given
2. Second valid, distinct reason given
3. Third valid, distinct reason given
4. Each reason is attributed to a narrator (not asserted bare)
5. The reasons come from at least three different narrators

**D3 checklist:**
1. (a) Onset explained by winter draw-down first taking the gauge below 14 ft
2. (a) The 14-ft mark is identified as the Gate 3 culvert lip/invert (drowned culvert = silent)
3. (a) Names war-era mill demand (~1918) as what pushed draw-down that low
4. (b) Cessation explained by the March 1946 refit (new pins)
5. (b) States what the refit removed: the slack from the worn/undersized Gate 3 pin

## Section E — Contradictions (10 pts)

1 pt each, awarded only when found AND correctly resolved with a stated method (max 8
from this list, any 8 count):

1. Gate number: 2 (R1) vs 1 (R5's attribution) vs 3 (R2, R6, R5's pin fact) → 3.
2. Bell fate: drowned (R1) vs sold 1906 (R6 quote, R4) → sold.
3. Fill time: 120 "as promised" (R4) vs 144 computed/147 actual (R2) → arithmetic.
4. Pin undersize: ¼ in (R2) vs ⅛ in (R5, R6 quote) → document.
5. Bell price: £46 (R4) vs £64 (R6 quote) → document beats memory (transposition).
6. Stump count: 11 (R4) vs 9 (R6) → document.
7. Drought year: '66 (R5) vs Sept 1968 (R6; R4's "two years after Aron died") → 1968.
8. Aron's relation: grandson (R3) vs son (R4) → birth-year arithmetic.
9. Tolling onset: 1907 (R3) vs 1918 (R5, with mechanism) → 1918.
10. Ledger/log authorship: R6's pencilled swap vs its own "I.V." signature + R3/R4 → swapped.

**+2 bonus** (within the 10-pt cap) for explicitly identifying R6's *internal*
inconsistency (attribution vs. signature) as self-refuting.

## Section F — Theory (10 pts: 10 yes/no items, 1 pt each)

**F1 checklist:**
1. Names the Gate 3 trunnion pin as undersized / worn / slack
2. States that the slack lets the gate rock or knock in its frame
3. States that the empty culvert resonates the knocking into the bell-like toll
4. Identifies the 14-ft threshold as the culvert invert (lip)
5. Explains the threshold physically: below 14 ft air enters the culvert; above it, water damps the sound
6. Names the east wind as the driving force that rocks the gate
7. Handles the silent qualifying nights honestly (wind not sustained through the night / conditions necessary but not sufficient), rather than ignoring them
8. Explains the 1918 onset as winter draw-down first crossing the invert
9. Explains the permanent cessation as the March 1946 re-pinning
10. Names the confirming physical evidence: the worn-oval original pin recovered from the Gate 3 culvert mud in the drought year

## Section G — Summary (5 pts: 5 yes/no items, 1 pt each)

**G1 checklist:**
1. At most 120 words
2. Names all three protagonists (Ilsa, Aron, Vera) and states their family link
3. Arc start present: the flaw was flagged and overruled
4. Arc end present: decades of misattributed, logged tolling were resolved by the drought-year evidence
5. Contains no canon contradiction and no absorbed planted corruption

## Score sheet

| Section | Max | Score |
|---|---|---|
| A Reconstruction | 30 | |
| B Relationships | 10 | |
| C Math | 20 | |
| D Logic | 15 | |
| E Contradictions | 10 | |
| F Theory | 10 | |
| G Summary | 5 | |
| Corruption deductions | (−) | |
| **Total** | **100** | |

Suggested bands: 85+ excellent (near-full reconstruction, correct arbitration of all
conflicts); 70–84 strong (reconstruction sound, some conflicts unresolved); 50–69
moderate (narrative recovered, arbitration weak — swallows 2+ corruptions); <50 weak
(cannot separate the three strands or reproduce the interlocking numbers).
