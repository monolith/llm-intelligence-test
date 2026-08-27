# Corruption Map, v2 (SECRET — never show to the system under test)

Twelve narrators (r01–r12). For each: who they are, what slice of the history they hold,
their reliability profile, and the exact list of planted errors.

**Design rules.**
1. Every planted error is unique to one narrator — **except** the designated
   **near-tie pairs** (eleven of them as of v2.1), where two narrators carry the identical
   wrong value, a straight source count gives a tie or a false majority, and only a quoted
   document, arithmetic, or one narrator's internal consistency breaks it
   (§ Near-tie pairs).
2. Every scored fact appears correctly in **≥2 narrators**, or is **derivable by
   arithmetic**, or is **settled by a quoted document** (§ Recoverability index).
3. The **ghost-train lore** is a designed shared belief, not a planted error in the
   uniqueness sense — the test would have nothing to debunk otherwise. It is asserted
   flatly and never withdrawn by exactly one narrator (**r01**); asserted and then
   withdrawn late by one (**r12**); and alluded to without endorsement by the rest. It is
   refuted five independent ways (F092) and twice documentarily.
4. **Abstention poles** (marked ⌀) are not errors. They are the paired unsupported claims
   that make A01–A06 unsettleable. A narrator carrying one is not "wrong"; the model is
   wrong if it picks a side. **r06's "1884" is a pole, not an error** (see A05): it was a
   planted error in v2.0 and was reclassified in v2.1.
5. **The decoy theory** (the forty-ton deck of 1909 as the cause of the onset) is carried by
   **r02** and **r09** and is refuted by one record and one arithmetic fact (F095). Like the
   ghost lore it is a designed shared belief, not a uniqueness breach.

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
| X03 | F010 | Dorsey Tice was Warren Tice's **nephew**. | His **son**. | **Near-tie 7** (partner r12) |
| X37 | F008 | Ruth Frayne was Judd's **grand-niece** — "she was his grand-niece, they told me." | Judd is her **first cousin once removed**. | **Near-tie 8** (partner r04, whose "my father's uncle" is the same error from the other end) |

*Not errors:* "a hundred nights if there was one" is folk rhetoric, not a count claim, and
is not penalized or scored.

---

## r02 — Harlan Pike, son of the CVR's chief clerk; memoir written 1958

**Slice.** Story 1 from the company office: the survey, the dimensions and mileposts, the
grade, the erection, the runaway and the *Sentinel*, the locomotive's purchase price, the
1911 fire, the 1909 re-decking, the 1954 rehabilitation. He is the corpus's backbone for
railroad and dimensional data.

**Reliability profile.** Precise and documentary in habit; impeccable on paper — mileposts,
dates, dollars, the two documents he quotes — and unreliable on engineering constants,
which he has from office talk and never checked. He also editorializes about Adela's
dismissal, which is where the corpus's first abstention trap sits, and he offers the
corpus's **decoy theory** as his one stated opinion. The split is deliberate: he must stay
credible enough for his two near-tie values to look like a real majority.

*Removed in v2.1:* his statement of the grade distance. He now gives the grade
(2.2 percent) without a mileage, so the nine miles must come from r03 or from his own
mileposts (31 − 22).

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X04 | F024 | Sheet 11 called for **four inches** of travel. | **Three inches.** | **Near-tie 1** (partner r09) |
| X05 | F045 | The re-decking was in **1908**. | **August 1909.** | Off-by-one |
| X38 | F060 | "One inch in three hundred feet for **fifty** degrees… an inch for every fifty degrees." | **Forty degrees.** | **Near-tie 5** (partner r09) |
| X39 | F095 | **DECOY THEORY.** "Forty tons is forty tons… I say the weight did it." The added dead load of the 1909 deck, not the re-seating, is what made the bearing bind. | The 1909 re-seating at 86°F raised the binding point to +6°F. The 1954 work left the 1909 deck in place and the sound stopped anyway; and a load cause produces no fixed temperature. | Decoy pole 1 (partner r09) — plausible, offered as opinion, never hedged |
| ⌀X40 | A01 | "Two of that party were taken back on in the August following, for the Ashby extension work, and she was not, and I have never needed anybody to explain that to me." | Undeterminable. | Abstention pole (the re-engagement read as proof of a grudge) |
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
| X13 | F080 | The Wexler record's lowest reading was **−13°F**. | **−11°F** (January 1918). | **Near-tie 6** (partner r11); corrupts the 2.8-inch movement range to 2.85 |
| X14 | F008 | She calls Judd Rennick "my father's uncle." | Judd and Wendell are **first cousins**; Judd is Ruth's **first cousin once removed**. | **Near-tie 8** (partner r01's "grand-niece") |
| ⌀X41 | A05 | "Miss Wexler puts the beginning of it at the first of January, 1894, and I have used her date." | Undeterminable. | Abstention pole — she names her source, and her source is the narrator who prints 1884 |

