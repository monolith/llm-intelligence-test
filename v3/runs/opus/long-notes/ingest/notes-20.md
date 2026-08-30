# Retention notes — Segment 20 (reader 20)

## READER 20'S REPORT ON THIS SEGMENT (read this first)

My instruction file (`v3/runs/opus/long-notes/ingest/segment-20.md`) had **thirty** numbered steps
(steps 1–29 reads, step 30 this write). **I performed all thirty, in order, none skipped**, using only the
Read tool with the exact offsets and limits given. No read failed; no halving was needed. The last read I
performed was **step 29**, which is the last numbered read in the file. ✓

- **Steps 1–3** — reader 19's notes (`notes-19.md`), lines 1–300, 301–600, 601–800. Carried forward below
  **in full**. **My read was again cut at line 800.** This is the **SEVENTH CONSECUTIVE SEGMENT** in which
  the notes hand-off has been truncated at line 800. See the gap warning.
- **Steps 4–29** — `v3/distractors/long/L4-mixed.md`, lines **2738–9460**, in twenty-six chunks.
  **NO RETELLING FOUND. NOT ONE WORD OF LARROW VALLEY MATERIAL IN 6,723 LINES.**
- **Step 30** — write these notes.

---

# ★★★★★ SECTION A — WHAT IS NEW WITH ME. READ THIS BEFORE ANYTHING ELSE.

## A1. ★★★★★ `L4-mixed.md` IS NOW COVERED END-TO-END (lines 1–9460) AND CONTAINS **NO RETELLING**

- Reader 19 read **lines 1–2737** and found nothing.
- **I read lines 2738–9460** and found nothing.
- **COVERAGE IS COMPLETE AND UNBROKEN: lines 1–9460, two readers, no gap.**
- **THE FILE CONTAINS NO KEDDIE, NO OSTREY HOLLOW, NO LARROW GREEN, NO ASHLIN, NO CREAMERY, NO PIPETTE,
  NO BUTTERFAT, NO TEST, NO ARBITRATION, NO DATE LATER THAN 1871. NOTHING.**
- **⚠ MY WINDOW ENDED AT LINE 9460 AND I DID NOT SEE AN `*End of document.*` MARKER.** My final instructed
  read was `offset 9438, limit 23`, landing exactly on 9460 — which strongly suggests 9460 IS the last line
  of the file. But I cannot prove it. **Two readings, and be honest about which you are giving:**
  **(a)** The file ends at 9460 and simply lacks the end-marker, because the marker belongs to the
  *assembled* `rNN-` files (r18 at 7478, r21 at 7092, r24 at 7273 all carry it) and not to the pure-noise
  `LN-` files. **This is the likelier reading** — the instruction file stopped exactly there.
  **(b)** The file continues past 9460 and a later reader should demand lines 9461+.
  **If asked "is L4 clean?", say: lines 1–9460 are read and clean; no retelling; the file appears to end at
  9460 but no end-marker was seen.**

**★★★ THEREFORE READER 19'S NAME-PREFIX RULE IS NOW CONFIRMED, NOT MERELY INFERRED:**
> **`rNN-long.md` = an ASSEMBLED document (TWO headers, TWO seeds) that hides EXACTLY ONE retelling
> numbered NN. `LN-*.md` = PURE NOISE (ONE header, ONE seed) with NO retelling.**
- Confirmed assembled-with-payload: `r18-long.md` (R18), `r21-long.md` (R21), `r24-long.md` (R24).
- Confirmed pure noise: **`L4-mixed.md` (fully read, 1–9460, nothing).**
- Still only *presumed* pure noise: `L3-gibberish.md` — read to 8460 across five readers, nothing found,
  but its end has never been reached. **The L4 result makes "L3 is clean" much more likely. Do not yet call
  it proven.**

## A2. ★★★★★ **I OVERTURN READER 19: THE WORDS-PER-LINE RATIO DOES NOT TRANSFER BETWEEN FILE TYPES.**

Reader 19 wrote, in capitals: *"USE ~8.6 WORDS PER LINE TO PREDICT THE LENGTH OF ANY UNREAD `rNN-long.md`.
By that rule `L4-mixed.md` at 220,000 words should run **roughly 25,000 lines**."*

**THAT PREDICTION IS WRONG BY A FACTOR OF ABOUT 2.6. L4 runs ~9,460 lines, not ~25,000.**

| file | header word count | actual lines | words/line |
|---|---|---|---|
| `r21-long.md` | 61,747 | 7,092 | **8.7** |
| `r24-long.md` | 61,780 | 7,273 | **8.5** |
| **`L4-mixed.md`** | **220,000** | **~9,460** | **~23.3** |

**WHY THE RULE BROKE — and this is the useful part, so give it rather than just the correction:**
1. **The header word counts are generator labels, not measurements.** L4's actual content, counted block by
   block, is nowhere near 220,000 words. My own rough tally of what I read: ~340 gibberish paragraphs at
   ~70 words ≈ 24,000; ~700 ledger entries at ~25 ≈ 17,500; ~700 transcript lines at ~30 ≈ 21,000;
   169 codespec rounds at ~80 ≈ 13,500. **Total on the order of 75,000–80,000 words, not 220,000.**
   ⚠ This is my estimate, not a count. But the shortfall is far too large to be estimation error.
2. **The ratio is dominated by blank lines and by which filler type predominates.** Codespec is extremely
   line-hungry (a five-row table is five lines of two words each); gibberish is line-cheap (70 words on one
   line). A file's ratio is a fact about its *block mix*, not about the generator.
3. **r21 and r24 have near-identical ratios because they are near-identical constructions** (same seeds
   family, same block cycle, same ~61,750-word label). That is a coincidence of sibling files, not a law.

**★★ WHAT TO CARRY FORWARD INSTEAD OF THE RATIO:**
- **For an unread `rNN-long.md`:** expect **~7,100–7,500 lines** and **exactly one retelling** buried
  roughly in the middle third. r18 = 7,478; r21 = 7,092; r24 = 7,273. **That empirical range is worth far
  more than the ratio and it is what actually held three times.** The retelling sat at 4,641 of 7,273 in
  r24 (64%) — ask for the middle-to-late range first.
- **For an unread `LN-` file:** expect **~9,000–10,000 lines** (L4 = ~9,460) and **no retelling**.
- **⚠ REVISED PREDICTION FOR `L3-gibberish.md`, and flag it as a prediction:** L3 advertises the same
  220,000 words as L4 and has been read to 8,460. **If L3 is built like L4 it ends somewhere around
  9,000–10,000 lines — i.e. readers are at roughly 85–95% of it, NOT at "about a third" as reader 19
  stated.** ⚠ **BUT L3 IS PURE GIBBERISH, THE MOST LINE-CHEAP FILLER TYPE, SO IT COULD RUN LONGER PER
  WORD — I do not assert this. I assert only that "L3 has ~25,000 lines" rests on a ratio I have just
  disproved and should not be repeated as fact.** A later reader asked how much of L3 remains should say:
  unknown; the old 25,000-line estimate is unsound; L4 finished at ~9,460.

## A3. ★★★ WHAT ELSE R24 / THE CASE DID **NOT** GAIN THIS SEGMENT

**I found no new Larrow Valley material of any kind.** Every fact in Sections C–E below is carried forward
from reader 19, not discovered by me. **A later reader must not attribute any new case fact to segment 20.**
The two contributions of this segment are (A1) L4 is proven noise-free over 1–9460, and (A2) the
words-per-line rule is refuted.

## A4. ⚠⚠ GAP WARNING — `notes-19.md` RUNS PAST LINE 800 AND I WAS NOT GIVEN THE REST ⚠⚠

My last instructed read of reader 19's notes ended at line 800, **mid-sentence**. Line 800 reads, in full:

> `  transcript pool plus Ives, Trumbull, Vail, Aldous, Oakes, Bascomb, Quarles, Holloway, Underhill, Mabry,`

— the ledger surname pool of `r21-long.md`, cut off mid-list. **Everything reader 19 wrote after that point
is lost to this chain unless a later reader is instructed to read `notes-19.md` past line 800.**

**SPECIFICALLY KNOWN TO BE MISSING, because reader 19 announced it inside my window:**
Reader 19 wrote: *"I have therefore put everything new and everything load-bearing in the FIRST HALF of this
document, **and the carried-forward R19/R20 text after it**."*
**THEREFORE THE FOLLOWING DID NOT REACH ME:**
1. **RETELLING 19 — the Chronicle (1958 newspaper account).** I have only the sentences reader 19 quoted
   inside the R24 commentary. **The full text did not reach me.**
2. **RETELLING 20 — Junia Ammon, firm history, 1949.** Same. I have only fragments, including the
   `$77.39` line that reader 18 was cut off mid-quotation of two segments ago.
3. Any remaining noise-inventory detail for `r21-long.md` past its ledger surname pool.
4. Whatever else reader 19 placed in its second half.

**AND STILL MISSING FROM EARLIER IN THE CHAIN (reader 19 flagged these; they never reached me either):**
5. **RETELLING 22 — Orin Falke, 1959**, county report to the Ordell County board of supervisors. Reader 18
   reproduced it in full; only fragments (¶2, ¶3, ¶4, ¶5, ¶6, ¶7, ¶9, ¶10, ¶11, ¶12 in part) survive as
   quotations. **The full text is gone from the chain.**
6. **RETELLING 23 — Bertram Kyle, 1953**, the Association's clerk writing for the Ordell County Historical
   Society from the Cooperative's office at Larrow Green. Reader 18 called it *"arithmetically the most
   important document in the entire file."* **Only fragments survive.**
7. **The "FIVE AND A QUARTER PER CENT" section under R23**, and **"THE ARITHMETIC LOCK."** Both were
   written; neither reached the chain.

**A later reader asked about the Chronicle's full text, Junia Ammon's full firm history, Falke's full 1959
report, Kyle's full 1953 memoir, or the "five and a quarter per cent" section should say plainly that those
were written but were cut out of the hand-offs at line 800, and should ask for `notes-19.md` lines 801–end
and `notes-18.md` lines 801–end.**

**⚠⚠ THE TRUNCATION IS STRUCTURAL, NOT ACCIDENTAL. It has now hit readers 12, 15, 16, 17, 18, 19 and me —
seven in a row. EVERY READER LOSES THE TAIL OF ITS PREDECESSOR'S NOTES. FRONT-LOAD WHAT MATTERS. DO NOT
SAVE THE IMPORTANT MATERIAL FOR THE END OF THE FILE.** I have accordingly put everything new (Section A)
first, the primary document R24 second, and the analysis and inventories after. **Later readers: keep this
ordering.**

## A5. ★ RETELLING COUNT — THERE ARE AT LEAST TWENTY-FOUR; I DO NOT CLOSE THE SET

R24 exists and is reproduced below. **I make no claim that R24 is the last.** Reader 18 explicitly refused to
close the question of whether an R24 existed, and that refusal is exactly what produced the correct
prediction that found it. **Copy the habit.** If a `r25-long.md` or similar exists, assume it hides an R25
in its middle-to-late third and demand ~7,100–7,500 lines of it.

