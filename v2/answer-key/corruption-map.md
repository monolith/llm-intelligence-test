# Corruption Map, v2 (SECRET — never show to the system under test)

Twelve narrators (r01–r12). For each: who they are, what slice of the history they hold,
their reliability profile, and the exact list of planted errors.

**Design rules.**
1. Every planted error is unique to one narrator — **except** the three designated
   **near-tie pairs**, where two narrators carry the identical wrong value and only a
   quoted document breaks the tie (§ Near-tie pairs).
2. Every scored fact appears correctly in **≥2 narrators**, or is **derivable by
   arithmetic**, or is **settled by a quoted document** (§ Recoverability index).
3. The **ghost-train lore** is a designed shared belief, not a planted error in the
   uniqueness sense — the test would have nothing to debunk otherwise. It is asserted
   flatly and never withdrawn by exactly one narrator (**r01**); asserted and then
   withdrawn late by one (**r12**); and alluded to without endorsement by the rest. It is
   refuted five independent ways (F092) and twice documentarily.
4. **Abstention poles** (marked ⌀) are not errors. They are the paired unsupported claims
   that make A01–A04 unsettleable. A narrator carrying one is not "wrong"; the model is
   wrong if it picks a side.

---

## r01 — Vesta Cobb, a mill hand's daughter (b. 1920), recorded at Cadder Falls, 1974

**Slice.** Cadder Falls folk memory: the boom as the town experienced it, the lore, the
store, the fact that the agent kept a book. Nothing of the engineering, nothing of Bly
County, nothing of the 1962 survey beyond hearsay.

**Reliability profile.** Vivid and largely accurate on *texture* — the boom's character
(a single deep report, always in the small hours, felt in the floor), the cold-night
condition in folk form ("only on the killing nights"), that it stopped when the railroad
"put new iron under the bridge," that Judd Rennick wrote it all down, that Dorsey Tice
kept the store. Unreliable on chronology and on anything documentary. She is the corpus's
purest carrier of the lore.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F092, F093 | "Number Nine and her crew are down in that gorge, and it is her they hear." Never withdrawn. | The engine was sold in 1901 and cut up in 1929; nobody died in the 1898 runaway. | Lore asserted as fact |
| X02 | F047 | The boom "started the winter the bridge was new" (1897/98). | First boom 17 January 1912. | Conflation with the wreck |
| X03 | F010 | Dorsey Tice was Warren Tice's **nephew**. | His **son**. | Kinship misattribution |

*Not errors:* "a hundred nights if there was one" is folk rhetoric, not a count claim, and
is not penalized or scored.

---

## r02 — Harlan Pike, son of the CVR's chief clerk; memoir written 1958

**Slice.** Story 1 from the company office: the survey, the dimensions and mileposts, the
grade, the erection, the runaway and the *Sentinel*, the locomotive's purchase price, the
1911 fire, the 1909 re-decking, the 1954 rehabilitation. He is the corpus's backbone for
railroad and dimensional data.

**Reliability profile.** Precise, documentary in habit, and correct on almost every
number he handles — with one specification error he never checked and one year he
misremembers. He also editorializes about Adela's dismissal, which is where the corpus's
first abstention trap sits.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X04 | F024 | Sheet 11 called for **four inches** of travel. | **Three inches.** | **Near-tie 1** (partner r09) |
| X05 | F045 | The re-decking was in **1908**. | **August 1909.** | Off-by-one |
| ⌀X06 | A01 | "Tice never forgave that entry, and she was gone inside four years." | Undeterminable. | Abstention pole (motive asserted) |
| ⌀X07 | A02 | "We never heard it at Ninestone. My father would have written it down." | Undeterminable. | Abstention pole (negative) |

---

## r03 — Judd Rennick, station agent (ret.), interviewed at Cadder Falls, 1965

**Slice.** Story 2 entire, first-hand: the night book, its columns and totals, the two
conditions, the silent qualifying nights and why, the death-omen test, the wager, the
1909 bridge gang as he watched it (including the 86° reading he copied from the depot
slate), the 1955/56 silence, the boom as a physical event at the station.