*Removed in v2.1:* her count of the silent qualifying nights. She now says "further nights
answered both conditions and produced nothing at all, and his own summing at the back of the
book gives the count of them," so the **5 / 66** survives only in r03 and in D7 (r07). This
is what makes NT-10 a true 2-vs-2.

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
| ⌀X17 | A05 | Her father began the record in **1884** — supported twice by her own text ("eighty-one years of it, now"; "eighty-odd years of pages"). | **Undeterminable.** Reclassified in v2.1: this is now an abstention pole, not a planted error, because the only two sources for 1894 (r04, r07) both name *her* as their authority. | Abstention pole (A05) |
| X18 | F071 | **Eight** nights met both conditions and gave no boom; "so sixty-nine nights in all." | **Five / 66.** | **Near-tie 10** (partner r09); corrupts the 66 total to 69 |

---

## r07 — Accession notes, Pell County Historical Society, 1970 (curator: Merrit Sable)

**Slice.** All four stories, documentarily. This is the corpus's documentary anchor: it
quotes **D1–D10 and D13 verbatim (eleven documents)** and refers to D11 without transcribing
it. It carries the correct value in **seven of the eleven near-tie pairs** (NT-1, NT-2, NT-5,
NT-6, NT-8, NT-10, NT-11) and the wrong value in one (NT-9), and it is the sole home of D13,
the notice that makes A01 two-sided. Its transcriptions are the corpus's single most valuable
resource and its inferences are its least.

**Reliability profile.** Every quotation is exact. Every *inference around* the quotations
is a hurried curator's guess, and one of those guesses is refuted by the very text he
transcribes below it.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X19 | F026, F027 | **INTERNAL CONTRADICTION.** The field book is catalogued as "J. Rennick" and the night book as "A. Rennick" — swapped — immediately above a transcription of page 62 dated 1897 and signed "**— A.R.**" (when Judd Rennick was nine years old) and a transcription of the night book's front matter about a bridge gang of 1909. | Field book = Adela Rennick; night book = Judd Rennick. | Swapped attribution, self-refuting on the page |
| X20 | F014, F015 | The weather book was "kept by two brothers named Wexler." | Father and daughter — Peter and Lettie. | Misattribution |
| X42 | F002 | "…the writer of the field book, Adela Rennick, born 1876 and died 1959." | Born **1874**. | **Near-tie 9** (partner r10) — a curator's note, not a transcription |
| ⌀X43 | A05 | "The depositor's own index sheet gives the beginning of the record as 1 January 1894, and I have entered that date on the authority of the sheet, having no other." | Undeterminable. | Abstention pole — the second 1894 source, and it too traces to Lettie Wexler |

**New document in v2.1.** r07 now transcribes **D13**, a printed CVR notice of 20 July 1901
folded inside D4, re-engaging two of the party (Corliss, rodman; Wain, chainman) for the
Ashby extension and not naming Adela. r07 adds the flat, non-committal observations that
both men were of the same party, that she is not named, and that there is no second slip.
D13 is what makes A01 genuinely two-sided: it removes "reduced entire, and nothing else"
as a settling argument without supplying a motive.

---

## r08 — Dorsey Tice, storekeeper, remarks recorded at the store, Cadder Falls, 1961