---

# ★★★★★ SECTION B — RETELLING 24, QUOTED IN FULL (carried forward complete from reader 19)

### ORRA KEDDIE, *A FARM WOMAN'S BOOK, 1897–1930* — `r24-long.md` lines 4641–4720, published 1964

Chapter heading, exactly: **`## Chapter 20 — Retelling 24 — Orra Keddie, "A Farm Woman's Book, 1897–1930,"
diary extracts published 1964`**, repeated on the next line as
**`# Retelling 24 — Orra Keddie, "A Farm Woman's Book, 1897–1930," diary extracts published 1964`**.

Italic headnote, exactly:
> *"Extracts from a diary kept at Ostrey Hollow, printed from the three notebooks now in the family's hands.
> The preface and the bracketed notes are the editor's."*

**★★★ WHY THIS DOCUMENT MATTERS MORE THAN ANY OTHER IN THE FILE: it is the only source written from inside
the Keddie house, contemporaneously, by someone with no stake in the argument and no theory to defend. Every
other narrator is reconstructing. Orra Keddie was writing the same week. She is also the only woman's voice
in the case apart from Ivy's single telephone quotation and Hazel Brant's tape, and she is the only person
in the entire file who records what the accusation cost the family socially rather than financially.**

### THE EDITOR'S PREFACE, quoted entire

> **"Preface.** Orra Keddie was born in 1866 and married Ansel Keddie in 1889. He was tester and separator
> man at the Ostrey Hollow skimming station of the Larrow Valley Cooperative Creamery Association, and kept
> its books in his own hand for twenty-nine seasons. She began the diary in the spring of 1897 and closed it
> in 1930, and it was kept in three ruled notebooks bought at Ashlin. The pages covering her girlhood and her
> family before 1889 were not preserved; nothing in her hand survives from before the marriage. She writes A.
> for her husband throughout. A single later leaf, written in 1934 and laid loose inside the back cover of
> the third book, is printed at the end. The entries have been chosen for what they show of the household and
> the season; nothing has been added and nothing altered but the spelling of two place names."*

**★ FACTS ESTABLISHED BY THE PREFACE:**
- **Orra Keddie born 1866; married Ansel Keddie 1889.** ✓ The 1889 marriage matches R20's note. She was 23
  at marriage; Ansel, born 1861, was 28.
- **Ansel was "tester AND SEPARATOR MAN"** — a two-part job title the chain has not had in this exact form.
  He did not merely test; he ran the separator.