**Reliability profile — THE DATE-UNRELIABLE NARRATOR.** He is right about everything he
counted and wrong about every year he names for the bridge, the book and the wager. The
one deliberate exception is his own birth year (1888), which is correct and is one of only
two sources for it. Counts, temperatures, conditions, sums,
mechanism, names and relationships: all correct. Dates: all wrong. This is the corpus's
designed test of whether a model can partition a source's reliability by *category*
instead of scoring the whole source as trustworthy or not.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X08 | F047 | The first boom was "the winter of 1913." | 17 January 1912. | Date drift |
| X09 | F045 | The bridge gang came "the summer of 1911." | August 1909. | Date drift |
| X10 | F052 | The rockers went in "the spring of 1953." | March 1954. | Date drift |
| X11 | F049 | The wager was "January of 1937." | 14 January 1936. | Date drift |
| X12 | F046 | "I went on nights in 1907 and started the book that same winter." | Night operator 1909; night book begun 18 January 1912. | Date drift (compound) |

*Everything else from r03 is canon-correct*, including: 43 winters; 61 booms; 34 boom
winters and 9 blank; 5 silent qualifying nights; 66 qualifying nights; low below +6°F and
a fall of at least 30 degrees; the 40-degree thaw that resets the shoe; 190 deaths, 7
following a boom; the wager numbers (38° at four o'clock, 4 degrees an hour, the day's
high 41, the low −3, the boom at ten past one, five dollars, Dorsey Tice); the 86° reading
and that the gang set the shoes "to the same mark"; the three silent nights of the second
winter after the rockers; the mileposts and the 2.2 percent grade.

---

## r04 — Ruth Frayne, "What the Creek Gave Back," a talk to the Pell County Historical Society, 1963

**Slice.** Story 4 entire, plus Story 1 through her grandmother's field book and Story 3
through the Bly County photostats. The corpus's principal explainer: she is the one who
puts the movement rule, the erection temperature, the two-inch mark and the 86° re-seating
together into the three binding temperatures.

**Reliability profile.** Authoritative on measurement, mechanism and documents. Two
errors: one numeric slip in a figure she took from someone else's book, and one loose
family term. She is never wrong about anything she measured herself.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X13 | F080 | The Wexler record's lowest reading was **−13°F**. | **−11°F** (January 1918). | Near-miss numeric (corrupts the 2.8-inch movement range to 2.85) |
| X14 | F008 | She calls Judd Rennick "my father's uncle." | Judd and Wendell are **first cousins**; Judd is Ruth's **first cousin once removed**. | Kinship compression |

---

## r05 — Alma Nace, "The Engines My Grandfather Bought," Bly County, 1970

**Slice.** Story 3 entire: the Tolliver Lumber Company, the Sixmile tram, No. 9's arrival
and renumbering, her working life, her retirement and scrapping, her mother Pearl's books
and the 1938 deposit. She has never been to Pell County and knows nothing of the boom
except that "they had some noise on a bridge down there."

**Reliability profile.** Excellent on the locomotive's second life and on her own family;
wrong on both halves of the 1901 transaction, which she is reciting from memory of a
ledger she last saw as a girl.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X15 | F042 | The purchase price was **$2,510**. | **$2,150.** | **Near-tie 2** (partner r11); digit transposition |
| X16 | F042 | The purchase was in **1902**. | **19 June 1901.** | Off-by-one |

---

## r06 — Lettie Wexler, "A Farm Book of Weather," 1965

**Slice.** The weather record and the valley's cold history: the extremes, the entry for
17 January 1912, the seven cold nights of 1897–1909 and the −9° of February 1899, the mild
winters of 1909/10 and 1910/11, and the fact that Ruth Frayne borrowed the book in 1962.

**Reliability profile.** Impeccable on temperature and completely disinterested — she had
no theory and no stake, which is what makes her the corroborating witness. Two errors:
the year her father began, and a count she copied out of Judd's book while it was on loan.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X17 | F029 | Her father began the record in **1884**. | **1 January 1894.** | Off-by-a-decade |
| X18 | F071 | **Eight** nights met both conditions and gave no boom. | **Five.** | Miscount from a borrowed book (corrupts the 66 total to 69) |

---

## r07 — Accession notes, Pell County Historical Society, 1970 (curator: Merrit Sable)