**Slice.** Story 2 from the counter: the wager he lost, the boom as heard in the village,
the store's ledger, the town's talk. Story 1 only as family hearsay, and he is defensive
about it. He carries **three of the night book's totals wrong and every wager figure right**
— the split is deliberate: he witnessed the wager and only ever heard the totals second-hand,
and he says so himself ("I do not believe five people ever asked").

**Reliability profile.** Reliable on the wager (including its date, which r03 gets wrong)
and on his own parentage. He carries an internal contradiction about his father's role
and the document-plus-majority count (NT-3).

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X21 | F009 | **INTERNAL CONTRADICTION.** Early: "My father had no hand in that bridge; he was in the Ninestone office the whole time it was building." Late: "He took me out on the deck when I was six and told me he had closed the span himself in ninety-seven." | Warren Tice was the **resident engineer** on the viaduct and overruled the objection on the day the span was closed. | Self-contradiction (defensive, then proud) |
| X22 | F069 | The book showed **fifty-seven** nights. | **Sixty-one.** | **Near-tie 3** (partner r12) — document + majority |
| X44 | F070 | "Thirty winters she spoke in and thirteen she never opened her mouth at all — thirty and thirteen, and there is your forty-three." | **34 and 9.** | **Near-tie 11** (partner r12); internally consistent (30 + 13 = 43), so only D7 breaks it. Corrupts C3(c) to 1.9 |
| X45 | F075 | "Better than a third of the burying in this town came inside the week after a night she spoke." | **7 of 190.** | Garbled hearsay of a count he never read |
| ⌀X23 | A03 | "I was at that dinner. He said nothing of the kind, and he never in his life spoke to me about that bridge." | Undeterminable. | Abstention pole (interested denial) |
| ⌀X24 | A04 | "Anders Berg set that nest. Everybody knew it." | Undeterminable. | Abstention pole (name 1) |

---

## r09 — "Memorandum on the Sallow Creek Viaduct," office of the Pell County engineer, 1971 (H. L. Quarles)

**Slice.** The mechanism, written coldly and technically: the roller nest, binding,
stick-slip release, why the report travels along the rails, why later nights of a cold
spell are silent, what the 1954 rockers changed. Also the dimensions and the mileposts.

**Reliability profile.** The best explanation of *how* in the corpus, and the worst
arithmetic. It restates the movement rule wrongly, which makes every temperature it
computes wrong; it repeats the four-inch specification error; it prints a grade distance
that its own mileposts refute two sentences earlier; and it floats the **decoy theory**,
which the very next section of the memo destroys. Its qualitative physics (¶11–15) is
entirely correct, which is exactly what makes the rest of it dangerous. It says of itself
that its account of the depot record is at second hand — that concession covers X47 and
⌀X49 and is the reader's warning.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X25 | F024 | Sheet 11 specified **four inches**. | **Three inches.** | **Near-tie 1** (partner r02) |
| X26 | F060 | "One inch in three hundred feet for **fifty** degrees." | **Forty degrees.** | **Near-tie 5** (partner r02). With its other figures (4 in specified, 2 in as built, re-seated at 86°) it computes −134°F as specified, −34°F as built, and **−14°F after 1909** — a value that contradicts the +6°F threshold every observational source reports, and that *coincidentally equals canon's true 1897 as-built figure*. A model that trusts r09's numbers lands on a real number attached to the wrong era. |
| X46 | F079 | The 2.2 percent grade is "maintained over **eight** miles" — in the same sentence that gives the quarry as milepost 31 and the viaduct as milepost 22. | **Nine miles** (31 − 22). | Off-by-one, self-refuting on the page. Yields 929.28 ft instead of 1,045.44 ft |
| X47 | F071 | "**Eight** such nights within the depot record, as the writer has it at second hand." | **Five.** | **Near-tie 10** (partner r06) |
| X48 | F095 | **DECOY THEORY.** "It is at least as probable that the added dead load, rather than any question of travel, was what brought the bearing to bind; and the date at which the local tradition is said to begin is consistent with the re-decking and with nothing else in the record." | The 1909 re-seating at 86°F is the cause. | Decoy pole 2 (partner r02) — and **self-refuted three paragraphs later**: "The deck of 1909 was not disturbed in that work and stands over the span today; nothing was altered in March 1954 but the bearings themselves." |
| ⌀X49 | A06 | "Three nights in the two winters following the work are reported to have answered both conditions." | Undeterminable as a two-winter total. | Abstention pole (the count for 1954/55 exists nowhere) |