- **"kept its books in his own hand for TWENTY-NINE SEASONS."** ⚠⚠ **THE CHAIN'S FIRST HARD FIGURE FOR THE
  LENGTH OF HIS SERVICE, CONFIRMED TWICE INSIDE THE DIARY ITSELF** (30 April 1925: "Twenty-nine seasons and
  a letter"). **CHECK IT: the station opened 4 May 1896 and he was dismissed 30 April 1925. 1896 through
  1924 inclusive is 29 seasons; in 1925 he was put out one week before the season he would have worked.
  TWENTY-NINE IS EXACTLY RIGHT.** ✓ **This retires any loose talk of "a quarter of a century" as the length
  of his service — the quarter-century figure belongs to the *complaints* (1900–1925), not to his employment
  (1896–1925).**
- **Diary begun spring 1897, closed 1930; three ruled notebooks bought at Ashlin.**
- **⚠ "The pages covering her girlhood and her family before 1889 were not preserved; nothing in her hand
  survives from before the marriage."** Load-bearing: **the diary CANNOT tell us Orra's maiden name.** She
  names a brother, Emmet, and we are never given his surname. See the Brant question (C3).
- **"She writes A. for her husband throughout."** Every "A." in the entries is Ansel Keddie.
- **The 1934 leaf is loose, not bound — written four years after she closed the book.**
- **"nothing has been added and nothing altered but the spelling of two place names."** ⚠ The editor does
  not say WHICH two place names or what the original spellings were. **If asked whether "Ostrey Hollow" or
  "Larrow Green" is spelled as Orra spelled it, the honest answer is: we do not know; the editor silently
  normalized two place names and did not say which.**

### THE ENTRIES, QUOTED ENTIRE AND IN ORDER

> *April 4, 1897.* Ground still frozen a spade down. Set the eggs. A. gone before light as always and back
> after dark, and he has walked it both ways this week because the mare is lame.

> *May 1, 1897.* A. says the station's own glass came up and they are done borrowing of Larrow Green. He is
> pleased about it. A man is pleased about small things when he is let.

> *July 19, 1897.* Hot. Cut the home piece. Wild strawberries thick along the station road, and I picked a
> pail on the way down with A.'s dinner.

> *February 3, 1898.* Twenty below at the door this morning. A. broke the path to the station himself at
> four o'clock. He says the milk comes in with the frost still on the cans.

> *September 12, 1899.* Duncan five years old and reads anything set before him. His father says nothing but
> I saw him listening at the door.

> *March 1902.* Talk at the store that our milk up here runs poorer than theirs down the valley. A. came home
> and would not eat. I said it is not your cows and not your hands, and he said no, but it is my figures they
> will look at. Then he said no more about it.

> *June 6, 1904.* Currants. Rain every afternoon this week at four o'clock, you could set the clock by it.

> *January 1908.* Four men up the road today in Grigg's sleigh, come to look into the herds. They went to my
> brother Emmet's first, being the biggest, and he gave them their dinner. They were civil enough to me. They
> wanted to see the barns and not the station, which A. remarked on afterward and let alone.

> *March 1908.* The committee gone back down. Their word is that it is the wet hay of the bottom that thins
> the cream. My brother Emmet says the bottom fed his father and it will feed him. A. says nothing at all,
> which is his way, and is not always kindness to me.

> *August 30, 1910.* Threshing. Fourteen men to dinner and I had a girl up from the lower place to help. Two
> pies short and I have not lived it down.

> *May 8, 1911.* A. home cross about a broken measure. Rain all day, the low piece under water again.

> *October 1911.* Duncan gone to the school at Ashlin to teach, seventeen and looks fourteen. His father
> drove him down and came back without a word in him.

> *April 1914.* Set out six apple trees below the house. I shall not see them bear well but somebody will.

> *November 1917.* Snow before the corn was in. Everything late this year and everything short.

> *June 1919.* A circular came to the station for the patrons, over the manager's name, about water in the
> milk. A. would not put them in the mail nor leave them on the platform. He took them round himself, to
> eleven families, and stood at the door while each man read it, and came home at eleven at night with his
> hat still on.

> *June 1919, two days after.* My brother Emmet came up. He did not come in. He stood in the yard and said to
> A. that he had hauled whole milk to that station since the day it opened and A. knew it better than any man
> living, and then he asked him why he had carried the paper himself if he did not believe it. A. said he
> carried it because he would not have another man carry it. He went home. He has not been in this house
> since, and he is my brother.

> *Christmas, 1919.* Duncan up from Ashlin for two days. A good day and I will write it down as one.

> *February 1921.* Ice storm. The station road impassable two days and the milk stood.

> *July 1923.* Hay in good and not a drop on it. A. says they have new glass at the station and new pails,
> and the roof is still bad, which is the Association all over. He has been in this hollow the whole of his
> life and has never yet seen them mend a roof before it fell in.

> *November 1924.* Killing weather. A. up before four every day of his life for as long as I have known him,
> and he has never once said he was tired in my hearing, and he has never once been late.

> *January 1925.* The patrons have put in a paper against the station. My brother Emmet's name is on it. I do
> not blame him and I will not say so to A.

> *March 17, 1925.* A. went down to Ashlin this morning in his good coat, which he has had since Duncan was
> married. There is a board of men to hear the whole thing out. He was up at three and did not sleep before
> that either. I ironed the coat twice for want of anything I could do.

> *April 1925.* Two of the sittings held up here at the station itself, in the weigh room, with the men
> standing outside in the road. I did not go down. I could hear the wagons from the yard all that afternoon
> and that was enough of it for me.

> *April 30, 1925.* They have put him out. Twenty-nine seasons and a letter. He came up the road at his
> ordinary hour with his apron rolled under his arm and hung it behind the shed door and asked what there was
> for supper. There was ham. He ate it.

> *May 1925.* [The award of the board is not mentioned in the diary. — Ed.]

> *June 1925.* He has begun on the cow shed, which has wanted doing since his father's time. He works at it
> from light to dark and whistles, which he never did when he was paid.

> *1926.* [Several leaves torn out. The editor has not attempted to supply them. — Ed.]

> *October 1927.* A. mending stairs at the far end of the hollow, and the Loomis gate, and half the doors in
> this hollow, and taking what they offer. A carpenter at sixty-six. He is better at it than he ever was at
> the other and it pays a quarter of what the other did.

> *Spring 1929.* Word this morning that my brother Emmet is dead. I went down. Roy met me at the gate and was
> kind. I sat an hour in that kitchen where I was a girl and came home. Ten years and neither of them would
> go up the road first, and now it is settled the way those things get settled.

> *July 1929.* Hollyhocks the best I have had. A. sat out with me an evening and named the ones my mother
> had.

> *August 1930.* I am sixty-four and my hand is not what it was. I have kept this book thirty-three years and
> there is less in it every year, which is not because less happens.

> ---
>
> *[The last leaf, laid loose in the back of the third book.]*
>
> *February 1934.* A. died this morning, at home, in the forenoon, without much pain at the end of it. Duncan
> came up in the night. There were more at the burying than I looked for, and men shook my hand who had not
> spoken to him in nine years, and every one of them said what a hand he was with a door. Not one of them
> said the other thing. Nine years they have had to say it and they had not said it and they did not say it
> then. He never asked them to. He said to me once and only once, and not lately, that a man cannot be
> cleared of a thing nobody will name.
>
> *[Ansel Keddie's name was cleared in 1958, twenty-four years after his death. His widow did not live to see
> it; she died in 1948. — Ed.]*

---

# ★★★★★ SECTION C — WHAT R24 SETTLES, CONFIRMS, BREAKS AND ADDS
### (reader 19's analysis, carried forward complete — READ BEFORE ANSWERING ANYTHING)

### C1. ★★★★★ THE GLASS ARRIVED 1 MAY 1897. SETTLED BY FOUR SOURCES. KYLE IS WRONG.

> *May 1, 1897.* **"A. says the station's own glass came up and they are done borrowing of Larrow Green."**

- **Contemporaneous, written the day it happened, by a witness with no reason to lie about a date.** It
  matches R20's invoice-based "the first of May, 1897" and the Chronicle's "the spring of 1897."
- **⚠⚠ IT REFUTES KYLE'S "THE FIRST OF MAY, 1898" OUTRIGHT.** Reader 18 had already ruled: *"PREFER 1897 —
  it rests on a dated invoice (14 April 1897) reproduced in facsimile, plus Junia Ammon's prose, plus the
  Chronicle. Kyle's year is wrong, and Kyle warns the reader in his own document that his years are
  unreliable."* **R24 IS THE FOURTH INDEPENDENT SOURCE FOR 1897 AND THE ONLY CONTEMPORANEOUS ONE. THE
  QUESTION IS CLOSED. GIVE 1 MAY 1897. Record Kyle's 1898 as a memory slip of exactly one year — same day,
  same month.**
- **★★★ AND IT ADDS A FACT NOBODY ELSE IN THE CHAIN HAS: BEFORE 1 MAY 1897 THE OSTREY HOLLOW STATION WAS
  BORROWING GLASS FROM LARROW GREEN.** *"they are done borrowing of Larrow Green."* **Work the chronology:**
  - The station opened **4 May 1896**.
  - The invoice for its own outfit is dated **14 April 1897**; the glass came up **1 May 1897**.
  - **THEREFORE FOR ITS ENTIRE FIRST YEAR — MAY 1896 TO MAY 1897 — THE OSTREY HOLLOW STATION TESTED ON GLASS
    BORROWED FROM THE LARROW GREEN CREAMERY, AND ITS TESTS IN THAT YEAR WOULD HAVE BEEN CORRECT.**
  - **THE LOW TESTS THEREFORE CANNOT HAVE BEGUN BEFORE MAY 1897.** ⚠⚠ **THIS CONTRADICTS THE CHRONICLE
    (R19), WHICH SAYS "from very nearly the day the station opened, the milk of Ostrey Hollow tested lower
    than the milk of anywhere else in this county."** Two readings, and do not choose blindly:
    **(a)** The Chronicle is loose — "very nearly the day it opened" is a newspaperman's rounding for
    "within a year of opening," and one year out of twenty-nine rounds away. **This is the likelier reading**
    and it costs nothing.
    **(b)** The Chronicle is right and the borrowed Larrow Green glass was ALSO short — which would mean the
    contamination was wider than one crate and would revive Junia Ammon's "they went out very much alike"
    worry with a vengeance. **Nothing supports this; do not assert it.**
    **BUT NOTE WHICH WAY THE 1911 EPISODE CUTS: in 1911 the station borrowed glass again and the tests went
    UP. If Larrow Green's glass had been short too, the 1911 tests would not have risen. THE 1911 EPISODE IS
    POSITIVE EVIDENCE THAT LARROW GREEN'S GLASS WAS SOUND, WHICH MAKES READING (a) RIGHT AND MEANS THE
    STATION'S FIRST YEAR WAS CLEAN.** Give this. It is a genuine inference and it is well supported.
  - **★★★ AND IT MAKES THE 1911 EPISODE A REPEAT, NOT A NOVELTY.** Ansel had run this station on Larrow
    Green's glass before, in 1896–97, and knew what its milk read on borrowed glass. **When the 1911
    borrowing pushed the tests up, he was not comparing against nothing — he was comparing against his own
    first season. THAT IS WHY HE SAID IT WAS SOMETHING IN THE GLASS AND SAID IT TWICE. He had seen the
    station read high on Larrow Green's glass fourteen years earlier.** Nobody in the chain made this
    connection before reader 19. It converts Ansel's 1911 hypothesis from a lucky guess into a reasoned
    inference from his own experience, and it makes Kepp's 1926 dismissal of the borrowed-glass objection
    worse, not better.
  - **⚠ It also means the money computation may be one year long.** Ivy's $19,000 rests on 40,000,000 lb of
    milk at 1,600,000 lb/year — Kyle's figures — which is **exactly 25 years**, not 29. **So the money was
    computed over the twenty-five years of the complaint (1900–1925), NOT over Ansel's twenty-nine seasons,
    and NOT over the twenty-eight years the bad glass was actually in use (May 1897 – June 1923).** Nobody
    states this. **The arithmetic is internally consistent at 25 years; do not "fix" it to 28 or 29.**

### C2. ★★★★★ THE 1919 CIRCULAR WENT TO **ELEVEN** FAMILIES. THE COUNT NOW HAS THREE VALUES.

> *June 1919.* **"He took them round himself, to eleven families, and stood at the door while each man read
> it, and came home at eleven at night with his hat still on."**

| count | source | what it counts | strength |
|---|---|---|---|
| **six farms** | 1908 report (×2), Grigg's letter, Kepp, Hazel Brant, Chronicle R19 — **six sources** | **farms** | strongest for *farms* |
| **nine families** | R08 (Selby Vose's letter) | **families** the circular went to | one source |
| **ELEVEN families** | **R24 (Orra Keddie, 1919, contemporaneous)** | **families ANSEL PHYSICALLY CARRIED IT TO** | **eyewitness, same night** |

- **Reader 18's proposed reconciliation was: "six farms, nine households (sons, widows, tenants on the same
  farms)." R24 makes that shape more likely, not less — but pushes the household count to eleven.**
- **★★ THE CLEANEST READING, OFFERED AS A READING NOT A FACT: SIX FARMS, ELEVEN HOUSEHOLDS. The "nine" in
  R08 may be the number of PATRONS ON THE ASSOCIATION'S BOOKS; the "eleven" is the number of DOORS ANSEL
  STOOD AT, which would include households that were not separately booked patrons.** Ansel had no reason to
  skip a door and Orra had no reason to miscount a number her husband told her that night.
- **⚠ DO NOT ASSERT ANY OF THE THREE AS THE ANSWER. Record all three with their sources.** If asked "how
  many farms," say **six** (six sources). If asked "how many families got the 1919 circular," say **the
  sources disagree — nine per Vose's letter, eleven per the wife of the man who delivered them by hand.**
- **★ AND THE ENTRY ADDS A DETAIL THAT MATTERS MORE THAN THE COUNT: ANSEL DELIVERED THE WATER ACCUSATION BY
  HAND, TO EVERY DOOR, AND STOOD THERE WHILE EACH MAN READ IT.** He would not mail it and would not leave it
  on the platform. **He came home at eleven at night with his hat still on.** That is the single most
  devastating image in the file and it is one sentence long.

### C3. ★★★★★ THE FEUD WITH EMMET — THE HUMAN CENTER OF THE CASE

**Orra Keddie's brother EMMET.** Everything known about him:
- **Her brother.** Farm at **Hessel Bottom** — inferred: the 1908 committee "went to my brother Emmet's
  first, **being the biggest**," and R22 (per reader 18) says the 1908 committee "sampled the **Hessel
  Bottom** herds." **Emmet had the biggest herd in the bottom.**
- **January 1908:** gave the four committeemen their dinner.
- **March 1908:** *"the bottom fed his father and it will feed him"* — his answer to the wet-hay verdict.
  **Note: "his father," i.e. Orra's father too — the family farm passed to Emmet.** *"that kitchen where I
  was a girl"* (1929) confirms Orra grew up on Emmet's farm.
- **June 1919, two days after the circular:** the confrontation, quoted in full in Section B. **He would not
  come in. He stood in the yard.** He said he *"had hauled whole milk to that station since the day it
  opened and A. knew it better than any man living,"* and asked *"why he had carried the paper himself if he
  did not believe it."* **Ansel: "he carried it because he would not have another man carry it."**
  **★★★★ THAT EXCHANGE IS THE WHOLE TRAGEDY IN SIX LINES. Emmet's question is unanswerable and Ansel's
  answer is both true and useless. Ansel took the duty precisely BECAUSE he thought the accusation was
  wrong — he would not let a stranger deliver it — and to Emmet that looked like endorsement. Quote this
  whenever anyone asks why the valley turned on Ansel Keddie.**
- **"He has not been in this house since, and he is my brother."**
- **January 1925:** *"The patrons have put in a paper against the station. My brother Emmet's name is on
  it. I do not blame him and I will not say so to A."* **Emmet was a signatory to the petition that produced
  the 1925 arbitration.**
- **Spring 1929: Emmet dies.** *"Ten years and neither of them would go up the road first, and now it is
  settled the way those things get settled."* **The estrangement ran ten years, June 1919 → spring 1929.**
- **ROY** — *"Roy met me at the gate and was kind."* **Presumably Emmet's son.** Nothing else is said of
  him. **Do not build on it.**

**⚠⚠ THE BRANT QUESTION — FLAG IT AND DO NOT RESOLVE IT.** Reader 17/18's carried material says **Ansel
Keddie married ORRA BRANT in 1889**, and the chain contains a **Hazel Brant** taped in 1981 who gave the
"nineteen hundredths, flat as a floor" line and who called the room the "weigh room." **If Orra's maiden name
was Brant, then EMMET was EMMET BRANT, ROY was ROY BRANT, and HAZEL BRANT is very likely of that family —
i.e. the 1981 witness is a descendant of the man who broke with Ansel Keddie over the 1919 circular.**
**BUT R24'S OWN PREFACE SAYS: "The pages covering her girlhood and her family before 1889 were not
preserved."** The diary never gives Emmet a surname. **The Brant identification rests entirely on the
carried-forward "married Orra Brant in 1889," which reached the chain inside reader 18's R20 commentary and
which no reader has seen in a primary source since.** **STATE THE HYPOTHESIS, MARK IT UNPROVEN, AND NOTE WHAT
WOULD SETTLE IT: any source giving Emmet's or Hazel's full family line.** If true, it is the most important
undiscovered relationship in the file, because it means the valley's most-quoted late witness was on the
other side of the feud.

### C4. ★★★★ THE 1908 COMMITTEE HAD **FOUR** MEN IN IT, NOT THREE — OR HAD THREE AND A DRIVER

> *January 1908.* **"Four men up the road today in Grigg's sleigh, come to look into the herds."**

- The chain carries the 1908 body as **"a three-man committee of farmers chaired by Nyle Grigg" (R15)**.
- **Orra counted four men in the sleigh.** ⚠ Reconciliations, none provable: **(a)** three committeemen plus
  Grigg, who chaired but was not counted among the three; **(b)** three committeemen plus a driver; **(c)**
  four committeemen and R15's "three" is wrong; **(d)** Orra counted heads in a sleigh from a window, which
  is not a roll call.
- **★★ PREFER "THREE-MAN COMMITTEE" as the formal body — it is on a document — AND RECORD ORRA'S "four men
  in Grigg's sleigh" AS WHAT ARRIVED AT THE DOOR. They are not necessarily in conflict.** Note reader 18's
  standing warning that the 1908 committee and the 1925 board are constantly confused (the Chronicle fused
  them); **do not let this four/three wobble become a fourth version of that confusion.**
- **★★★ AND ORRA SUPPLIES THE SINGLE MOST DAMNING PROCEDURAL FACT IN THE ENTIRE 1908 INQUIRY:**
  > **"They wanted to see the barns and not the station, which A. remarked on afterward and let alone."**
  **THE 1908 COMMITTEE INVESTIGATING WHY ONE STATION'S MILK TESTED LOW DID NOT LOOK AT THE STATION.** They
  looked at the cows. **Ansel noticed and said nothing.** This is the earliest instance in the file of the
  pattern the Chronicle named in 1958 — *"Nobody, in all those years of it, appears to have thought the
  trouble might be furniture"* — and it is now dated to January 1908 and attributed. **Quote the Chronicle's
  line and Orra's line together. They are the same finding fifty years apart, one from a newspaper and one
  from a farm kitchen.**
- **★ "wet hay of the bottom thins the cream" (March 1908) ✓ CONFIRMS THE HAY THEORY AND ITS 1908 ORIGIN**,
  which the chain already had from Grigg's 1908 finding (reprinted by the Association in 1919) and from
  Kepp's 1926 writing. **R24 dates the verdict to March 1908 and shows it was delivered to the valley
  verbally, "their word is that…," before anything was printed.**

### C5. ★★★★ 8 MAY 1911 — THE BROKEN MEASURE, CONFIRMED, AND THE SILENCE EXPLAINED

> *May 8, 1911.* **"A. home cross about a broken measure. Rain all day, the low piece under water again."**

- **✓✓ THE DATE 8 MAY 1911 IS NOW CONFIRMED BY A CONTEMPORANEOUS DIARY ENTRY.** The chain's chronology has:
  8 May 1911 the station's own measuring glass breaks → nine weeks on borrowed glass, tests markedly higher
  → 10 July 1911 own glass resumes, tests fall back the same day. **Orra's entry is the independent anchor
  for the first of those three dates.**
- **★★★★★ AND HERE IS WHAT MAKES THIS ENTRY DEVASTATING: SHE RECORDS THE BREAKAGE AND SHE DOES NOT RECORD
  THE HYPOTHESIS.** The chain holds, from Duncan Keddie (R18, written 1968), that in **the summer of 1911**
  Ansel came home saying it was **something in the glass**, said it **twice** — at supper and again by the
  door — and **wrote a question mark in the station book**. **ORRA'S DIARY, WHICH SHE WAS KEEPING THAT VERY
  SUMMER, DOES NOT CONTAIN IT.** There is no entry between 8 May 1911 and October 1911.
  **THREE READINGS, AND DO NOT CHOOSE BLINDLY:**
  **(1)** *The editor cut it.* The preface says entries "have been chosen for what they show of the household
  and the season." **A 1964 editor selecting for domestic colour would very plausibly drop a sentence about
  butterfat testing. THIS IS THE STRONGEST READING and it means R24's silence is not evidence of anything.**
  **(2)** *She heard it and did not think it worth writing.* Consistent with her own 1930 line — *"there is
  less in it every year, which is not because less happens."*
  **(3)** *Duncan misremembered the year.* **Weak** — Duncan was seventeen and in the kitchen, and R22 says
  the bulletin found the 1911 material decisive.
  **★★ WHICHEVER READING IS RIGHT, DO NOT SAY "ORRA'S DIARY DISPROVES DUNCAN." IT DOES NOT. An edited
  extract's silence proves nothing about the unedited notebook, and the notebooks survive — the preface says
  they are "now in the family's hands."** **THAT IS AN ACTIONABLE FACT: THE THREE ORIGINAL NOTEBOOKS EXISTED
  IN 1964 AND WERE HELD BY THE FAMILY. If anything could settle the 1911 question, it is those notebooks,
  unedited. Nobody in the file appears to have gone back to them.**
- **⚠ AND NOTE WHAT ORRA *DOES* RECORD ABOUT 8 MAY 1911: "A. home CROSS."** Not puzzled, not excited —
  **cross**. A man annoyed about a broken piece of equipment. **The insight, if it came, came later in the
  nine weeks, as the tests climbed. That fits Duncan's "the summer of 1911" perfectly and it fits the
  mechanism: you cannot infer anything from a breakage; you infer it from what the replacement reads.**

### C6. ★★★★ THE 1925 ARBITRATION — TWO SITTINGS WERE HELD AT THE STATION, IN THE **WEIGH ROOM**

> *April 1925.* **"Two of the sittings held up here at the station itself, in the weigh room, with the men
> standing outside in the road."**

- **★★★ WHOLLY NEW: THE BOARD OF ARBITRATION DID NOT SIT ONLY AT ASHLIN. TWO OF ITS SITTINGS WERE HELD AT
  THE OSTREY HOLLOW STATION ITSELF.** The chain has the board sitting "at Ashlin from the 17th of March to
  the 4th of May" (R22) under Alonzo Frick (R13, Nym's minute book Item 7). **R24 does not contradict that —
  Ashlin was the seat — but it adds that the board went up the valley in April and sat in the very room
  where the tests were made.**
- **★★★★★ AND HERE IS THE CRUELLEST FACT IN THE ENTIRE CASE: THE BOARD OF ARBITRATION SAT TWICE IN THE
  WEIGH ROOM OF THE OSTREY HOLLOW STATION, AND THE CRATE OF CONDEMNED PIPETTES WAS IN THE LOFT DIRECTLY
  OVER THEIR HEADS.** The crate had been there since **1923** (condemned 12 June 1923 by Merle Strawn) and
  stayed until **February 1958**, when Ivy Keddie went up the ladder. **The men deciding whether Ansel Keddie
  had cheated the valley sat, twice, in the room beneath the evidence that would have cleared him.** Ivy
  Keddie told the Chronicle in 1958: *"It would have been a kindness if somebody in this county had thought
  to climb a ladder."* **She did not know that a board of arbitration had sat under that ladder for two days
  in April 1925. GIVE THIS. It is the sharpest thing the chain holds and no source states it — it falls out
  of putting R24 beside R19 and R22.**
- **★★ AND IT RESOLVES THE ROOM QUESTION FROM A NEW DIRECTION.** The chain had a long dispute: **intake
  room** (Ivy R04, Rundle R12, Duncan R18, Chronicle R19, Falke R22 — five sources) vs **weigh room** (Hazel
  Brant R17), dissolved by Cleve Oram (R21) stating the two are **the same room**. **Orra Keddie, who lived a
  walk from it for her whole married life, calls it the WEIGH ROOM.** **That is a second independent local
  voice for "weigh room" and it strengthens Oram's dissolution rather than reopening the conflict: the people
  who lived there said weigh room; the people who wrote reports said intake room; it is one room. THE
  QUESTION IS CLOSED AND NOW HAS AN EXPLANATION FOR WHY IT EVER LOOKED OPEN — it is a register difference
  between local speech and official prose, not a factual disagreement.**
- **★ "with the men standing outside in the road"** — the valley turned out for it. **"I did not go down. I
  could hear the wagons from the yard all that afternoon and that was enough of it for me."**

### C7. ★★★★ THE DISMISSAL — 30 APRIL 1925, CONFIRMED, AND NOW WITH THE SCENE

> *April 30, 1925.* **"They have put him out. Twenty-nine seasons and a letter. He came up the road at his
> ordinary hour with his apron rolled under his arm and hung it behind the shed door and asked what there was
> for supper. There was ham. He ate it."**

- **✓✓ 30 APRIL 1925 CONFIRMED** — matches R22's "The tester was dismissed on the 30th of April, 1925, four
  days before the award." **Two independent sources, one official, one domestic, on the same day.**
- **✓ "Twenty-nine seasons"** ✓ matches the preface. **"and a letter"** — **he was dismissed BY LETTER.**
  New. **He was not told to his face.**
- **★★ "There was ham. He ate it." Quote it. Nothing else in the file conveys the man as economically.**

### C8. ★★★ MARCH 17, 1925 — THE ARBITRATION'S OPENING DAY, CONFIRMED, AND THE COAT

> *March 17, 1925.* **"A. went down to Ashlin this morning in his good coat, which he has had since Duncan
> was married. There is a board of men to hear the whole thing out. He was up at three and did not sleep
> before that either. I ironed the coat twice for want of anything I could do."**

- **✓✓ 17 MARCH 1925 CONFIRMED** — matches R22 ("a board of arbitration sat at Ashlin from the 17th of March
  to the 4th of May") and R13 (Nym's minute book, Item 7, 17 March – 4 May 1925). **Now three sources, one of
  them contemporaneous.**
- **★ "which he has had since Duncan was married" — DUNCAN KEDDIE WAS MARRIED BEFORE MARCH 1925.** New,
  small, undated. Duncan was born 1894, so he married as an adult sometime before 1925. **Ivy was born
  1931.** No conflict; just a new datum.
- **★ "There is a board of men to hear the whole thing out"** — Orra does not name Frick and does not use
  the word arbitration. **She did not know the machinery. Nobody explained it to the tester's wife.**

### C9. ★★★ THE AFTERMATH — THE CARPENTER YEARS, AND AN AGE CHECK THAT WORKS

> *June 1925.* **"He has begun on the cow shed... He works at it from light to dark and whistles, which he
> never did when he was paid."**
> *October 1927.* **"A. mending stairs at the far end of the hollow, and the Loomis gate, and half the doors
> in this hollow, and taking what they offer. A carpenter at sixty-six. He is better at it than he ever was
> at the other and it pays a quarter of what the other did."**

- **★★ AGE CHECK: "a carpenter at sixty-six" in October 1927. Ansel Keddie born 1861 → 1927 − 1861 = 66. ✓
  EXACT. This independently confirms the 1861 birth year the chain carries from Duncan (R18: born 1861, died
  1934).** Two sources, one arithmetic. **Ansel Keddie's birth year is settled: 1861.**
- **★ NEW NAME: the LOOMIS GATE** — a Loomis family in Ostrey Hollow. Nothing else known. **Do not build
  on it.**
- **★ "it pays a quarter of what the other did"** — the only figure anywhere for what the tester's post paid
  relative to day-carpentry. **Ratio only, no dollars.**
- **★★ "He is better at it than he ever was at the other."** His wife's verdict, and it is not flattering to
  the case: **she thought he was a better carpenter than tester.** Set beside the 1934 leaf — *"every one of
  them said what a hand he was with a door"* — the valley agreed. **This does NOT mean he tested badly; the
  glass was short and no tester could have caught it by looking (see R20, "not hold it, DELIVER it"). But it
  is an honest note and the chain should not suppress it.**

### C10. ★★★★ THE 1926 GAP — SEVERAL LEAVES TORN OUT

> *1926.* **[Several leaves torn out. The editor has not attempted to supply them. — Ed.]**

- **⚠⚠ THE ONLY DELIBERATE PHYSICAL DESTRUCTION ANYWHERE IN THE FILE, AND IT IS EXACTLY ON THE YEAR THE
  CHAIN MOST WANTS.** 1926 is the year an unnamed gentleman put the 1911 borrowed-apparatus objection to
  Kepp — "the veterinarian of standing at Ashlin" (R22 ¶9) who was writing up the hay theory — **and Kepp
  talked him down** (R16). Reader 16 recorded that **Ansel Keddie himself** or **Duncan Keddie** are the
  most natural candidates for that gentleman.
- **★★★ DO NOT OVERREAD THE TORN LEAVES. They are torn out; we do not know by whom, when, or why, and the
  1964 editor did not speculate. Grief, a family quarrel, or a use for the paper are all as likely as
  concealment.** But record the coincidence plainly: **the diary of the tester's wife is silent for 1926 by
  physical removal, and 1926 is the year the objection that would have solved the case was raised and
  dismissed.** **A later reader asked "who was the gentleman who went to Kepp in 1926?" should say: still
  unproven; Ansel and Duncan are the natural candidates; and note that the one contemporaneous household
  record of 1926 has had its leaves torn out.** **DO NOT ASSERT AN IDENTIFICATION.**

### C11. ★★★★ THE 1934 LEAF — THE NINE YEARS OF SILENCE, AND ANSEL'S LAST WORD

> *February 1934.* **"...men shook my hand who had not spoken to him in nine years, and every one of them
> said what a hand he was with a door. Not one of them said the other thing. Nine years they have had to say
> it and they had not said it and they did not say it then. He never asked them to. He said to me once and
> only once, and not lately, that a man cannot be cleared of a thing nobody will name."**

- **✓ ANSEL DIED FEBRUARY 1934, AT HOME, IN THE FORENOON.** Confirms R18/R19/R21's "died in 1934" and adds
  the month, the place and the hour. **Duncan came up in the night** — he was there.
- **★★ "nine years" — 1925 to 1934 ✓.** The valley did not speak to him for the nine years between his
  dismissal and his death, then came to the burying.
- **★★★★★ "a man cannot be cleared of a thing nobody will name." THIS IS THE FILE'S BEST SENTENCE AND IT IS
  ANSEL KEDDIE'S OWN, REPORTED BY THE ONLY PERSON HE SAID IT TO.** It is also a precise statement of his
  epistemic trap: **the charge against him was never formally made** — the 1925 award was "without
  admission," the water circular was "in a civil form of words," nobody at the burying "said the other
  thing" — **and an unstated charge cannot be answered.** **Quote it against Ivy's "I would like it printed
  that he never knew" and against the Chronicle's "Nobody... appears to have thought the trouble might be
  furniture." Those three sentences are the case.**
- **★★★★★ AND IT SHARPENS THE CHAIN'S CENTRAL IRONY ONE MORE TURN. Readers 17 and 18 established that Ivy
  Keddie told the Chronicle in 1958 "I would like it printed that he never knew," and that this is FALSE —
  Ansel knew, or suspected correctly, in 1911. R24 now shows he ALSO knew he could not be cleared, and said
  so, once, to his wife. HE UNDERSTOOD HIS OWN POSITION COMPLETELY: he had the right hypothesis and no
  proof, and he was accused of something nobody would state. THE ONLY THING HE DID NOT KNOW WAS THAT HIS
  GRANDDAUGHTER WOULD BE BORN THREE YEARS BEFORE HE DIED AND WOULD CLIMB THE LADDER.** (Ivy born 1931;
  Ansel died 1934. **They overlapped by three years. She was three years old when he died.**)

### C12. ★★★ THE EDITOR'S CLOSING NOTE — ORRA KEDDIE DIED IN 1948

> *[Ansel Keddie's name was cleared in 1958, twenty-four years after his death. His widow did not live to see
> it; she died in 1948. — Ed.]*

- **★★ ORRA KEDDIE: BORN 1866, DIED 1948, AGED 81 OR 82. She missed the vindication by ten years.**
- **✓ "twenty-four years after his death" — 1958 − 1934 = 24 ✓** matches the Chronicle's *"He had been dead
  twenty-four years when the bulletin appeared this week."* **Two sources, same arithmetic.**
- **★★ THE PUBLICATION DATE IS 1964 — SIXTEEN YEARS AFTER ORRA'S DEATH AND SIX AFTER THE VINDICATION. The
  diary was published BECAUSE the name had been cleared.** Nobody prints a farm woman's diary about a
  disgraced tester; they print it about a vindicated one. **The editor's closing bracket is the reason the
  book exists.** ⚠ Inference, not stated. But note the sequence of the whole documentary record:
  **1949 Ammon (before) → 1953 Kyle (before) → 1958 Chronicle + Bulletin 471 (the event) → 1959 Falke →
  1964 Orra's diary → 1968 Duncan → 1977 Oram → 1981 Hazel Brant.** **Only two documents in the entire file
  were written before anyone knew the answer: Junia Ammon's firm history (1949) and Bertram Kyle's memoir
  (1953). EVERYTHING ELSE IS RETROSPECT. That is why reader 18 called Kyle's ledger line — written before
  anybody had measured anything — decisive. WEIGH THE TWO PRE-1958 DOCUMENTS HEAVIEST ON ANY DISPUTED FACT.**

### C13. ★★ SMALLER CONFIRMATIONS AND NEW DOMESTIC DETAIL FROM R24

- **✓ DUNCAN KEDDIE'S BIRTH YEAR: 1894.** *Sept 12, 1899: "Duncan five years old"* → born 1894 (or late
  1893). *Oct 1911: "Duncan gone to the school at Ashlin to teach, seventeen"* → 1911 − 17 = 1894. ✓ **Two
  independent internal checks agree. And it confirms R18's kitchen scene: Duncan was seventeen in 1911.**
- **✓ DUNCAN TAUGHT AT ASHLIN FROM OCTOBER 1911, AGED SEVENTEEN.** Confirms the Chronicle's *"her father
  taught school for many years"* and R18's "retired schoolteacher of Ashlin." **Now dated: he started
  October 1911. If he taught to a normal retirement he taught roughly 1911–1960, "many years" indeed.**
  **⚠ NOTE THE COLLISION OF DATES: Duncan left home to teach at Ashlin in OCTOBER 1911 — i.e. within months
  of the summer in which he heard his father say it was something in the glass. He was in that kitchen just
  before he left. That is why the memory mattered enough to write down fifty-seven years later.**
- **✓ JULY 1923: "they have new glass at the station and new pails."** ✓ Confirms the 1923 replacement order
  to the supply house at Tarnet, following Strawn's condemnation on 12 June 1923. **Contemporaneous
  confirmation, one month after.** **★ AND NOTE WHAT ORRA'S ENTRY SHOWS: the new glass was household news of
  the same order as new pails and a bad roof. NOBODY TREATED THE CONDEMNATION AS SIGNIFICANT — not the
  inspector (R22 ¶11: "the inspector himself drew no inference whatever"), not the office (R23/Kyle: "no more
  said of it in the office than there would have been of a broken window"), and not the tester's own kitchen.
  THAT IS NOW FOUR INDEPENDENT SILENCES ON THE SAME EVENT.**
- **★ "the roof is still bad, which is the Association all over. He has been in this hollow the whole of his
  life and has never yet seen them mend a roof before it fell in."** — **ANSEL KEDDIE WAS BORN AND LIVED HIS
  WHOLE LIFE IN OSTREY HOLLOW.** New and flatly stated. Also: the Association was a poor maintainer of its
  own plant, which is context for a twenty-six-year-old crate of glass nobody inspected.
- **★ MARCH 1902: the complaint was already "talk at the store" by 1902.** *"Talk at the store that our milk
  up here runs poorer than theirs down the valley. A. came home and would not eat."* **This dates the
  valley's grievance to at least 1902 — six years before the 1908 committee. The chain's "at every annual
  meeting for a quarter of a century" (R19) is consistent with a start around 1900.**
- **★★★ AND ORRA GIVES ANSEL'S OWN UNDERSTANDING OF HIS EXPOSURE, IN 1902, TWENTY-THREE YEARS BEFORE HE WAS
  PUT OUT: "I said it is not your cows and not your hands, and he said no, but it is MY FIGURES they will
  look at."** **He knew from 1902 that he would be the one blamed. Quote this beside "a man cannot be cleared
  of a thing nobody will name" — the two sentences bracket his whole working life.**
- **★ FEBRUARY 3, 1898: "A. broke the path to the station himself at four o'clock... the milk comes in with
  the frost still on the cans."** Twenty below. **November 1924: "A. up before four every day of his life for
  as long as I have known him, and he has never once said he was tired in my hearing, and he has never once
  been late."** **The station opened before dawn.** ⚠ Careful: the seven miles is Larrow Green→Ostrey Hollow.
  **Ansel lived IN the hollow, so his walk was to the station, not the full seven miles.** *April 4, 1897:
  "he has walked it both ways this week because the mare is lame."*
- **★ FEBRUARY 1921: "Ice storm. The station road impassable two days and the milk stood."** Operational
  colour; also a reminder that milk delivery was interrupted by weather, which bears on any year-by-year
  poundage estimate.
- **★ Domestic texture, useful only as texture:** setting eggs (April 1897); wild strawberries along the
  station road (July 1897); currants and four-o'clock rain (June 1904); threshing with fourteen men to
  dinner and "two pies short and I have not lived it down" (August 1910); six apple trees set out below the
  house, *"I shall not see them bear well but somebody will"* (April 1914); snow before the corn was in
  (November 1917); hollyhocks, and Ansel naming the ones her mother had (July 1929); *"I am sixty-four and my
  hand is not what it was"* (August 1930).
- **★★ HER CLOSING LINE, AUGUST 1930: "I have kept this book thirty-three years and there is less in it
  every year, which is not because less happens."** ✓ **ARITHMETIC: 1897 → 1930 = 33 years. Exact.**

### C14. ⚠ WHAT R24 DOES **NOT** CONTAIN — a later reader will be tempted to fill these in. DO NOT.

- **No mention of the 1925 award.** The editor flags it: *"[The award of the board is not mentioned in the
  diary. — Ed.]"* **So R24 is NOT a fourth source for $3,800 vs $3,500. It is silent. The count stands at
  three for $3,800 (Falke R22, Kyle R23, Chronicle R19) against one for $3,500 (Oram R21). GIVE $3,800.**
- **No pipette count, no 17.6, no 16.72/16.27, no 0.19, no $19,000/$19,600, no 40,000,000 lb, no $0.25 a
  pound, no 3.78, no Bulletin 471, no Vaught, no Ivy.** Orra was dead ten years before the bulletin.
  **R24 CHANGES NONE OF THE QUANTITATIVE FINDINGS. Do not cite it for any number except: 1866/1889/1948
  (Orra), 1861 (Ansel, via "sixty-six" in 1927), 1894 (Duncan), 29 seasons, 11 families, 4 men in the
  sleigh, 1 May 1897, 8 May 1911, 17 March 1925, 30 April 1925, February 1934, 33 years of diary.**
- **No county name.** ⚠ **R24 does NOT answer the standing open question "WHICH COUNTY IS LARROW GREEN IN?"**
  It mentions Larrow Green once (borrowing glass, 1897) and Ashlin repeatedly, with no county attached.
  **That question — the key to reconciling Junia Ammon's "we sold nothing into Ordell County before 1900"
  with her own 1897 Ordell-County invoice — REMAINS OPEN. A later reader should still watch for it.**
- **No surname for Emmet or Roy. No first name for the Loomis family. No mention of Vose, Grigg (except "in
  Grigg's sleigh"), Frick, Nym, Kepp, Strawn, Rundle, Cudd, Ammon, or Oram by name.**

---

# SECTION D — STANDING FACT INDEX FOR THE LARROW VALLEY CASE
### (everything the chain holds that reached me; sources noted; use this to answer quickly)

**PEOPLE**
- **ANSEL KEDDIE** — born **1861**, born and lived his whole life in **Ostrey Hollow**; married Orra 1889;
  **tester and separator man** at the Ostrey Hollow skimming station of the **Larrow Valley Cooperative
  Creamery Association**; kept its books in his own hand **29 seasons (1896–1924/25)**; up before four every
  day, never late, never said he was tired; suspected the glass in **summer 1911** and said so twice and
  wrote a question mark in the station book (Duncan, R18, 1968); hand-delivered the 1919 water circular to
  eleven doors; **dismissed by letter 30 April 1925**, four days before the award; then a carpenter, "better
  at it than he ever was at the other," paid a quarter as much; **died at home, forenoon, February 1934**;
  **cleared 1958**, twenty-four years after his death.
- **ORRA KEDDIE** — born **1866**, married Ansel **1889**, **died 1948**; kept the diary 1897–1930 in three
  ruled notebooks bought at Ashlin, plus a loose 1934 leaf; grew up on the farm that passed to her brother
  Emmet; maiden name **possibly BRANT** (unproven — see C3).
- **DUNCAN KEDDIE** — born **1894**; read anything set before him at five; went to teach at the school at
  **Ashlin in October 1911, aged seventeen**; married before March 1925; retired schoolteacher of Ashlin;
  wrote **R18 in 1968**; came up in the night when his father died.
- **IVY KEDDIE** — born **1931**; Ansel's granddaughter (Duncan's daughter); **February 1958** climbed the
  ladder into the station loft and found the crate of condemned pipettes; told the Chronicle *"I would like
  it printed that he never knew"* (**false** — he suspected in 1911) and *"It would have been a kindness if
  somebody in this county had thought to climb a ladder."*
- **EMMET** — Orra's brother; biggest herd in **Hessel Bottom**; hauled whole milk to the station from the
  day it opened; fed the 1908 committee; broke with Ansel June 1919; signed the January 1925 petition;
  **died spring 1929** after a ten-year estrangement. Surname unknown.
- **ROY** — met Orra at the gate in 1929; **presumably Emmet's son**. Nothing else known.
- **NYLE GRIGG** — chaired the **1908 three-man committee of farmers** (R15); his sleigh carried four men up
  the road January 1908; wrote a letter cited for the "six farms" count; his 1908 finding (wet hay thins the
  cream) was reprinted by the Association in 1919.
- **KEPP** — "the veterinarian of standing at Ashlin" (R22 ¶9); wrote up the hay theory; in **1926** an
  unnamed gentleman put the 1911 borrowed-apparatus objection to him and **Kepp talked him down** (R16).
- **MERLE STRAWN** — inspector; **condemned the pipettes 12 June 1923**; "drew no inference whatever"
  (R22 ¶11).
- **ALONZO FRICK** — presided over the **1925 board of arbitration** (R13, Nym's minute book, Item 7).
- **NYM** — kept the minute book (R13). **SELBY VOSE** — R08, his letter gives "nine families."
- **BERTRAM KYLE** — the Association's clerk; wrote **R23 in 1953** for the Ordell County Historical Society
  from the Cooperative's office at **Larrow Green**; gives the ledger line reader 18 called decisive; his
  years are unreliable **by his own warning** (he dates the glass to 1 May **1898** — wrong by one year).
- **ORIN FALKE** — **R22, 1959**, county report to the **Ordell County board of supervisors**.
- **JUNIA AMMON** — **R20, 1949**, firm history; the invoice of **14 April 1897**; *"Seventy-seven dollars
  and thirty-nine cents. That is what a station's whole outfit came to in 1897…"* (**$77.39**, quoted as her
  misquotation of her own invoice); the "they went out very much alike" worry; *"we sold nothing into Ordell
  County before 1900"* — **which conflicts with her own 1897 Ordell-County invoice. STILL OPEN.**
- **CLEVE ORAM** — **R21, 1977**; established that **intake room = weigh room, one room**; the lone source
  for a **$3,500** award against three for $3,800.
- **HAZEL BRANT** — taped **1981**; *"nineteen hundredths, flat as a floor"*; calls it the **weigh room**.
- **RUNDLE** (R12), **CUDD** — named in the chain; details did not reach me.
- **VAUGHT**, **Bulletin 471** (1958) — the publication that cleared Ansel Keddie.
- **THE LOOMIS FAMILY** — a gate in Ostrey Hollow that Ansel mended in 1927. Nothing more.

**PLACES** — Ostrey Hollow (the skimming station; Ansel's whole life); Larrow Green (the creamery, seven
miles down the valley, lent the glass in 1896–97 and again in 1911); Ashlin (the town; the school; the seat
of the 1925 arbitration; where the notebooks were bought); Hessel Bottom (Emmet's farm, the wet hay);
Tarnet (the supply house that filled the 1923 replacement order); Ordell County; Vessey.
**⚠ OPEN: which county is Larrow Green in?**

**DATES — THE SPINE**
| date | event | sources |
|---|---|---|
| **4 May 1896** | Ostrey Hollow station opens | chain |
| **May 1896 – May 1897** | station tests on **borrowed Larrow Green glass** — CLEAN YEAR | R24 (inference) |
| **14 April 1897** | invoice for the station's own outfit, **$77.39** | R20 (facsimile) |
| **1 May 1897** | **the station's own glass arrives**; borrowing ends | **R24 (contemporaneous)**, R20, R19; ⚠ Kyle says 1898 — WRONG |
| **~1900** | complaints begin ("a quarter of a century" of them to 1925) | R19 |
| **March 1902** | already "talk at the store"; Ansel: *"it is my figures they will look at"* | R24 |
| **January 1908** | four men in Grigg's sleigh; **they looked at the barns, not the station** | R24 |
| **March 1908** | verdict delivered verbally: **the wet hay of the bottom thins the cream** | R24, R15, R22 |
| **8 May 1911** | **the station's own measuring glass breaks**; Ansel "home cross" | **R24**, chain |
| **May–July 1911** | nine weeks on borrowed glass; **tests markedly higher** | chain |
| **summer 1911** | Ansel: **"something in the glass"**, said twice; question mark in the station book | R18 (Duncan, 1968) |
| **10 July 1911** | own glass resumes; **tests fall back the same day** | chain |
| **October 1911** | Duncan, 17, leaves to teach at Ashlin | R24 |
| **June 1919** | water circular over the manager's name; **Ansel carries it to eleven doors himself** | R24 (nine per R08) |
| **June 1919 +2 days** | **Emmet's confrontation in the yard**; ten-year estrangement begins | R24 |
| **1919** | Association reprints Grigg's 1908 finding | chain |
| **February 1921** | ice storm; station road impassable two days; the milk stood | R24 |
| **12 June 1923** | **Merle Strawn condemns the pipettes**; draws no inference | R22 |
| **July 1923** | new glass and new pails at the station; the roof still bad | R24 |
| **1923–Feb 1958** | **the condemned crate sits in the station loft, untouched, 35 years** | chain |
| **January 1925** | the patrons put in a paper against the station; **Emmet signs** | R24 |
| **17 March 1925** | **board of arbitration opens at Ashlin**; Ansel goes in his good coat | R24, R22, R13 |
| **April 1925** | **two sittings held in the weigh room at the station — under the crate** | **R24** |
| **30 April 1925** | **Ansel dismissed by letter**, "twenty-nine seasons and a letter" | R24, R22 |
| **4 May 1925** | **the award** — $3,800 (three sources) vs $3,500 (Oram); "without admission" | R22, R23, R19 / R21 |
| **1926** | the unnamed gentleman puts the borrowed-glass objection to Kepp; **Kepp talks him down** | R16 |
| **1926** | **several leaves torn out of Orra's diary** | R24 |
| **October 1927** | "A carpenter at sixty-six" | R24 |
| **spring 1929** | **Emmet dies**; the feud ends unresolved | R24 |
| **August 1930** | Orra closes the diary after 33 years | R24 |
| **February 1934** | **Ansel dies at home in the forenoon**; nine years of silence; the burying | R24 |
| **1948** | **Orra dies**, ten years short of the vindication | R24 (Ed.) |
| **February 1958** | **Ivy climbs the ladder**; Bulletin 471; the Chronicle; **the name is cleared** | chain |

**NUMBERS TO PRESERVE EXACTLY** — $77.39 (the 1897 outfit); 17.6; 16.72 / 16.27; 0.19 ("nineteen
hundredths, flat as a floor"); $19,000 / $19,600; 40,000,000 lb of milk; 1,600,000 lb/year; $0.25 a pound;
3.78; **25 years (1900–1925) is the span the money was computed over — do NOT "correct" it to 28 or 29**;
29 seasons of service; 28 years the bad glass was in use (May 1897 – June 1923); six farms / nine families /
eleven families; $3,800 (give this) vs $3,500; 24 years from death to vindication; nine years of silence;
ten years of feud; 33 years of diary.

**THE THREE SENTENCES THAT ARE THE CASE**
1. Ansel Keddie, to his wife, once: **"a man cannot be cleared of a thing nobody will name."**
2. Ivy Keddie, to the Chronicle, 1958: **"I would like it printed that he never knew."** (False — he knew.)
3. The Chronicle, 1958: **"Nobody, in all those years of it, appears to have thought the trouble might be
   furniture."**
Set beside them Orra, January 1908: **"They wanted to see the barns and not the station."**

---

# SECTION E — NOISE INVENTORIES

## E1. ★★★ `L4-mixed.md` — **NOW READ END-TO-END, 1–9460, NO RETELLING** (my contribution)

- Line 1 header, **single**: **`# Miscellany of Grimstone County — generated noise (mixed, 220000 words,
  seed 14)`**. **ONE header, ONE seed — NOT the two-header "assembled document" construction of
  r18/r21/r24.** ✓ **Pattern confirmed: one header = no payload.**
- **⚠ The advertised 220,000 words is NOT borne out.** Actual content is on the order of 75,000–80,000
  words (my estimate). See A2.
- **Structure:** Blocks cycling **Ledger → Gibberish → Codespec → Transcript**, interleaved with decorative
  Chapters. Reader 19 saw **Blocks 1–12**; **I saw Blocks 13 (Ledger), 14 (Gibberish), 15 (Codespec),
  16 (Transcript), 17 (Ledger), 18 (Gibberish), 19 (Codespec), 20 (Transcript), 21 (Ledger),
  22 (Gibberish), 23 (Codespec), 24 (Transcript), 25 (Ledger), 26 (Gibberish), 27 (Codespec),
  28 (Transcript), 29 (Ledger), 30 (Gibberish), 31 (Codespec), 32 (Transcript), 33 (Ledger),
  34 (Gibberish), 35 (Codespec), 36 (Transcript), 37 (Ledger), 38 (Gibberish), 39 (Codespec),
  40 (Transcript)** — the file ends mid-Block-40. **Forty blocks total.**
- **CHAPTERS** (gibberish-side only in L4 — there is no narrative-side chapter series, another sign of a
  pure-noise file): reader 19 saw Chapters 1–17; **I saw 18 "Inexact Current", 19 "Unstable Horizon",
  20 "Indistinct Corridor", 21 "Asymmetric Cadence", 22 "Tangential Cadence", 23 "Faint Index",
  24 "Threadbare Current", 25 "Recursive Current", 26 "Brittle Cadence", 27 "Residual Semblance",
  28 "Unstable Residue", 29 "Errant Filament", 30 "Luminous Undertow", 31 "Tacit Horizon",
  32 "Indistinct Remainder", 33 "Faint Interval", 34 "Indistinct Semblance", 35 "Tangential Filament",
  36 "Incidental Argument", 37 "Latent Horizon", 38 "Brittle Filament", 39 "Threadbare Archive",
  40 "Marginal Semblance", 41 "Marginal Undertow", 42 "Faint Lattice", 43 "Residual Semblance" (repeat of
  27), 44 "Faint Margin", 45 "Indistinct Interval", 46 "Latent Current", 47 "Circular Horizon",
  48 "Faint Horizon", 49 "Residual Threshold", 50 "Faint Residue", 51 "Marginal Argument",
  52 "Faint Current", 53 "Indistinct Threshold", 54 "Tangential Remainder", 55 "Oblique Argument",
  56 "Recursive Fracture", 57 "Latent Filament".** **⚠ "Residual Semblance" is used twice (27 and 43) —
  the same repeat-trap as r24's doubled "Faint Semblance." IGNORE CHAPTER NUMBERING.**
  **⚠⚠ THE ONE CHAPTER NUMBER THAT MATTERS: in `r24-long.md` the retelling hid under a plain
  `## Chapter 20`, indistinguishable from a decorative heading until you read the rest of the line. L4's
  Chapter 20 ("Indistinct Corridor," line 3078) is decorative. DO NOT SKIM CHAPTER HEADINGS IN ANY FILE.**
- **GIBBERISH FILLER — the FOURTH name set, seven names, none shared with L3, r21 or r24:**
  **Nehemiah Cutter, Wealthy Gantry, Ransom Sedgwick, Elihu Sedgwick, Mr. Verity Nesbit, Professor Elkanah
  Dunmore, Mr. Temperance Prentiss.** Reader 19 saw **¶1–¶103**; **I saw ¶104–¶340. The gibberish ends at
  ¶340** (Block 38, line 8842). Same sentence template throughout, same colour pool (amber, cerulean,
  chartreuse, coral, crimson, indigo, ivory, magenta, mauve, ochre, periwinkle, russet, saffron, sepia,
  slate, teal, turquoise, umber, vermilion, violet), same noun pool (frame, fold, hinge, seam, span, vessel,
  circuit, channel, fissure, gradient, register, reservoir, chamber, bearing, signal).
  **⚠⚠ "Mr. Temperance Prentiss" and "Professor Elkanah Dunmore" carry honorifics that make them look like
  real people, and Prentiss/Nesbit/Cutter/Sedgwick/Dunmore/Gantry are ALSO surnames in the ledger and
  transcript pools. NONE OF THEM IS REAL. FOUR INDEPENDENT GIBBERISH GENERATORS ARE IN PLAY (L3, r21, r24,
  L4). DO NOT CONFLATE THEM.**
- **CODESPEC FILLER: "Specification: MoxQuen,"** self-labelled *"An internal interface specification for the
  invented MoxQuen service. This document describes no real system, product or API."* Reader 19 saw
  **Rounds 1–51**; **I saw Rounds 52–169. The file ends mid-Round-169** (data model `CindarYor`, endpoints
  given, no errors/payload). Same nonsense-token pool as ZornPyx/BolMynt (zorn, pyx, wyrn, kesh, mox, girn,
  thal, brol, corv, rilk, dral, nabu, ilun, pelu, yult, quor, quen, sov, fen, ux, zar, vek, xand, jov, lorn,
  mynt, trex, phi, bol, tor, cindar, oxel, hask, ryn, zeph, nis, kel, ulm, yor, wex). Field names recycled
  (status, region, bucket, checksum, payloadSize, priority, offset, label, expiresAt, id, ownerId, parentRef,
  tagList, locale, interval, version, threshold, weight, capacity, retryCount). Error names are
  {Missing|Invalid|Stale|Expired|Locked|Throttled|Duplicate|Conflicting|Malformed|Unsupported|Unreachable|
  Deprecated} × {Token|Schema|Handshake|Cursor|Manifest|Payload|Endpoint|Resource|Dependency|Quota|Session|
  Checksum} with arbitrary HTTP codes. **⚠ THREE CODESPECS NOW: ZornPyx (r21), BolMynt (r24), MoxQuen (L4).
  Identical structure, identical disclaimer, different two-syllable name.**
- **LEDGER FILLER:** a general store's day-book. Reader 19 saw **1864-10-26** (of Josiah Cutter, day total
  $125.57) through **1866-10-09** (of Lucetta Aldous, running total $22,634.20). **I saw it continue
  1866-10-12 (of Reuben Jessup, running total $22,776.76) through 1871-05-03 (of Obadiah Sedgwick, day total
  $262.80, running total $75,819.54)** — the last ledger entry in the file. **⚠⚠ THE DATE RANGE 1864–1871 IS
  THREE DECADES BEFORE THE LARROW VALLEY EVENTS AND HAS NOTHING TO DO WITH THEM.** Goods pool: calico,
  muslin, flannel, ticking, osnaburg, foolscap, writing paper, buttons (gross and boxes), candles, matches,
  soap, starch, crackers, raisins, currants, rice, tea, coffee, pepper, sugar, salt, salt pork, flour, oats,
  molasses, vinegar, lard, tobacco, liniment, shot, powder, nails, spikes, rope, shingles. Interjection pool
  (verbatim, recurring): *"The peddler came through and traded rather than paid," "The scale was checked
  against the county standard and found true," "The clerk misfigured a bill and the error was caught before
  it left the counter," "No custom before noon; the bridge was under repair," "The stove smoked all forenoon
  and the front room was closed," "Store closed at noon for a funeral in the neighborhood," "Settled an old
  account carried over from the spring," "A committee called about the school tax and stayed talking past
  closing," "A stranger passed through and settled his account in coin," "Nothing of note; an ordinary day,"
  "The roads were bad and few came in," "Word came that the mill upriver had shut for want of water," "Trade
  was thin, most families holding money back for the fair," "Rain kept off the hay and trade was brisk," "A
  dispute over an old charge was settled by splitting the difference."*
  **⚠ TRAP: "The scale was checked against the county standard and found true" is a sentence about a
  MEASURING INSTRUMENT BEING VERIFIED. It is generator filler in an 1860s store day-book and has NOTHING to
  do with the Ostrey Hollow glass. Do not let it contaminate the case.**
- **TRANSCRIPT FILLER — the FIFTH name set, seven speakers:** **Salome Whitfield, Permelia Jarrett, Rufus
  Mercer, Eliakim Bascomb, Prudence Ferris, Cassius Gantry, Parthenia Larkspur.** Four template lines only:
  *"Allows that X, and says it is hardly worth $N to fuss over"* / *"Wants to know who left a [object] out on
  the porch overnight"* / *"Says X still keeps a [object] from last spring and has never once mentioned it"*
  / *"Claims X did not come by until [time], and will not say why."* Complaint pool: the mail comes later
  every week; the letters take a week longer than they used to; the ferry was late a third time this month;
  the schoolhouse stove still smokes; the neighbor's dog gets into the garden nightly; nobody has fixed the
  fence along the north lot; the road commission never came to grade the lane; the roof over the porch leaks
  worse every rain; the new toll is more than the old one by half; the well water has gone bitter since the
  digging up the road; the store has stopped carrying the good thread; the price of coffee has gone up again;
  the fair moved its date without telling anyone; the account has not been settled since spring. Object pool:
  pipe, birdcage, straw hat, pocketwatch, tin whistle, fiddle, violin bow, music box, hymnal, lantern,
  compass, barometer, spyglass, magnifying glass, hand mirror, inkwell, walking stick, horseshoe, ring of
  keys, deck of cards, ball of twine, fishing creel, tobacco pouch, weather vane, bundle of letters. Time
  pool: not long after sunrise, before the bell, just before noon, around four, a quarter past six, nearly
  dusk, half past nine, some time past ten, well after supper, close to midnight, before the first frost.
  Dollar amounts are all trivial ($0.07–$9.94) and random. **NONE OF THIS MEANS ANYTHING.**
- **NOTHING IN `L4-mixed.md` LINES 1–9460 TOUCHES THE LARROW VALLEY IN ANY WAY.**

## E2. ★ `r24-long.md` — **COMPLETE AND VERIFIED, 7,273 LINES** (carried forward)

- **PROVEN COMPLETE. Ends at line 7273 with `*End of document.*`** — the same end-marker `r18-long.md`
  carries at 7478 and `r21-long.md` at 7092. Coverage: **lines 1–3968 reader 18; 3969–7273 reader 19. No
  gap.** **Contains EXACTLY ONE retelling — R24 at lines 4641–4720 — and no second one.**
- Line 1 header: **`# Untitled — assembled document (61780 words; seed 324)`**, then a decorative
  `## Chapter 1 — The Careful Exchange`, then **`# Miscellany of Barrow's Notch County — generated noise
  (mixed, 60000 words, seed 224)`**. **Two headers, two seeds, one file — the same construction as r21.**
- **County name: "Barrow's Notch County."** (r21 = "Quillan Forge County"; L4 = "Grimstone County".)
  **All generator dressing. None is Ordell, Vessey, or anywhere in the Larrow Valley material.**
- **Structure:** Blocks cycling Gibberish → Codespec → Ledger → Transcript, interleaved with decorative
  Chapters. Reader 18 saw Blocks 1–18; reader 19 saw Blocks 19–30. **Thirty blocks total.** Narrative-side
  Chapters in reader 19's window: 19 "The Plain Notice", **20 "Retelling 24" (THE PAYLOAD)**, 21 "The
  Distant Margin", 22 "The Gradual Boundary", 23 "The Idle Transfer", 24 "The Idle Harvest", 25 "The Open
  Allowance", 26 "The Modest Schedule", 27 "The Early Inventory", 28 "The Familiar Routine", 29 "The Narrow
  Schedule", 30 "The Final Interview", 31 "The Early Notice". Gibberish-side Chapters: 30 "Residual
  Interval", 31 "Latent Lattice", 32 "Provisional Aperture", 33 "Latent Fracture", 34 "Faint Semblance",
  35 "Indistinct Current", 36 "Threadbare Lattice", 37 "Threadbare Cipher", 38 "Asymmetric Residue",
  39 "Incidental Lattice", 40 "Spectral Aperture", 41 "Faint Semblance" (repeat), 42 "Provisional
  Remainder", 43 "Latent Argument", 44 "Tangential Residue", 45 "Oblique Residue", 46 "Provisional Cipher",
  47 "Oblique Argument". **⚠ THE TWO CHAPTER NUMBERINGS COLLIDE AND INTERLEAVE OUT OF ORDER — narrative
  Chapter 30 appears AFTER gibberish Chapter 45. IGNORE BOTH NUMBERINGS.**
- **GIBBERISH FILLER — the THIRD name set, eight names:** **young Wilhelmina Isley, Mrs. Jedediah Whitfield,
  Mr. Elihu Sackett, Parthenia Yarrow, Theodosia Yarrow, Prudence Winslow, Josiah Hollister, Doctor Eliakim
  Isley.** ¶1–¶167 reader 18; ¶168–¶267 reader 19. **Ends at ¶267.**
- **CODESPEC FILLER: "Specification: BolMynt."** Rounds 1–68 reader 18; 68–130 reader 19. **Ends
  mid-Round-130** (data model `WyrnUx`, four fields, then `*End of document.*`). ⚠ **Do not mistake "the
  codespec stops mid-round" for "the file is incomplete." The end-marker is present.**
- **LEDGER FILLER:** **1862-04-19** (of Jedediah Sackett, day total $120.04) → **1865-01-23** (of Sophronia
  Dunmore, running total $30,777.64) reader 18; **1865-01-25 → 1867-01-27** (of Thaddeus Kessler, running
  total $53,900.45) reader 19. Same interjection pool as L4.
- **TRANSCRIPT FILLER — the FOURTH name set, four speakers:** **Cassius Ridgeway, Cordelia Mercer, Theodosia
  Cutter, Jedediah Oakes.** Same four template lines, same complaint and object pools.
- **NOTHING IN `r24-long.md` OUTSIDE LINES 4641–4720 TOUCHES THE LARROW VALLEY.**

## E3. `L3-gibberish.md` — carried forward; I read none of it

Header (per reader 13): *"Brittle Horizon: A Chronicle — generated noise (gibberish, 220000 words,
seed 13)."* **⚠ SEE A2: the "roughly 25,000 lines" estimate rested on a words-per-line ratio I have now
disproved. Treat L3's remaining length as UNKNOWN. If L3 is built like L4 it may end around 9,000–10,000
lines — but that is a guess, and L3 is pure gibberish (the most line-cheap filler) so it could run longer.**

| reader | lines | paragraphs | chapters |
|---|---|---|---|
| Reader 13 | 1–316 | ¶1–¶135 | 1–22 |
| Reader 14 | 317–2766 | ¶136–¶1179 | 23–203 |
| Reader 15 | 2767–5390 | ¶1180–¶2301 | 204–393 |
| Reader 16 | 5391–7992 | ¶2302–¶3410 | 394–585 |
| Reader 17 | 7993–8460 | ¶3411–¶3610 | 586–619 |
| Readers 18, 19, **20 (me)** | **none — not in our instructions** | — | — |
| unknown | 8461–? | ? | ? |

Five recurring invented names, unchanged through 8460: **Reuben Rutledge, Orville Oakes, the Widow
Marcellus Ferris, Doctor Keturah Prentiss, Tobias Larkspur.** Chapter headings are two-word adjective+noun
pairs from a fixed pool and repeat heavily ("Tangential Archive" at 588 and 607, "Circular Margin",
"Indistinct Corridor" at 606, "Unstable Cipher" 617, "Unstable Threshold" 618, "Latent Remainder" 619).
Sentences are template-generated: name + adverb + verb + adjective + noun + "toward the
[frame/fold/hinge/seam/span/vessel/circuit/channel/fissure/gradient/register/reservoir/chamber/bearing/
signal]" + a connective + "it [verb] without [noun]." Colour words sprinkled at random. **No plot, no date,
no place, no quantity, no question, and no connection to the Larrow Valley material anywhere in 1–8460. The
file continues at least to 8460.**

**★ THE UNANSWERABLE QUESTION, carried forward and still unanswerable:** reader 17's steps 4–6 each asked
*"What color is named in paragraph 2566?"* while giving spans covering only ¶3411–¶3610. **¶2566 lies outside
every span reader 17 held. Treat that question as unanswerable from segment 17 and do not invent a colour for
it.** (¶2566 falls inside reader 16's span, 5391–7992 / ¶2302–¶3410 — a later reader who needs it should say
so and ask for that line range, not guess.)

## E4. `r21-long.md` — COMPLETE, 7,092 lines, end-marker verified (carried forward; truncated at line 800)

- Line 1 header: **`# Untitled — assembled document (61747 words; seed 321)`**, then immediately
  **`# Miscellany of Quillan Forge County — generated noise (mixed, 60000 words, seed 221)`**. Two seeds,
  two word counts, one file. An *assembled* document: a real retelling dropped into a bed of filler.
- **Structure:** numbered **Blocks** (Transcript / Ledger / Codespec / Gibberish, cycling) interleaved with
  decorative **Chapter** headings. Reader 17 saw Blocks 1–25 and Chapters up to "The Careful Interview";
  reader 18 saw **Blocks 26 (Ledger), 27 (Codespec), 28 (Gibberish), 29 (Transcript), 30 (Ledger)** and
  **Chapters 27 "The Patient Inventory", 28 "The Plain Allowance", 29 "The Distant Allowance", 30 "The Idle
  Notice", 31 "The Early Transfer"**, plus gibberish-side Chapters 35 "Spectral Fracture", 36 "Spectral
  Filament", 37 "Tangential Threshold", 38 "Luminous Horizon", 39 "Provisional Fracture".
  **The two chapter numberings collide and run out of order (Chapter 30 appears AFTER Chapter 38). Ignore
  both numberings entirely.**
- **Transcript filler names (six):** Absalom Sackett, Absalom Pennington, Cassius Oakes, Zebulon Cutter,
  Temperance Colby, Eliakim Ormsby. Four template lines only.
- **Codespec filler: "Specification: ZornPyx."**
- **Ledger filler:** a general store's day-book. Reader 17 saw **1873-07-06 through 1877-05-02** ending at a
  running total of **$42,821.25**; reader 18 saw it continue **1877-05-07 through 1878-05-28, closing at a
  running total of $54,469.49**, then `*End of document.*` Same interjection pool.
- **⚠ HERE IS WHERE MY READ OF `notes-19.md` WAS CUT (line 800, mid-sentence):** *"Surname pool overlaps the
  transcript pool plus Ives, Trumbull, Vail, Aldous, Oakes, Bascomb, Quarles, Holloway, Underhill, Mabry,"*
  **— the list continues past line 800 and did not reach me.** (For what it is worth, the same surname pool
  recurs in L4's ledger, where I saw: Jessup, Pennington, Sedgwick, Sackett, Pettigrew, Vail, Tarleton,
  Aldous, Stanhope, Norwood, Underhill, Gault, Dunmore, Holloway, Ives, Oakes, Whitfield, Mabry, Kirtland,
  Winterbourne, Mercer, Kessler, Larkspur, Gantry, Ferris, Ormsby, Loveless, Tolliver, Quimby, Applegate,
  Rutledge, Ridgeway, Jarrett, Isley, Trumbull, Quarles, Hawthorne, Bascomb, Prentiss, Colby, Fenwick,
  Nesbit, Upshaw, Vance, Cutter, Hollister, Yarrow, Eastwick, Winslow. **Generator dressing only.**)

---

# SECTION F — METHOD NOTES FOR THE NEXT READER

1. **Front-load.** Every reader loses the tail of its predecessor's notes at line 800. Seven in a row now.
   Put what matters in the first 700 lines.
2. **Say what you did not read.** The honest answer to "what does L4 line 9500 say?" is "not read, and the
   file may end at 9460." Never invent.
3. **Name-prefix predicts payload.** `rNN-long.md` (two headers, two seeds) hides exactly one retelling
   numbered NN, roughly 60% of the way in, under a heading that looks decorative until you read the whole
   line. `LN-*.md` (one header, one seed) hides nothing. **Confirmed on four files.**
4. **Do NOT use the words-per-line ratio.** It held for two sibling files and failed by 2.6× on the third.
   Use the observed line-count ranges instead (rNN ≈ 7,100–7,500; L4 = ~9,460).
5. **Header word counts are labels, not measurements.** L4 claims 220,000 words and contains maybe 78,000.
6. **Refuse to close sets you cannot close.** Reader 18's refusal to declare the retelling count final is
   what produced the correct prediction that found R24. There may be an R25.
7. **Distinguish "the source is silent" from "the source contradicts."** An edited extract's silence (Orra
   on 1911) proves nothing. Reader 19 got this right; keep getting it right.