**Slice.** All four stories, documentarily. This is the corpus's documentary anchor: it
quotes D1–D10 verbatim (ten documents) and refers to D11 without transcribing it, and it is the source that
settles both near-ties (NT-1, NT-2) and the document-plus-majority count (NT-3).

**Reliability profile.** Every quotation is exact. Every *inference around* the quotations
is a hurried curator's guess, and one of those guesses is refuted by the very text he
transcribes below it.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X19 | F026, F027 | **INTERNAL CONTRADICTION.** The field book is catalogued as "J. Rennick" and the night book as "A. Rennick" — swapped — immediately above a transcription of page 62 dated 1897 and signed "**— A.R.**" (when Judd Rennick was nine years old) and a transcription of the night book's front matter about a bridge gang of 1909. | Field book = Adela Rennick; night book = Judd Rennick. | Swapped attribution, self-refuting on the page |
| X20 | F014, F015 | The weather book was "kept by two brothers named Wexler." | Father and daughter — Peter and Lettie. | Misattribution |

---

## r08 — Dorsey Tice, storekeeper, remarks recorded at the store, Cadder Falls, 1961

**Slice.** Story 2 from the counter: the wager he lost, the boom as heard in the village,
the store's ledger, the town's talk. Story 1 only as family hearsay, and he is defensive
about it.

**Reliability profile.** Reliable on the wager (including its date, which r03 gets wrong)
and on his own parentage. He carries an internal contradiction about his father's role
and the document-plus-majority count (NT-3).

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X21 | F009 | **INTERNAL CONTRADICTION.** Early: "My father had no hand in that bridge; he was in the Ninestone office the whole time it was building." Late: "He took me out on the deck when I was six and told me he had closed the span himself in ninety-seven." | Warren Tice was the **resident engineer** on the viaduct and overruled the objection on the day the span was closed. | Self-contradiction (defensive, then proud) |
| X22 | F069 | The book showed **fifty-seven** nights. | **Sixty-one.** | **Near-tie 3** (partner r12) |
| ⌀X23 | A03 | "I was at that dinner. He said nothing of the kind, and he never in his life spoke to me about that bridge." | Undeterminable. | Abstention pole (interested denial) |
| ⌀X24 | A04 | "Anders Berg set that nest. Everybody knew it." | Undeterminable. | Abstention pole (name 1) |

---

## r09 — "Memorandum on the Sallow Creek Viaduct," office of the Pell County engineer, 1971 (H. L. Quarles)

**Slice.** The mechanism, written coldly and technically: the roller nest, binding,
stick-slip release, why the report travels along the rails, why later nights of a cold
spell are silent, what the 1954 rockers changed. Also the dimensions and the mileposts.

**Reliability profile.** The best explanation of *how* in the corpus, and the worst
arithmetic. It restates the movement rule wrongly, which makes every temperature it
computes wrong, and it repeats the four-inch specification error. Its qualitative physics
is entirely correct.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X25 | F024 | Sheet 11 specified **four inches**. | **Three inches.** | **Near-tie 1** (partner r02) |
| X26 | F060 | "One inch in three hundred feet for **fifty** degrees." | **Forty degrees.** | Wrong constant. With its other figures (4 in specified, 2 in as built, re-seated at 86°) it computes −134°F as specified, −34°F as built, and **−14°F after 1909** — a value that contradicts the +6°F threshold every observational source reports, and that *coincidentally equals canon's true 1897 as-built figure*. A model that trusts r09's numbers lands on a real number attached to the wrong era. |

---

## r10 — Wendell Frayne, "Notes for the family," 1971

**Slice.** The genealogy and the custody chain: births, marriages, deaths, who was whose,
who held which book when. Story 1 through his mother, Story 4 through his daughter.

**Reliability profile.** The corpus's authority on relationships, and correct on all of
them. One birth year slips. He carries the opposite pole of the A01 trap and one pole of
the A03 trap.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X27 | F002 | Adela was born in **1876**. | **1874.** | Off-by-two |
| ⌀X28 | A01 | "The party was let go entire and she was in it. There was nothing else in it." | Undeterminable. | Abstention pole (motive denied) |
| ⌀X29 | A03 | "Uncle Emil told my mother that at Tice's retirement dinner the old man said: *we set that nest a mark shy and I have listened to it ever since.*" | Undeterminable. | Abstention pole (double hearsay) |

