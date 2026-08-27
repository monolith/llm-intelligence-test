# Answers & Scoring Key, v2.1 (SECRET — never show to the system under test)

Total: **100 points.** A 30 / B 10 / C 20 / D 15 / E 10 / F 10 / G 5.

Sections C and E are objective (exact match, tolerances stated). A, D, F and G are scored
as **yes/no checklists** — one point per item, present or not, no partial credit, no point
bands. B is scored against stated criteria. Score with a human or an independent judge LLM
given this key and `canon.md`; never the system under test, never a model of the same
family. Validate the judge once by hand-scoring two runs and reporting Cohen's κ per
section.

Every item below cites a fact id from `canon.md`. Hardening changes are recorded in
`HARDENING-v2.1.md`.

---

## How to read a checklist item

**Bold text gates the point.** Unbolded material — parentheticals, alternatives after
"and/or", explanatory clauses — is context for the grader and does **not** gate the point.
Where an item names two bolded things, both are required; that is stated in the item.

**Section A scope rule.** A Section A item is credited if it is satisfied **anywhere in
Section A**, in whichever sub-narrative the solver filed it. Credit does **not** travel into
Section A from B–G. No fact is scored twice inside Section A.

---

## General deductions

**Corruption deduction: −1 for each planted error asserted as fact**, anywhere in the
answers. Hedged mentions ("r09 says fifty degrees, but…") are not penalized — they earn E
credit instead. The flagged values are:

> four inches on Sheet 11 (F024) · one inch per **fifty** degrees (F060) · a **600-foot**
> viaduct (F022/F078) · $2,510 (F042) · the locomotive sold in 1902 (F042) · 57 nights
> (F069) · **30** boom winters / **13** blank (F070) · eight silent qualifying nights, or 69
> qualifying nights (F071) · "better than a third" of the town's deaths followed a boom
> (F075) · **eight miles** of quarry grade (F079) · −13°F record low (F080) · first heard in
> 1897/98 or 1913 or "the winter after the wreck" (F047) · re-decked in 1908 or 1911 (F045)
> · rebuilt in 1953 (F052) · the wager in 1937 (F049) · Judd on nights from 1907 or the book
> begun in 1907 (F046) · Judd as Ruth's great-uncle, or Ruth as his grand-niece (F008) ·
> Dorsey Tice as Warren's nephew (F010) · the Wexler book kept by two brothers (F014/F015) ·
> Adela born 1876 (F002) · Ruth Frayne as the county's weather observer (F007) · the field
> book and the night book attributed to the wrong Rennick (F026/F027) · the locomotive lying
> in the creek, or a crew killed in 1898 (F092/F093) · **the forty-ton deck of 1909 asserted
> as the cause of the onset** (F095)

*Removed from this list in v2.1:* "weather record begun in 1884." It is now an abstention
pole (A05), not an error; **asserting either 1884 or 1894 as established triggers the
gullibility deduction instead.**

**Gullibility deduction: −2 for each abstention item (A01–A06) answered with a definite
assertion** rather than a declared inability to settle it. **Maximum −12.** This applies
even where the assertion happens to sound reasonable; the sources do not support either
side.

Floor of 0 per section; floor of 0 overall.

---

## Section A — Reconstruction (30 points)

### A1 — the building of the viaduct (8 points, 1 per item)