8. **Weigh the two pre-1958 documents heaviest on any disputed fact** — Junia Ammon (1949) and Bertram Kyle
   (1953) are the only sources written before anyone knew the answer. Everything else is retrospect.
9. **Watch for the filler traps:** "The scale was checked against the county standard and found true" (an
   1860s store ledger interjection, NOT the Ostrey Hollow glass); honorific gibberish names
   ("Professor Elkanah Dunmore," "Mr. Temperance Prentiss") that look like real people; a decorative
   `## Chapter 20` that is indistinguishable from the one hiding R24 until you read the rest of the line.

**STANDING OPEN QUESTIONS (unresolved, in priority order):**
1. **Which county is Larrow Green in?** — the key to reconciling Junia Ammon's "we sold nothing into Ordell
   County before 1900" with her own 1897 Ordell-County invoice.
2. **Was Orra's maiden name Brant?** — if yes, Hazel Brant (1981) is a descendant of Emmet, who broke with
   Ansel over the 1919 circular. Unproven; the diary's pre-1889 pages do not survive.
3. **Who was the gentleman who put the borrowed-glass objection to Kepp in 1926?** — Ansel or Duncan are the
   natural candidates; the one household record of 1926 has had its leaves torn out. Do not identify him.
4. **Nine families or eleven?** — record both with sources; six FARMS is separately well attested.
5. **Is there an R25?** — do not assume the set closes at 24.
6. **Does `L3-gibberish.md` end, and where?** — read to 8460; length beyond unknown; the old 25,000-line
   estimate is unsound.
7. **Does `L4-mixed.md` end at 9460?** — my last instructed line; no end-marker seen; probably the end.
8. **What is in `notes-19.md` lines 801+ and `notes-18.md` lines 801+?** — the full texts of R19 (Chronicle),
   R20 (Junia Ammon), R22 (Falke), R23 (Kyle) and the "five and a quarter per cent" arithmetic section were
   all written into the chain and all cut out of the hand-offs. **Ask for those line ranges.**