---

## r11 — *Ninestone Sentinel*, 14 October 1962: "The Ghost of Sallow Creek Lies Down"

**Slice.** A reporter's compression of all four stories, written three weeks after Ruth's
survey. **A juxtaposing narrator**: it runs the 1898 wreck, the 1912 onset, the 1936
wager, the 1954 rebuild and the 1962 dig into one flowing story and welds two of them
together at the joints.

**Reliability profile.** Correct on what it saw and on the recent record — the draw-down,
the pedestal, the chisel mark, the absence of a locomotive, March 1954, the wager's date,
9 February 1954 as the last boom. Wrong wherever it compresses.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X30 | F038, F047 | "From the winter after the wreck, the valley began to hear her." | The wreck was March 1898; the first boom was January 1912 — fourteen years later. | Conflation of two events |
| X31 | F007, F015 | Ruth Frayne described as "the county's weather observer, who has kept the valley's temperatures for years." | Ruth is a **civil engineer** with the county highway department; the weather observer was **Lettie Wexler**. | Identity conflation |
| X32 | F042 | The sale price was **$2,510**. | **$2,150.** | **Near-tie 2** (partner r05) |
| ⌀X33 | A02 | "Old men here remember hearing it at Ninestone in the winter of 1918." | Undeterminable. | Abstention pole (positive) |

---

## r12 — "Our Valley: A Short History for the Schools," Cadder Falls, 1966 (Corwin Athey)

**Slice.** A schoolteacher's compilation of Stories 1, 2 and 3 — the building, the boom,
the locomotive — with a strong narrative line and a conscience. **A juxtaposing
narrator**, and **the late-reversal narrator**.