---

## r10 — Wendell Frayne, "Notes for the family," 1971

**Slice.** The genealogy and the custody chain: births, marriages, deaths, who was whose,
who held which book when. Story 1 through his mother, Story 4 through his daughter.

**Reliability profile.** The corpus's authority on relationships, and correct on all of
them. One birth year slips. He carries the opposite pole of the A01 trap and one pole of
the A03 trap.

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X27 | F002 | Adela was born in **1876**. | **1874.** | **Near-tie 9** (partner r07); self-refuted by his own "died in 1959, at eighty-five" |
| ⌀X28 | A01 | "The party was let go entire and she was in it. There was nothing else in it." | Undeterminable. | Abstention pole (motive denied) |
| ⌀X50 | A01 | He reports the re-engagement himself — "the road took two of that party back on in the August following… and it did not take her. That is true and it proves nothing" — and answers it with "she was the only computer the road ever had and it never had another one." | Undeterminable. | Abstention pole (the same document read the other way). Neither reading is refutable |
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
| X51 | F022, F078 | "the viaduct — **six hundred feet** of it, ninety-seven feet up." | **540 ft** (120 + 300 + 120). | **Near-tie 4** (partner r12); broken by arithmetic |
| X52 | F080 | "**Thirteen below zero** up at Kettle Bench, and nothing since has come near it." | **−11°F.** | **Near-tie 6** (partner r04) |
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
| X34 | F069 | "Fifty-seven nights are recorded." | **Sixty-one.** | **Near-tie 3** (partner r08) — document + majority |
| X53 | F022, F078 | "It is six hundred feet long and it stands ninety-seven feet above the water." | **540 ft.** (The 97 ft is correct.) | **Near-tie 4** (partner r11) |
| X54 | F010 | "Warren Tice, whose **nephew** Dorsey keeps the store today." | His **son**. | **Near-tie 7** (partner r01) |
| X55 | F070 | "In thirty of those winters the bridge spoke at least once; in thirteen of them it never spoke at all." | **34 and 9.** | **Near-tie 11** (partner r08) |
| ⌀X56 | A06 | "Three nights in the two winters that followed answered every condition the book lays down, and the bridge said nothing on any of them." | Undeterminable as a two-winter total. | Abstention pole (partner r09) |
| X35 | F092 | **LATE REVERSAL.** Body of the pamphlet, asserted flatly: "Number Nine lies in the creek to this day, and it is her that the valley hears." Then, in a *Note added at press* at the very end, the author writes that he wrote to the Bly County Historical Rooms, quotes the shop book verbatim — *"No. 4 (ex-Cadder Valley 9) cut up at Sixmile this month. Scrap to Ravel Brothers, $470."* — and withdraws the claim: "I leave the paragraph as I wrote it and correct it here." | The engine was cut up at Sixmile in May 1929. | Claim planted early, retracted late by a quoted document |
| ⌀X36 | A04 | "Cass Nolan, who set the rollers…" | Undeterminable. | Abstention pole (name 2) |

---

## Near-tie pairs (explicit)

A near-tie is a wrong value carried by **two** narrators, so that counting sources gives a
tie (2 correct vs 2 wrong) or a false majority. Only a **quoted document**, **arithmetic**,
or **one narrator's internal consistency** breaks it. Eleven pairs; **eight are new in
v2.1** (NT-4 – NT-11).