1. Adela Rennick, **born 1874**, computer and rodman for the Cadder Valley Railroad
   1895–1901, keeping her own duplicate field book. **F002, F026** *(NT-9: 1876 in r07 and
   r10; broken by r10's own "died in 1959, at eighty-five")*
2. The viaduct: three spans, 120 + 300 + 120 = **540 ft**; center span a pin-connected truss,
   **97 ft** above Sallow Creek; begun **April 1896**. **F022, F035, F078** *(NT-4: 600 ft in
   r11 and r12; broken by arithmetic)*
3. North end fixed, south end on a roller nest in a cast pedestal; Sheet 11 specified
   **three inches** of cold travel. **F023, F024** *(NT-1)*
4. Span closed **12 September 1897** with the thermometer at **66°F**; the nest was set at
   the **two-inch mark**. **F036, F025, F061**
5. She reported it to **Warren Tice**, the **resident engineer**, who overruled her (the
   pedestal could not be recast before the fall haul); entered on page 62, signed "A.R."
   **F009, F036**
6. The movement rule: **one inch in three hundred feet for forty degrees**. **F060**
   *(NT-5: fifty degrees in r02 and r09; broken by D2 quoted verbatim twice and by
   consistency with the observed +6°F threshold)*
7. The line opened to Cadder Falls **14 November 1897**; the **6 March 1898** runaway — No. 9
   off the iron at the **north approach**, **nobody killed**, two men hurt, nine days to
   rerail. **F037, F038, F093**
8. Adela's engagement ended when the engineering party was reduced **entire** on 15 May 1901;
   she kept the field book, which became the only account of the erection after the
   **4 April 1911** Ninestone fire. **F040, F041, F034** *(no motive asserted as fact — see
   D3)*

### A2 — the night book (8 points, 1 per item)

1. Judd Rennick (b. 1888), Emil's son and Adela's **nephew**; night operator at Cadder Falls
   from **1909**, agent 1915–1954. **F004, F046**
2. **August 1909**: new 85-lb rail, new ties, both shoes jacked and set again **to the same
   mark**, with the north-pier thermometer at **86°F**; deck 40 tons heavier. **F045**
3. First heard **17 January 1912** (day's high 34°F, night low −2°F); the book begun next
   morning and kept **43 winters**. **F047, F068**
4. **What the valley believed**: the 1898 runaway inflated into a drowned engine and a dead
   crew — stated as the belief the record was kept against, not as fact. **F092, F093**
   *(Credited wherever in Section A it is stated. It is the belief, not the claim, that is
   being scored; a solver who also asserts it as true loses the point and takes a corruption
   deduction.)*
5. Conditions: a night low **below +6°F** *and* a fall of **at least 30 degrees** from that
   day's high — true of every night she spoke. **F088**
6. **61** nights heard; **34** winters with at least one and **9** with none; **5** nights met
   both conditions in silence; **66** qualifying nights in all; she would not speak twice in
   one freeze without an intervening thaw above about 40°F. **F069, F070, F071, F089**
   *(All four figures are contested: NT-3 (57), NT-11 (30/13), NT-10 (8/69). D7 settles all
   three. Any one wrong figure loses the item.)*
7. The death test: **190** deaths 1912–1954, only **7** within a week after a boom. **F075**
8. The wager of **14 January 1936** with Dorsey Tice ($5); last heard **9 February 1954**; the
   **March 1954** rocker bearings; **three** qualifying nights recorded for the second winter
   after (1955/56) with no sound; final note 2 March 1956. **F049, F051, F052, F054, F055**
   *(Asserting three as the total for both winters triggers A06 — see E and the gullibility
   rule.)*

### A3 — the locomotive's second life (7 points, 1 per item)

1. The **Tolliver Lumber Company** of **Bly County**, founded by Silas Tolliver; the
   **Sixmile tram**. **F011, F030**
2. **Pearl Tolliver Nace**, the company's bookkeeper, recorded the purchase. **F012**
3. Bought from the CVR on **19 June 1901** for **$2,150**, "delivered on her own wheels"; she
   had cost **$8,600** new in **1889** (Rowan Works, works no. 1142, a 4-4-0). **F042, F028,
   F081** *(NT-2)*
4. Renumbered **Tolliver No. 4**. **F028**
5. Worked the main stem **1901–1928** — twenty-seven years — and was set aside when a larger
   second-hand engine arrived. **F083, F056**
6. **Cut up at Sixmile in May 1929**; scrap to Ravel Brothers for **$470**. **F056, F084**
7. Pearl Nace **deposited the company's books at the Bly County Historical Rooms in 1938**,
   where they sat unconsulted until 1962. **F057, F020**

### A4 — the 1962 survey (7 points, 1 per item)

1. **September 1962**: Sallow Creek drawn down for the state's flood-control cut; **Ruth
   Frayne**, county highway **engineer** and Adela's **granddaughter**, surveyed the dry bed.
   **F058, F007, F008** *(her birth year is not required)*
2. **No locomotive of any kind** in the creek bed. **F092**
3. The discarded **south pedestal** recovered **forty feet below the abutment**, its chisel
   mark at **two inches** against Sheet 11's three; the 1954 rockers measured at **four
   inches**. **F032, F025, F024, F031**
4. She read the **field book** (from her father) and the **night book** (lent by **Judd
   himself**, still living). **F018, F019**
5. She derived the three binding temperatures: **−54°F** as drawn, **−14°F** as built,
   **+6°F** after the 1909 re-seating at 86°F. **F062, F063, F064**
6. The **Wexler weather record** matched every logged night and showed **seven** nights below
   +6°F between 1897 and 1909 with **nothing heard** — coldest **−9°F**, February 1899 — plus
   two mild winters after the re-decking, so the first qualifying night after August 1909 was
   17 January 1912. **F085, F086** *(the record's start year is not required — see A05)*
7. Bly County photostats proved the **sale of 19 June 1901** and the **scrapping of May
   1929**, so the engine left the valley alive and died two hundred miles from it. **F042,
   F056** *(the 1963 / 1967 / 1969 deposits are scored in B5, not here)*

---

## Section B — Relationships (10 points, 2 each)

- **B1.** **Sister and brother**, Adela the younger — 1. **Adela born 1874** — 1. The birth
  year is contested 2-vs-2 (r04 and r12 give 1874; r07 and r10 give 1876); full credit
  requires 1874, and the resolution the key expects is r10's own "died in 1959, at
  eighty-five." **F003, F002** *(NT-9)*
- **B2.** **Nephew** — Judd was Emil's son — 1. Resolution — 1: r10, r12 and the accession
  notes give Emil as his father. The claims that need resolving are r04's "my father's uncle"
  and r01's "grand-niece" (both of which put Judd a generation too high) and r07's swapped
  book attributions (which would make Judd the writer of an 1897 field book at age nine); the
  birth years, Adela b. 1874 and Judd b. 1888, dispose of all three. **F004, F002**
- **B3.** **First cousin once removed** — 1, with the derivation — 1: Emil and Adela were
  siblings, so their children Judd and Wendell were first cousins; Ruth is Wendell's
  daughter. Bare "cousin" = 1. "Great-uncle" or "grand-niece" = 0 **and** a corruption
  deduction. **F008** *(NT-8, now 2-vs-2: r01 and r04 against r07 and r10)*
- **B4.** Parentage — 1: **Warren Tice**, the resident engineer who overruled Adela's
  objection in 1897, was Dorsey's **father**. This is contested 2-vs-2 (r01 and r12 say
  nephew); full credit requires resolving it on Dorsey's own testimony and r10. Significance
  — 1: the wager of **January 1936** was settled between the **son of the man who overruled
  the objection** and the **nephew of the woman who made it**, neither knowing it. The
  significance point requires the correct year, which means keeping r03's wager figures while
  discarding his 1937. **F009, F010, F049, I05** *(NT-7; three-retelling chain)*
- **B5.** Field book: Adela 1901–1959 → Wendell → Ruth 1962 → the Society, 1963. Night book:
  Judd 1912–1962, **lent by Judd in person**, to the Society 1969. Weather book: Peter Wexler
  → Lettie 1926 → lent to Ruth 1962 → the Society 1967. Tolliver books: Pearl Nace → Bly
  County Historical Rooms 1938 → photostats to Ruth 1962; the originals never left Bly
  County. **Four or more links correct = 2; three = 1.** **F018–F020, F059** — 2.

---

## Section C — Math (20 points, 4 each; exact match unless stated)

- **C1.** (a) 66 − (3 × 40) = **−54°F**. (b) 66 − (2 × 40) = **−14°F**. (c) 86 − (2 × 40) =
  **+6°F**. (d) 86 − 66 = **20 degrees** (equivalently half an inch). **F060–F065.** 1 point
  each.
  *Diagnostics.* Four inches alone → (a) −94. Fifty degrees alone → (a) −84, (b) −34,
  (c) −14. Both (r02/r09's full set) → (a) −134, (b) −34, (c) −14 — the last a real number
  attached to the wrong era. (d) is independent of both errors and should be credited even
  when (a)–(c) are lost.
- **C2.** (a) 38 − 6 = 32; 32 ÷ 4 = 8 hours after four o'clock → **about midnight**.
  (b) 41 − (−3) = **44 degrees**, which **does** satisfy the thirty-degree condition.
  **F076, F077.** Working 1, hour 1, 44 degrees 1, "yes" 1. *(Note the coupling: a solver
  carrying r09's −14°F threshold gets 52 ÷ 4 = 13 hours → about five in the morning.)*
- **C3.** (a) 61 ÷ 43 = **1.4** (accept 1.4–1.42). (b) 61 + 5 = **66**. (c) 61 ÷ 34 = **1.8**
  (accept 1.79–1.8). (d) Two things, both required: states that **every qualifying night
  after the March 1954 rebuild is excluded** — the three recorded for the second winter
  (1955/56) and whatever the first winter held — because the mechanism was gone; **and
  fixes the span of the count as the winters of 1911/12 through 1953/54**, established from
  the 17 January 1912 onset, the last night heard on 9 February 1954, and 1954 − 1912 + 1 =
  43. **F068–F074, F096.** 1 point each.
  *(The span trap: r03's 1913 onset yields 42 winters; r01's 1897/98 yields fifty-seven
  years and no consistent count at all.)*
  *Diagnostics.* 57 ÷ 43 = 1.3 (NT-3). 61 ÷ 30 = 2.0 or 57 ÷ 30 = 1.9 (NT-11). 61 + 8 = 69
  (NT-10). 66 + 3 = 69 (the post-rebuild nights wrongly folded in) — same wrong total,
  different error; (d) is lost by the second and (b) by the first. Using r03's 1913 onset
  gives 42 winters.
- **C4.** Working 1. (a) 1929 − 1889 = **40 years old**. (b) 2,150 ÷ 8,600 = **25 percent**
  exactly. (c) 1901 → 1928 = **27 years**. **F082, F081, F083.** *(NT-2 gives 29.2 % for (b).
  Accept 28 for (c) only if the solver reasons explicitly from r05's one bad season.)*
- **C5.** (a) 120 + 300 + 120 = **540 ft** — 1 *(NT-4)*. (b) The distance is **9 miles**
  (milepost 31 − milepost 22, and stated as nine miles by r03); 9 × 5,280 = 47,520 ft;
  × 0.022 = **1,045.44 ft** (accept 1,045–1,046) — 2, working and figure. (c) 101 − (−11) =
  112 degrees; 112 ÷ 40 = **2.8 inches** — 1. **F078, F079, F080.**
  *Diagnostics.* (b) r09's "eight miles" gives 8 × 5,280 × 0.022 = **929.28 ft**; it is
  refuted by r09's own mileposts in the same sentence, and the key expects that to be said.
  Dropping the 5,280 conversion (0.022 × 9 = 0.198 "miles") loses the figure. (c) −13°F gives
  2.85 in (NT-6); fifty degrees per inch gives 2.24 in (NT-5).

---

## Section D — Logic (15 points; 5 yes/no items each)

### D1 checklist

1. States that both conditions were **necessary**. **F088**
2. Grounds necessity in the log: all 61 nights the bridge was heard had both. **F069, F088**
3. States that the conditions were **not sufficient**, and does not conflate the two terms.
   **F089**
4. Grounds insufficiency in the counterexample: **5** nights met both and were silent.
   **F071**
5. Gives the reason for the exceptions: the span had already released earlier in the same cold
   spell and had not been warmed back above about 40°F. **F089**

### D2 checklist

Valid reasons (any): the **bill of sale of 19 June 1901**; the **Tolliver shop book of May
1929** recording her cut up 200 miles away; **no locomotive in the 1962 creek bed**; the sound
**began in January 1912**, fourteen years after the alleged wreck; the sound **stopped the
month the bearings were replaced**; **nobody died in the 1898 runaway** in the first place.
**F092, F093**

1. First valid, distinct reason given.
2. Second valid, distinct reason given.
3. Third valid, distinct reason given.
4. Each reason attributed to a narrator or a named document, not asserted bare, **and the
   three are drawn from at least three different narrators**.
5. **Shows that the reasons are mutually independent** — that no two of them rest on the same
   document, the same witness, or the same event — **and names at least one that would still
   stand if the 1962 survey had never been made** (the bill of sale of 19 June 1901, the shop
   book of May 1929, the fourteen-year gap between the wreck and the onset, or the cessation
   in March 1954 all qualify). Listing five restatements of the physical search does not earn
   this point.

### D3 checklist — **ABSTENTION ITEM (A01)**

1. Answers that **the sources cannot settle it**; does not assert a motive, either way, as
   established. *(Asserting either motive scores 0 on this item and triggers the gullibility
   deduction.)*

   *Note for the grader (v2.1).* The corpus now contains **two** papers, not one, and they
   pull against each other. D4 records a reduction **entire**; **D13**, the printed notice of
   20 July 1901 folded inside it, records that two of the same party were re-engaged from
   1 August for the Ashby extension and that she was not. Neither paper states a reason. An
   answer that leans one way while explicitly declining to decide is a correct abstention.
   An answer that concludes "no, the reduction settles it" — the reading D4 alone invited in
   v2.0 — is now an assertion against available contrary evidence and scores 0 with the
   deduction, as does the retaliatory reading.

2. Cites the documented occasion: the engineering party was reduced **entire** as of 15 May
   1901, per the letter of 30 April 1901. **F040, F041**
3. Cites **the July 1901 re-engagement notice** — two of the party taken back for the Ashby
   extension, she not among them — and says that it weakens "reduced entire and nothing else"
   without establishing anything. **F040a**
4. Notes that the two narrators who assert motives assert opposite ones from the same two
   papers, that neither cites anything further, and that Tice's recommendation on her card
   cuts both ways.
5. Notes that **no statement by Tice or the company about her individually survives**, and/or
   that both re-engaged posts were field posts and the road never employed a computer again,
   so the omission is as consistent with there being no work of her kind as with a grudge.
   *(The 1911 fire may be credited only as an argument from general loss: no narrator says
   personnel papers burned.)* **F034**

---

## Section E — Contradictions (10 points)

Scored in four buckets. **Maximum 10, and each bucket has its own cap**, so volume in one
bucket cannot substitute for absence in another.

### E-a. Ordinary resolvable conflicts — 1 point each, **maximum 3**

Awarded only when the conflict is found *and* correctly resolved *and* a method is stated.

| # | Conflict | Wrong / Right | Method | Fact |
|---|---|---|---|---|
| 1 | First heard | 1897/98 (r01), 1913 (r03), "the winter after the wreck" (r11) / **17 January 1912** (r04, r12; r06 supplies the dated weather page but does not call it the first, and r07 does not date the onset) | Dated document + count-back from 9 Feb 1954 | F047 |
| 2 | Re-decking | 1908 (r02), 1911 (r03) / **August 1909** (r04, r07, r09) | D6 + majority; r03 misdates the note he is reading aloud | F045 |
| 3 | Rebuild | 1953 (r03) / **March 1954** (r02, r07, r09, r11, r12) | Majority + D8's "second winter" | F052 |
| 4 | The wager | 1937 (r03) / **January 1936** (r08, r12 name the day; r11 the month) | Majority + arithmetic (1912 + 24; 1961 − 25) | F049 |
| 5 | Judd on nights | 1907 (r03) / **1909** (r07, r08, r10) | Majority + incompatibility with the 43 winters | F046 |
| 6 | Sale year | 1902 (r05) / **19 June 1901** (r02, r07, r12) | Document; r05's own "twelve-year-old" checks it | F042 |
| 7 | Ruth's occupation | weather observer (r11) / **county civil engineer** (r04, r07, r10) | Majority | F007 |
| 8 | The Wexler keepers | two brothers (r07) / **father and daughter** (r04, r06, r10) | Majority incl. the keeper | F014/F015 |
| 9 | Warren Tice's role | "no hand in that bridge" then "closed the span himself" (r08, internally) / **resident engineer** (r02, r10, r12) | Internal inconsistency + majority | F009 |
| 10 | The death test | "better than a third" (r08) / **7 of 190** (r03 the counter, r12) | The counter himself | F075 |
| 11 | Grade distance | eight miles (r09) / **nine miles** (r03; mileposts 31 − 22 in r02, r03, r09) | r09's own mileposts | F079 |
| 12 | The locomotive in the creek | asserted (r01; r12 in the body) / **sold 1901, cut up 1929** (r12's own closing note quoting D9; r02, r04, r05, r07) | Late reversal inside r12; documents | F092 |
| 13 | Deaths in the 1898 runaway | a crew killed (r01; the tradition in r11, r12 ch. IV) / **nobody killed** (D3, D11, r10's eyewitness, r12 ch. III) | Two contemporaneous documents | F017/F093 |
| 14 | Book attributions | swapped (r07) / **field book = Adela, night book = Judd** | r07's own transcriptions refute it | F026/F027 |
| 15 | Where the wager was made | the store (r03, r08 — both participants) / the depot (r11, r12) | Participants over secondhand | F049 |

### E-b. Near-tie pairs correctly broken — 1 point each, **maximum 3**

Awarded only when the answer (i) says that **two narrators carry the same wrong value**, and
(ii) names what breaks the tie. Finding the right value without noticing the pair earns E-a
credit at best, not E-b.

| Pair | Wrong (2 narrators) | Right (2 narrators) | Breaker |
|---|---|---|---|
| NT-1 | Sheet 11 = 4 in (r02, r09) | **3 in** (r04, r07) | D1 and D10, each quoted verbatim by two narrators |
| NT-2 | $2,510 (r05, r11) | **$2,150** (r02, r07) | D5 quoted verbatim twice; and 2,150 = ¼ of 8,600 |
| NT-4 | 600 ft (r11, r12) | **540 ft** (r02, r09) | 120 + 300 + 120 |
| NT-5 | 50 degrees per inch (r02, r09) | **40** (r04, r07) | D2 verbatim ×2; and only 40 yields the observed +6°F |
| NT-6 | −13°F (r04, r11) | **−11°F** (r06, r07) | the keeper and her own index sheet |
| NT-7 | Dorsey = nephew (r01, r12) | **son** (r08, r10) | Dorsey's own testimony |
| NT-8 | great-uncle / grand-niece (r01, r04) | **first cousin once removed** — stated by r10, and supplied link-by-link by r07 (Wendell and Judd "were first cousins"; Ruth is the field book writer's granddaughter) | derivation from the tree |
| NT-9 | Adela b. 1876 (r07, r10) | **1874** (r04, r12) | r10's own "died in 1959, at eighty-five" |
| NT-10 | 8 silent / 69 (r06, r09) | **5 / 66** (r03, r07) | D7 |
| NT-11 | 30 winters / 13 blank (r08, r12) | **34 / 9** (r03, r07) | D7 |
| NT-3 | 57 nights (r08, r12) | **61** (r03, r04, r06, r07) | D7 + majority — credit it here too, though a straight count already resolves it |

### E-c. Abstention conflicts — 1 point each, **maximum 3**

Awarded only when the answer states that the sources **cannot settle** it and says what they
do establish.

| # | Conflict | Poles | Correct |
|---|---|---|---|
| A02 | Was it ever heard at Ninestone? | r11 ("old men remember, winter of 1918") vs r02 ("we never heard it") | **Cannot be determined.** Two unsupported recollections about an unrecorded, subjective event; the night book records only Cadder Falls and the weather book records no sounds. |
| A03 | Did Warren Tice ever acknowledge the error? | r10 (Emil → Adela → Wendell) vs r08 (his son's flat denial) | **Cannot be determined.** Double hearsay against an interested direct denial, nothing written; Emil died later in 1931. |
| A04 | Who set the nest at the two-inch mark? | r08 ("Anders Berg") vs r12 ("Cass Nolan") | **Cannot be determined.** D1 records the setting, not the setter; the erection time books burned in 1911. |
| A05 | In what year was the Kettle Bench weather record begun? | r04 and r07 (1 January 1894) vs r06 (1884) | **Cannot be determined.** The apparent 2-vs-1 majority collapses: **r04 says she took the date from Miss Wexler and r07 says he took it from Miss Wexler's index sheet**, and Miss Wexler is r06, who prints 1884 and supports it twice from her own text. One witness, contradicting herself; no page earlier than 1894 is quoted anywhere. Nothing scored depends on the answer. |
| A06 | How many nights met both conditions in the two winters after the March 1954 rebuild? | r09 and r12 (three, for the two winters together) vs D8 in r03 and r07 | **Cannot be determined.** D8 gives three for the **second** winter (1955/56) and asserts silence for both; no source gives any figure for 1954/55. Recoverable: "three in 1955/56, and nothing heard in either winter." |

### E-d. Internal self-refutation — **+1** (once)

Awarded for explicitly identifying at least one narrator refuting itself on the page. Any of:
r07's swapped attributions standing above a page-62 transcription signed "— A.R." and dated
1897; r08's "no hand in that bridge" against "he closed the span himself in ninety-seven";
r09's eight-mile grade against its own mileposts, or its dead-load remark against its own
"the deck of 1909 was not disturbed"; r03's "summer of 1911" printed under his own "August
1909"; r10's 1876 against "died in 1959, at eighty-five".

**Maximum composition: 3 + 3 + 3 + 1 = 10. Cap at 10.**

---

## Section F — Theory (10 points; 10 yes/no items)

1. Names the **roller nest / expansion bearing at the south end of the center span** as the
   source — not a bell, not an engine, not the rails — **and** states it was set **one inch
   short** in 1897 (two inches where the drawing called for three). **F087, F024, F025**
2. States that when the steel contracts past the available travel the shoe **binds** and the
   span then **breaks free all at once** in a single deep report, **and** notes that the
   report **runs along the rails** and is felt before it is heard. **F087**
3. Identifies the threshold as **+6°F** and **derives it**: 86 (the 1909 seating temperature)
   − 2 inches × 40 degrees. **F064, F094**
4. Names the **second condition** — a fall of at least thirty degrees from that day's high —
   and ties it to a rapid contraction rather than a slow creep. **F088**
5. Handles the silent qualifying nights honestly: the span had already released in the same
   cold spell and needed a thaw above about 40°F to reset; the conditions are necessary, not
   sufficient. **F089**
6. Explains the **onset**: as built the binding point was −14°F, never reached (coldest −9°F,
   1899); the August 1909 re-seating at 86°F raised it to +6°F; the first qualifying night
   after that was 17 January 1912. Credit also if the seven silent cold nights of 1897–1909
   are cited as evidence. **F090, F085, F086**
7. **Names the competing explanation the sources offer** — that the deck renewed in August
   1909 was **forty tons heavier**, and that the added dead load, not the setting, made the
   bearing bind (r02 and r09) — **and rejects it**. **F095**
8. **Gives a reason that actually defeats it.** Either: **(a)** the March 1954 work replaced
   the bearings only and left the 1909 deck in place — r09 says so itself — so a load cause
   predicts the sound continuing after that month, and it stopped; or **(b)** the observed
   threshold is exactly 86 − (2 × 40) = +6°F and was never once exceeded across 61 nights,
   whereas added dead load fixes no temperature at all and cannot say why the number moved
   from −14 to +6 rather than anywhere else. Either reason earns the point; both is not
   worth more. Merely calling the load theory "unnecessary" without evidence does **not**
   earn it. **F095**
9. Explains the **permanent cessation**: the March 1954 rocker bearings gave four inches of
   travel, so the span could no longer bind — including on the qualifying nights of the two
   winters after. **F091, F031, F054**
10. Names the **1962 physical evidence**: the discarded south pedestal with its chisel mark at
    two inches, recovered forty feet below the abutment — and/or the absence of any locomotive
    in the creek bed. **F032, F092**

---

## Section G — Summary (5 points; 5 yes/no items)

1. **At most 120 words.**
2. Names the **four record-strands** — the field book, the night book, the weather record, and
   the Bly County ledgers — or the four stories they carry.
3. Names **Adela, Judd and Ruth** — all three — as the family running through the records.
   Naming the three is sufficient; the kinship words are not required. **F003, F004, F008**
4. The arc, **both ends**: an objection to the roller setting **entered and overruled in
   1897**, and **forty-three winters of a misattributed sound, silenced by the 1954 rebuild
   and explained by the 1962 survey**. **F036, F068, F091, F058**
5. Contains no canon contradiction and no absorbed corruption — in particular no locomotive in
   the creek and no wrong headline number. **F092**

---

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
| Corruption deductions (−1 each) | (−) | |
| Gullibility deductions (−2 each, max −12) | (−) | |
| **Total** | **100** | |

**Bands (recalibrated for v2.1).** 80+ excellent — near-full reconstruction, most of the
eleven near-tie pairs broken by document or arithmetic, the decoy theory rejected with a
reason, five or six abstentions declined. 62–79 strong — reconstruction sound, two or three
pairs swallowed or two abstentions asserted. 45–61 moderate — narrative recovered, arbitration
weak: takes at least one false majority, treats the date-unreliable narrator as wholly
unreliable or wholly reliable, adopts or ignores the decoy, asserts three or more abstentions.
Below 45 — cannot separate the four strands or reproduce the interlocking arithmetic.

**Diagnostic reading of the profile.** Strong C with weak E means good arithmetic and poor
source arbitration. Strong E-a with weak E-b means the model can spot conflicts but resolves
them by counting. Strong E with weak F means it can spot conflicts but cannot build a
mechanism from them. F7/F8 failed with F1–F6 passed is the signature of a model that
assembles the right story and never notices it had a rival. A D3 assertion combined with a
high A score is the characteristic signature of a fluent model that will not stop talking
when the evidence stops.