**Reliability profile.** Sound on chronology (it is one of the corpus's better date
sources: 12 September 1897, April 1896, 14 November 1897, 17 January 1912, 14 January
1936, 9 February 1954, 1902, Adela's 1874), and sound on the family. It carries one
near-tie count. Its central feature is the reversal.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X34 | F069 | "Fifty-seven nights are recorded." | **Sixty-one.** | **Near-tie 3** (partner r08) |
| X35 | F092 | **LATE REVERSAL.** Body of the pamphlet, asserted flatly: "Number Nine lies in the creek to this day, and it is her that the valley hears." Then, in a *Note added at press* at the very end, the author writes that he wrote to the Bly County Historical Rooms, quotes the shop book verbatim — *"No. 4 (ex-Cadder Valley 9) cut up at Sixmile this month. Scrap to Ravel Brothers, $470."* — and withdraws the claim: "I leave the paragraph as I wrote it and correct it here." | The engine was cut up at Sixmile in May 1929. | Claim planted early, retracted late by a quoted document |
| ⌀X36 | A04 | "Cass Nolan, who set the rollers…" | Undeterminable. | Abstention pole (name 2) |

---

## Near-tie pairs (explicit)

A near-tie is a wrong value carried by **two** narrators, so that counting sources gives a
tie (2 correct vs 2 wrong) or a false majority. Only a **quoted document** breaks it.

| Pair | Wrong value | Carried by | Correct value | Settled by |
|---|---|---|---|---|
| **NT-1** | Sheet 11 specified **4 inches** of travel | r02, r09 | **3 inches** | **D1** (field book p. 62: *"Rollers set at the two-inch mark. Sheet 11 calls for three."*) quoted in **r07**, and **D10** (Ruth's report: *"The chisel mark on the roller seat is at two inches. Sheet 11 calls for three."*) quoted in **r04**. Both quotations are of documents; both agree. |
| **NT-2** | No. 9 sold for **$2,510** | r05, r11 | **$2,150** | **D5** (stock book, 19 June 1901) quoted verbatim in **both r07 and r02** — two documentary quotations against two memories; r02 additionally supplies the $8,600 cost new, from which the exact-quarter relation is derivable. |
| **NT-3** (not a true near-tie) | **57** booms | r08, r12 | **61** | **61 also appears correctly in r04 and r06**, so the pair resolves **4-vs-2 on a straight count of sources**, without needing the document. **D7** (night book summary page) quoted in **r07**, and the book's own author r03, confirm it; a model that has discounted r03 wholesale still has r04 and r06. |

Consequences of swallowing a near-tie (useful as diagnostics when grading):
- NT-1 → C1(a) becomes −94°F instead of −54°F.
- NT-2 → C4(b) becomes 29.2 % instead of exactly 25 %.
- NT-3 → C3(a) becomes 1.3 instead of 1.4, and C3(c) 1.7 instead of 1.8.

---

## Recoverability index

For every scored fact: the narrators in which it appears **correctly** (≥2), or the
arithmetic that derives it, or the document that settles it. "✎" marks a documentary
quotation.

### Relationships and people

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F002 Adela b. 1874 | r04, r12 | r10 (1876) | Majority |
| F003 Adela and Emil siblings | r04, r10, r12 | — | Majority |
| F004 Judd b. 1888, Emil's son | r07 ✎, r10, r12 | — | Majority + arithmetic (Adela b. 1874 could not have a son b. 1888) |
| F006 Wendell b. 1904, Adela's son | r04, r10 | — | Majority |
| F007 Ruth, civil engineer, b. 1934 | r04, r07 ✎, r10 | r11 (weather observer) | Majority |
| F008 Judd = Ruth's first cousin once removed | r07, r10 | r04 ("my father's uncle") | Derivation from F003/F004/F006/F007 |
| F009 Warren Tice, resident engineer | r02, r10, r12 | r08 (internal contradiction) | Majority + r08's own later sentence |
| F010 Dorsey = Warren's son | r08, r10, r12 | r01 (nephew) | Majority, incl. Dorsey himself |
| F014/F015 Peter and Lettie, father and daughter | r04, r06, r10 | r07 ("two brothers") | Majority |
| F017 Lidell and Sherrod hurt, none killed | r02 ✎, r07 ✎, r10, r12 | r01 (dead crew) | Two documents (D3, D11) |
| F018–F020 custody chains | r04, r07 ✎, r10 | — | Majority |

### Places, objects, dimensions

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F021 mileposts 0 / 22 / 23 / 31 | r02, r03, r09 | — | Majority |
| F022 120 + 300 + 120 = 540 ft; 97 ft high | r02, r09 | — | Majority + arithmetic |
| F023 north end fixed, south on rollers | r02, r04, r09 | — | Majority |
| F024 Sheet 11 = 3 in | r04 ✎, r07 ✎ | r02, r09 (4 in) | **NT-1 — document** |
| F025 as built 2 in; chisel mark at 2 in | r04 ✎, r07 ✎, r09, r11 | — | Majority + documents |
| F028 No. 9: 4-4-0, Rowan 1889, $8,600 new | r02, r05, r07 ✎ | — | Majority + D5 |
| F029 weather record 1894–1966 | r04, r07 | r06 (1884) | Majority |
| F031 1954 rockers, 4 in | r04, r07, r09 | — | Majority |
| F032 pedestal 40 ft below the abutment | r04 ✎, r07 ✎, r11 | — | Majority + D10 |
| F034 Ninestone fire, 4 April 1911 | r02, r10 | — | Majority |

### Dates

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F035 construction begins April 1896 | r02, r12 | — | Majority |
| F036 12 Sept 1897, 66°F, two-inch mark | r02, r04, r07 ✎, r12 | — | D1 |
| F037 line opens 14 Nov 1897 | r02, r12 | — | Majority |
| F038 runaway 6 March 1898, north approach | r02, r07 ✎, r12 | r01, r11 (conflations) | D3, D11 |
| F040/F041 letter 30 April 1901; last day 15 May | r07 ✎, r10 | — | D4 |
| F042 sale 19 June 1901 | r02, r07 ✎, r12 | r05 (1902) | D5 |
| F043 marriage 1902 | r10, r12 | — | Majority |
| F045 re-decking August 1909 | r04, r07 ✎, r09 | r02 (1908), r03 (1911) | D6 + majority |
| F046 Judd night operator 1909, agent 1915 | r07, r08, r10 | r03 (1907) | Majority |
| F047 first boom 17 January 1912 | r04, r12 (r06 ✎ supplies D12) | r01 (1897/98), r03 (1913), r11 ("the winter after the wreck") | D12 + majority |
| F048 peak winter 1917/18, five booms; −11°F Jan 1918 | r06, r07, r12 | r04 (−13°F) | Majority |
| F049 wager 14 January 1936 | r08, r12 (both name the day), r11 (month only) | r03 (1937) | Majority |
| F050 record high 101°F, July 1936 | r04, r06 | — | Majority |
| F051 last boom 9 February 1954 | r07, r11, r12 | — | Majority |
| F052 rebuild March 1954 | r02, r04, r09, r11 | r03 (1953) | Majority |
| F054/F055 three silent nights, 1955/56; final note 2 March 1956 | r03, r07 ✎ | — | D8 |
| F056 retired 1928; cut up May 1929; scrap $470 | r05, r07 ✎, r12 (late) ✎ | — | D9 |
| F057 Tolliver books deposited 1938 | r05, r07 | — | Majority |
| F058 survey September 1962 | r04, r07, r10, r11 | — | Majority |

### Quantities and chains

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F060 rule: 1 in per 40° | r02, r04, r07 ✎ | r09 (50°) | D2 + majority + consistency with the observed +6°F threshold |
| F061 erection 66°F | r02, r04, r07 ✎, r12 | — | D1 |
| F062 −54°F as specified | r04, r07 ✎ | r09 (computes −134°F from its two bad constants) | **Arithmetic**: 66 − 3×40 |
| F063 −14°F as built | r04, r07 ✎ | r09 (computes −34°F) | **Arithmetic**: 66 − 2×40 |
| F064 +6°F after 1909 | r03, r04, r07 ✎ | r09 (computes −14°F) | **Arithmetic**: 86 − 2×40; confirmed against the log's 61 boom nights |
| F065 20 degrees / half an inch lost in 1909 | r04, r07 | — | **Arithmetic**: 86 − 66 |
| F068 43 winters | r03, r07 ✎, r08, r12 | — | D7 |
| F069 61 booms | r03, r04, r06, r07 ✎ | r08, r12 (57) | **Majority + document** |
| F070 34 boom winters, 9 blank | r03, r07 ✎ | — | D7 |
| F071 5 silent qualifying; 66 total | r03, r07 ✎ | r06 (8 / 69) | D7 |
| F072/F073 averages 1.4 and 1.8 | — | — | **Arithmetic** from F068–F070 |
| F074 1955/56's three nights excluded | r03, r07 ✎ | — | D8's "second winter since the rockers went in" |
| F075 190 deaths, 7 within a week | r03, r12 | — | Majority |
| F076/F077 wager arithmetic (38°, 4°/hr, 41 high, −3 low) | r03, r08, r12 | — | Majority + arithmetic |
| F078 540 ft | r02, r09 | — | Arithmetic |
| F079 2.2 % over 9 miles → 1,045 ft | r02, r03, r09 | — | Arithmetic |
| F080 101 / −11 → 2.8 in | r06, r07 (temps) | r04 (−13) | Majority + arithmetic |
| F081 $8,600 new | r02, r05 | — | Majority |
| F082 built 1889, cut up 1929 → 40 years | r02, r05, r07 ✎ | — | Arithmetic |
| F083 27 years at Tolliver | r05 (stated); arithmetic from D5's 1901 sale (r02 ✎, r07 ✎) + r05's September 1928 retirement | — | Arithmetic |
| F084 scrap $470 | r05, r07 ✎, r12 (late) ✎ | — | D9 |
| F085 seven cold nights 1897–1909, coldest −9°F | r04, r06 | — | Majority |
| F086 mild 1909/10 and 1910/11, coldest 9°F | r04, r06 | — | Majority |

### Mechanism and theory

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F087 binding, stick-slip release, report along the rails | r03 (observed), r04, r09 | — | Majority |
| F088 both conditions necessary | r03, r04, r07 ✎, r09 | — | D7 + majority |
| F089 not sufficient; the 40° thaw resets the shoe | r03, r09 | r06 (miscounts the exceptions but reports them) | Majority |
| F090 onset explained by the 1909 re-seating | r04, r09 (qualitatively), r06 (supplies the data) | — | Cross-story derivation |
| F091 cessation explained by the 1954 rockers | r02, r04, r09, r11 | — | Majority |
| F092 not No. 9 (five refutations) | r02, r04, r05, r07 ✎, r12 (late) ✎ | r01, r12 (early) | Two documents + physical absence + chronology |

### Single-source scored facts (uncontested)

Six scored facts appear in only **one** narrator. None is contradicted anywhere, so each
remains derivable — but each is lost outright by a model that discounts its carrier
wholesale.

| Fact | Only in | Status |
|---|---|---|
| Silas Tolliver as the lumber company's founder | r05 | Single-source, uncontested |
| The Sixmile tram | r05 | Single-source, uncontested |
| Pearl Nace by name | r05 | Single-source, uncontested |
| The 1928 retirement and the replacement engine | r05 | Single-source, uncontested — obliquely corroborated by r07's Item 6 note ("the engine having been set aside the previous year") |
| Ruth's birth year, 1934 | r10 | Single-source, uncontested |
| Emil's birth year, 1866 | r10 | Single-source, uncontested |

**Four of the six rest on r05**, a narrator carrying two planted errors (the 1902 sale year
and the $2,510 price). That is the fragility to watch when grading A3.5 and C4(c): r05 must
be discounted on those two values and trusted on everything else.

---

## Device checklist (Spec D3)

| Device | Where implemented | Facts touched |
|---|---|---|
| **Near-tie error broken only by a quoted document** | **NT-1** (r02 + r09 vs D1/D10 in r04/r07); **NT-2** (r05 + r11 vs D5 in r07); (NT-3, r08 + r12 vs D7 in r07, is document-plus-majority: 61 is also correct in r03, r04, r06) | F024, F042; F069 by majority + document |
| **3–4-hop inference across three retellings** | **C1**: movement rule (r02/r04/r07 ✎) → erection temperature 66°F (r02/r04/r07 ✎) → Sheet 11's 3 in vs the 2-in mark (r04/r07 ✎, contested by r02/r09) → the 86°F re-seating (r03, r07 ✎) → three binding temperatures. **C5**: mileposts (r02/r03/r09) → grade (r02/r09) → span length (r02/r04/r09) → Wexler extremes (r06/r07) → 2.8 in of movement. **C4**: cost new (r02/r05) → sale price (D5 in r07, contested) → build year (r02/r05/r07) → scrapping (r05/r07/r12-late) | F060–F066; F078–F080; F081–F084 |
| **A narrator wrong only on dates** | **r03**, Judd Rennick: five date errors (X08–X12), everything else canon-correct — including his own birth year, 1888. He also carries a third internal contradiction: the D6 quote reading "August 1909" is printed immediately above his own "That was the summer of 1911." | F045, F046, F047, F049, F052 |
| **A late reversal inside a retelling** | **r12**: the ghost claim asserted in the body, withdrawn in the closing *Note added at press* by quoting D9 verbatim (X35) | F092, F056 |
| **Internal contradictions in two retellings** | **r07** (X19: swapped attributions refuted by the "— A.R." signature and the 1909 front matter it transcribes itself); **r08** (X21: "no hand in that bridge" vs "he closed the span himself in ninety-seven") | F026/F027; F009 |
| **Two or more narrators juxtaposing separate stories** | **r07** (four collections, four stories, welded by a curator's guesses); **r11** (wreck + onset + survey compressed into one narrative, two joints welded wrong); **r12** (building + boom + locomotive) | F038/F047; F007/F015 |
| **≥3 abstention items** | **A01** (r02 ⌀X06 vs r10 ⌀X28); **A02** (r11 ⌀X33 vs r02 ⌀X07); **A03** (r10 ⌀X29 vs r08 ⌀X23); **A04** (r08 ⌀X24 vs r12 ⌀X36) — four in all | A01–A04 |

**Totals.** 28 canon-contradicting planted errors (X01–X05, X08–X22, X25–X27, X30–X32,
X34–X35), 8 abstention poles (⌀X06, ⌀X07, ⌀X23, ⌀X24, ⌀X28, ⌀X29, ⌀X33, ⌀X36), 2 near-tie
pairs (NT-1, NT-2) and one document-plus-majority pair (NT-3), 2 internal contradictions, 1 late reversal, 1 date-only-unreliable narrator, 3
juxtaposing narrators.