| Pair | Wrong value | Carried by | Correct value | Carried by | Settled by |
|---|---|---|---|---|---|
| **NT-1** | Sheet 11 specified **4 inches** of travel | r02 (X04), r09 (X25) | **3 inches** | r04 ✎, r07 ✎ | **Document.** D1 (field book p. 62: *"Rollers set at the two-inch mark. Sheet 11 calls for three."*) and D10 (Ruth's report), each quoted verbatim by two narrators. Note r09 claims to hold the drawings — the hardest document-vs-document call in the corpus |
| **NT-2** | No. 9 sold for **$2,510** | r05 (X15), r11 (X32) | **$2,150** | r02 ✎, r07 ✎ | **Document.** D5 (stock book, 19 June 1901) quoted verbatim in both r02 and r07 — two documentary quotations against two memories. **Arithmetic backstop:** $2,150 is exactly a quarter of the $8,600 cost new (r02, r05); $2,510 is 29.2 % |
| **NT-3** | **57** nights heard | r08 (X22), r12 (X34) | **61** | r03, r04, r06, r07 ✎ | **Document + majority.** Not a true near-tie: 61 also stands in r04 and r06, so a straight count resolves it 4-vs-2 even before D7 |
| **NT-4** | Viaduct **600 feet** long | r11 (X51), r12 (X53) | **540 ft** | r02, r09 | **Arithmetic.** 120 + 300 + 120 = 540, and r02 and r09 both give the three span lengths *and* the total. Neither 600-source gives components |
| **NT-5** | Movement rule = one inch per **50 degrees** | r02 (X38), r09 (X26) | **40 degrees** | r04 ✎, r07 ✎ | **Document + internal consistency.** D2 (*"Rule for the long span: one inch in three hundred feet for forty degrees."*) quoted verbatim in r04 and r07; and only 40 reproduces the +6°F threshold that the night book records 61 times (86 − 2 × 40 = 6). r09 itself reports that its own result "is not readily reconciled with the local record" |
| **NT-6** | Record low **−13°F** | r04 (X13), r11 (X52) | **−11°F** | r06, r07 ✎ | **Keeper + document.** r06 kept the thermometer; r07 takes −11 "from the depositor's own index sheet." Corrupts C5(c) to 2.85 in |
| **NT-7** | Dorsey Tice was Warren Tice's **nephew** | r01 (X03), r12 (X54) | **son** | r08, r10 | **Direct testimony + internal consistency.** r08 is Dorsey himself and calls Warren "my father" throughout, including "he took me out on the deck when I was six"; r10 is the family's record-keeper |
| **NT-8** | Judd was Ruth's **great-uncle** (r04: "my father's uncle"; r01: "his grand-niece") | r01 (X37), r04 (X14) | **first cousin once removed** | r10 (states it), r07 (supplies both links) | **Derivation.** Emil and Adela are siblings (r03, r07, r10, r12); Judd is Emil's son (r03, r10, r12); Wendell is Adela's son (r04, r10); Ruth is Wendell's daughter (r07, r10). r10 states the conclusion and names the courtesy title as the source of the error |
| **NT-9** | Adela born **1876** | r07 (X42), r10 (X27) | **1874** | r04, r12 | **Arithmetic, inside a wrong-value carrier.** r10's own sentence says she "died in 1959, at eighty-five" → 1874 |
| **NT-10** | **8** silent qualifying nights → **69** in all | r06 (X18), r09 (X47) | **5 → 66** | r03, r07 ✎ | **Document.** D7 (night-book summary page) quoted verbatim in r07 and given in the same figures by its author r03. Both wrong-value carriers say where they got it — r06 read the book for an hour, r09 has it "at second hand" |
| **NT-11** | **30** boom winters / **13** blank | r08 (X44), r12 (X55) | **34 / 9** | r03, r07 ✎ | **Document.** D7. The wrong pair is internally consistent (30 + 13 = 43), so arithmetic alone will not break it. Corrupts C3(c) to 1.9 |

Consequences of swallowing a near-tie (useful as diagnostics when grading):
- NT-1 → C1(a) becomes −94°F instead of −54°F (or −134°F if NT-5 is swallowed too).
- NT-2 → C4(b) becomes 29.2 % instead of exactly 25 %.
- NT-3 → C3(a) becomes 1.3 instead of 1.4.
- NT-4 → C5(a) becomes 600 ft instead of 540 ft.
- NT-5 → C1(b) becomes −34°F, C1(c) becomes −14°F (a real number attached to the wrong era), C5(c) becomes 2.24 in.
- NT-6 → C5(c) becomes 2.85 in.
- NT-7 → B4 parentage lost.
- NT-8 → B3 lost.
- NT-9 → A1.1 / B1 lost.
- NT-10 → C3(b) becomes 69, and C3(d) is usually lost with it.
- NT-11 → C3(c) becomes 1.9 instead of 1.8.

**Two roads to 69.** A model can reach the wrong total 69 either by taking r06/r09's eight
silent nights (61 + 8) or by adding the three post-rebuild nights to the correct 66. The key
distinguishes them: the first loses C3(b); the second loses C3(d) and, if asserted as a
two-winter count, triggers A06's gullibility deduction.

## Recoverability index

For every scored fact: the narrators in which it appears **correctly** (≥2), or the
arithmetic that derives it, or the document that settles it. "✎" marks a documentary
quotation.

### Relationships and people

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F002 Adela b. 1874 | r04, r12 | r07, r10 (1876) | **NT-9 — arithmetic** (r10: died 1959 at 85) |
| F003 Adela and Emil siblings | r04, r10, r12 | — | Majority |
| F004 Judd b. 1888, Emil's son | r07 ✎, r10, r12 | — | Majority + arithmetic (Adela b. 1874 could not have a son b. 1888) |
| F006 Wendell b. 1904, Adela's son | r04, r10 | — | Majority |
| F007 Ruth, civil engineer, b. 1934 | r04, r07 ✎, r10 | r11 (weather observer) | Majority |
| F008 Judd = Ruth's first cousin once removed | r07, r10 | r01 ("grand-niece"), r04 ("my father's uncle") | **NT-8 — derivation** from F003/F004/F006/F007 |
| F009 Warren Tice, resident engineer | r02, r10, r12 | r08 (internal contradiction) | Majority + r08's own later sentence |
| F010 Dorsey = Warren's son | r08, r10 | r01, r12 (nephew) | **NT-7 — direct testimony** (r08 is Dorsey) |
| F014/F015 Peter and Lettie, father and daughter | r04, r06, r10 | r07 ("two brothers") | Majority |
| F017 Lidell and Sherrod hurt, none killed | r02 ✎, r07 ✎, r10, r12 | r01 (dead crew) | Two documents (D3, D11) |
| F018–F020 custody chains | r04, r07 ✎, r10 | — | Majority |

### Places, objects, dimensions

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F021 mileposts 0 / 22 / 23 / 31 | r02, r03, r09 | — | Majority |
| F022 120 + 300 + 120 = 540 ft; 97 ft high | r02, r09 | r11, r12 (600 ft) | **NT-4 — arithmetic** (97 ft uncontested: r02, r09, r11, r12) |
| F023 north end fixed, south on rollers | r02, r04, r09 | — | Majority |
| F024 Sheet 11 = 3 in | r04 ✎, r07 ✎ | r02, r09 (4 in) | **NT-1 — document** |
| F025 as built 2 in; chisel mark at 2 in | r04 ✎, r07 ✎, r09, r11 | — | Majority + documents |
| F028 No. 9: 4-4-0, Rowan 1889, $8,600 new | r02, r05, r07 ✎ | — | Majority + D5 |
| F029 weather record start year | — | — | **A05 — abstention.** Both 1894 sources cite r06, who prints 1884. Nothing scored depends on it |
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
| F060 rule: 1 in per 40° | r04 ✎, r07 ✎ | r02, r09 (50°) | **NT-5 — D2 verbatim ×2 + consistency with the observed +6°F threshold** |
| F061 erection 66°F | r02, r04, r07 ✎, r12 | — | D1 |
| F062 −54°F as specified | r04, r07 ✎ | r09 (computes −134°F from its two bad constants) | **Arithmetic**: 66 − 3×40 |
| F063 −14°F as built | r04, r07 ✎ | r09 (computes −34°F) | **Arithmetic**: 66 − 2×40 |
| F064 +6°F after 1909 | r03, r04, r07 ✎ | r09 (computes −14°F) | **Arithmetic**: 86 − 2×40; confirmed against the log's 61 boom nights |
| F065 20 degrees / half an inch lost in 1909 | r04, r07 | — | **Arithmetic**: 86 − 66 |
| F068 43 winters | r03, r07 ✎, r08, r12 | — | D7 |
| F069 61 booms | r03, r04, r06, r07 ✎ | r08, r12 (57) | **Majority + document** |
| F070 34 boom winters, 9 blank | r03, r07 ✎ | r08, r12 (30 / 13) | **NT-11 — D7** |
| F071 5 silent qualifying; 66 total | r03, r07 ✎ | r06, r09 (8 / 69) | **NT-10 — D7** |
| F072/F073 averages 1.4 and 1.8 | — | — | **Arithmetic** from F068–F070 |
| F074 1955/56's three nights excluded | r03, r07 ✎ | — | D8's "second winter since the rockers went in" |
| F075 190 deaths, 7 within a week | r03 (the counter), r12 | r08 ("better than a third") | Majority + the counter himself |
| F076/F077 wager arithmetic (38°, 4°/hr, 41 high, −3 low) | r03, r08, r12 | — | Majority + arithmetic |
| F078 540 ft | r02, r09 | r11, r12 (600 ft) | **NT-4 — arithmetic** |
| F079 2.2 % over 9 miles → 1,045 ft | grade: r02, r09; distance: r03 (stated), r02/r03/r09 (mileposts) | r09 ("eight miles") | **Arithmetic + r09's own mileposts.** Three-retelling chain; r03's count kept while his dates are discarded |
| F080 101 / −11 → 2.8 in | r06, r07 ✎ (temps) | r04, r11 (−13) | **NT-6 — keeper + index sheet** |
| F081 $8,600 new | r02, r05 | — | Majority |
| F082 built 1889, cut up 1929 → 40 years | r02, r05, r07 ✎ | — | Arithmetic |
| F083 27 years at Tolliver | r05 (stated); arithmetic from D5's 1901 sale (r02 ✎, r07 ✎) + r05's September 1928 retirement | — | Arithmetic |
| F084 scrap $470 | r05, r07 ✎, r12 (late) ✎ | — | D9 |
| F085 seven cold nights 1897–1909, coldest −9°F | r04, r06 | — | Majority |
| F095 the forty-ton deck was **not** the cause | r09 ✎ (its own ¶15), r04 + r03/r07 ✎ (the 86° re-seating and the +6 threshold) | r02, r09 (decoy) | **Record + arithmetic.** The 1954 work changed the bearings only and the 1909 deck is still in place (r09), yet the sound stopped; and +6 = 86 − 2 × 40 exactly |
| F096 post-1954 qualifying nights | — | — | **A06 — abstention.** D8 counts the second winter only |
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

## Device checklist (Spec D3 + v2.1 hardening)

| Device | Where implemented | Facts touched |
|---|---|---|
| **Near-tie error broken only by a document, arithmetic, or internal consistency** | **Eleven pairs.** Document: NT-1, NT-2, NT-5, NT-6, NT-10, NT-11. Arithmetic: NT-4, NT-9. Derivation: NT-8. Direct testimony: NT-7. Document + majority: NT-3 | F002, F008, F010, F022/F078, F024, F042, F060, F069, F070, F071, F080 |
| **3–4-hop inference across three retellings** | **C1** (rule → 66°F erection → the 2-in mark against Sheet 11's 3 → the 86°F re-seating → three binding temperatures; r02/r03/r04/r07/r09). **C3** (61 from D7/r03/r04 → 43 → 34 from D7/r03 → the March 1954 rebuild from r02/r09/r11/r12 → exclude the post-rebuild nights; **r03's counts kept, his 1953 and 1913 discarded**). **C5(b)** (mileposts from r02/r03/r09 → grade 2.2 % from r02/r09 → nine miles from **r03** or from 31 − 22, against r09's "eight miles" → × 5,280 ft). **B4** (r08's own parentage + r10 → D1's "W.T." in r04/r07 → Judd as Adela's nephew in r03/r10 → the wager year 1936 in r08/r12 with **r03's figures kept and his 1937 discarded**). **C4** (cost new → D5 sale → build year → scrapping) | F060–F066; F068–F074; F079; F009/F010/F049; F081–F084 |
| **Unit / off-by-one traps the key resolves explicitly** | C5(b): r09's "eight miles" against its own mileposts (929.28 ft vs 1,045.44 ft), and miles → feet at 5,280. C3: 43 winters = 1911/12–1953/54 (r03's 1913 onset yields 42); and the **two roads to 69** (61 + 8, or 66 + 3) | F079; F068, F071, F074 |
| **A decoy theory that must be rejected** | The **forty-ton deck of August 1909** as the cause of the onset — asserted by **r02** ("I say the weight did it") and **r09** (¶10, as opinion). Consistent with the onset date, the cessation, the cold, and the character of the sound. Refuted by **one record** (r09's own ¶15: the 1909 deck was not disturbed in 1954, only the bearings — so a load cause predicts the sound continuing) and **one arithmetic fact** (86 − 2 × 40 = +6, matching 61 observed nights exactly; a load cause fixes no temperature). Scored at **F7 and F8** | F095, F045, F064, F091 |
| **A narrator wrong only on dates** | **r03**, Judd Rennick: five date errors (X08–X12), everything else canon-correct — including his own birth year, 1888, and now the only stated "nine miles" in the corpus. He also carries an internal contradiction: the D6 quote reading "August 1909" is printed immediately above his own "That was the summer of 1911" | F045, F046, F047, F049, F052; F079 |
| **A late reversal inside a retelling** | **r12**: the ghost claim asserted in the body, withdrawn in the closing *Note added at press* by quoting D9 verbatim (X35) | F092, F056 |
| **Internal contradictions** | **r07** (X19: swapped attributions refuted by the "— A.R." signature and the 1909 front matter it transcribes itself); **r08** (X21: "no hand in that bridge" vs "he closed the span himself in ninety-seven"); **r09** (X46: eight miles against its own mileposts; X48: the decoy against its own ¶15; and its own "not readily reconciled" concession); **r03** (August 1909 above "the summer of 1911"); **r10** (1876 against "died in 1959, at eighty-five") | F026/F027; F009; F079/F095; F045; F002 |
| **Two or more narrators juxtaposing separate stories** | **r07** (four collections, four stories, welded by a curator's guesses); **r11** (wreck + onset + survey compressed, two joints welded wrong); **r12** (building + boom + locomotive) | F038/F047; F007/F015 |
| **Abstention items** | **Six.** A01 (r02 ⌀X06/⌀X40 vs r10 ⌀X28/⌀X50, over D4 + **D13**); A02 (r11 ⌀X33 vs r02 ⌀X07); A03 (r10 ⌀X29 vs r08 ⌀X23); A04 (r08 ⌀X24 vs r12 ⌀X36); **A05** (r04 ⌀X41 + r07 ⌀X43 vs r06 ⌀X17 — both 1894 sources cite the 1884 witness); **A06** (r09 ⌀X49 + r12 ⌀X56 vs D8 in r03/r07) | A01–A06 |

**Totals (v2.1).** **41 canon-contradicting planted entries** (X01–X05, X08–X16, X18–X22,
X25–X27, X30–X32, X34–X35, X37–X39, X42, X44–X48, X51–X55) — of which **39 are fact errors
and 2 (X39, X48) are the decoy-theory poles**; X17 has been reclassified out of this list as
an abstention pole. **15 abstention poles** (⌀X06, ⌀X07, ⌀X17, ⌀X23, ⌀X24, ⌀X28, ⌀X29,
⌀X33, ⌀X36, ⌀X40, ⌀X41, ⌀X43, ⌀X49, ⌀X50, ⌀X56) across **6 abstention items** — ⌀X40 and
⌀X50 extend the A01 pair, ⌀X41 and ⌀X43 form the 1894 side of A05, ⌀X49 and ⌀X56 form A06.
**11 near-tie pairs** (NT-1 – NT-11, of which NT-3 is document-plus-majority). **1 decoy
theory** carried by two narrators. **5 internal contradictions** (r03, r07, r08, r09, r10).
1 late reversal; 1 date-only-unreliable narrator; 3 juxtaposing narrators; **13 verbatim
documents** (D1–D13).

**Uniqueness check.** Every planted error sits in exactly one narrator except the twenty-two
values that make up the eleven designed pairs, plus the two decoy poles and the shared ghost
lore. Verified by grep over `test-input/retellings/` after the v2.1 edits.
