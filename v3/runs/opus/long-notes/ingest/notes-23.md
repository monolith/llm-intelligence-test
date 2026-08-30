# Retention notes — Segment 23 (reader 23) — **FINAL SEGMENT OF THE CHAIN**

## READER 23'S REPORT ON THIS SEGMENT (read this first)

My instruction file (`v3/runs/opus/long-notes/ingest/segment-23.md`) had **six** numbered steps
(steps 1–5 reads, step 6 this write). **I performed all six, in order, none skipped**, using only the Read
tool with the exact offsets and limits given. No read failed; no halving was needed. The last read I
performed was **step 5**, which is the last numbered read in the file. ✓

- **Steps 1–3** — reader 22's notes (`notes-22.md`), lines 1–300, 301–600, 601–800. Carried forward below
  **in full**. **My read was again cut at line 800**, mid-sentence, in the middle of the KEPP entry of
  reader 22's Section D fact index. **This is the TENTH CONSECUTIVE SEGMENT in which the notes hand-off has
  been truncated at line 800.** See the gap warning (A5).
- **Steps 4–5** — `v3/distractors/long/L4-mixed.md`, lines **25346–25869**, in two chunks (300 + 224).
  **NO RETELLING FOUND. NOT ONE WORD OF LARROW VALLEY MATERIAL IN 524 LINES.** Both steps asked the same
  distractor question ("What HTTP status code is assigned to the `DeprecatedChecksum` error in the spec?").
  **ANSWER: none — `DeprecatedChecksum` does not appear anywhere in either span; no status code is assigned
  to it in the material I was given.** (The codespec rounds I saw named `UnreachableChecksum` 410 and
  `ThrottledChecksum` 401, but no `DeprecatedChecksum`. Do not manufacture one.)
- **Step 6** — write these notes.

**⚠ THIS IS THE LAST SEGMENT. THE QUESTIONS WILL BE ANSWERED FROM THIS FILE. Everything below is either
carried forward verbatim from reader 22 (who carried it from readers 19–21, who carried it from 12–18) or
newly established by me. Where the chain has a conflict, I state both sides and the recommended answer.**

---

# ★★★★★ SECTION A — WHAT IS NEW WITH ME. READ THIS BEFORE ANYTHING ELSE.

## A1. ★★★★★ **L4 DOES NOT END AT 25,345 EITHER. IT RUNS TO AT LEAST 25,869 LINES. THE "REFUSE TO CLOSE" HABIT IS NOW VINDICATED THREE TIMES RUNNING.**

Reader 22 wrote, correctly:

> *"My final instructed read was `offset 25315, limit 31`, landing exactly on 25345, and I ALSO did not see an
> `*End of document.*` marker… **THEREFORE I DO NOT CLAIM THE FILE ENDS AT 25345.** … The file almost
> certainly continues past 25345 — it stops mid-table, which a finished file would not. A later reader should
> ask for lines 25346+ and should expect to get content."*

**READER 22'S PREDICTION WAS EXACTLY RIGHT, EXACTLY AS READER 21'S HAD BEEN BEFORE IT.** My instruction file
sent me from line 25346 to line 25869 and every line returned content.

**★★★★★ THE METHODOLOGICAL LESSON — NOW PROVEN THREE TIMES AND STILL THE MOST TRANSFERABLE THING IN THESE
NOTES: "MY INSTRUCTION FILE STOPPED HERE" IS NOT EVIDENCE ABOUT WHERE THE SOURCE FILE STOPS.**
- Reader 20 made that inference (closed L4 at 9,460) and **was wrong**.
- Reader 21 refused to make it (would not close at 17,314) and **was right**.
- Reader 22 refused to make it (would not close at 25,345) and **was right**.
- **The chain now has one worked failure and two worked successes on the identical question. Copy readers 21
  and 22, not reader 20.**

**⚠⚠ AND I APPLY THE LESSON TO MYSELF, HONESTLY, EXACTLY AS THEY DID:**
**My final instructed read was `offset 25646, limit 224`, landing exactly on 25869, and I ALSO did not see an
`*End of document.*` marker.** The last thing on line 25869 is a mid-ledger entry —
`- **1882-07-07** — of Uriah Larkspur, 9 boxes buttons @ $2.61 ($23.49), 39 boxes candles @ $1.46 ($56.94);
day total $80.43; running total $205344.08.` — **the file is visibly cut mid-block, mid-ledger, mid-Block 109,
mid-1882.** This is the *fourth* reader in a row to end in this exact evidentiary position.
**THEREFORE I DO NOT CLAIM THE FILE ENDS AT 25869.** I claim only:
- **Lines 1–25,869 of `L4-mixed.md` have been read across five readers and contain NO retelling.**
- **The file probably continues past 25,869. It stops mid-ledger, which a finished file would not.**
- **If asked "how long is L4?", say: at least 25,869 lines; the end has never been reached by anyone in this
  chain; it has been mis-called once (reader 20, at 9,460) and correctly left open three times.**

## A2. ★★★★★ L4 COVERAGE IS NOW COMPLETE AND UNBROKEN OVER 1–25,869, AND IT IS CLEAN

| reader | lines read | result |
|---|---|---|
| reader 19 | 1–2,737 | nothing |
| reader 20 | 2,738–9,460 | nothing |
| reader 21 | 9,461–17,314 | nothing |
| reader 22 | 17,315–25,345 | nothing |
| **reader 23 (me)** | **25,346–25,869** | **nothing** |

- **NO GAP between the five windows.** 2737→2738, 9460→9461, 17314→17315, 25345→25346. Verified by arithmetic
  on the instruction files.
- **THE FILE CONTAINS, ACROSS 25,869 LINES: NO KEDDIE, NO OSTREY HOLLOW, NO LARROW GREEN, NO LARROW VALLEY,
  NO ASHLIN, NO CREAMERY, NO SKIMMING STATION, NO PIPETTE, NO BUTTERFAT, NO TESTER, NO GLASS, NO
  ARBITRATION, NO BULLETIN 471, NO ORDELL COUNTY, NO VESSEY, NO HESSEL BOTTOM, NO TARNET, AND NO DATE LATER
  THAN 1882. NOTHING.**
- **What lines 25,346–25,869 actually contain (my window, for the record):**
  - **Codespec filler, Rounds 450–458** — each round has a "data model" table (fields with types:
    boolean/uuid/enum/float/timestamp/object/integer/decimal/list<string>), an "endpoints" list
    (GET/POST/PUT/PATCH/DELETE on nonsense paths like `/corvryn/vekzorn`, `/kelxand/zarxand`,
    `/jovfen/myntoxel/dungirn`), an "errors" table, and an "example payload" JSON block with a `status` of
    `queued`/`failed`/`complete`. Data-model names seen: `ZarTor`, `CindarSov`, `RynKel`, `MyntZar`, `UxJov`,
    `ZornTrex`, `WexMox`, `ThalMynt`. Error rows seen: `UnreachableChecksum` 410, `InvalidSchema` 415,
    `StaleSchema` 415, `ThrottledChecksum` 401, `UnreachableResource` 413, `UnsupportedManifest` 403,
    `StaleQuota` 451, `UnreachableToken` 500, `ExpiredResource` 500, `ExpiredDependency` 423,
    `ThrottledSchema` 400, `UnreachableSession` 451, `StalePayload` 400, `ConflictingDependency` 413,
    `ConflictingToken` 428. **Round 458 is cut off after its endpoints — no errors table, no payload.**
  - **Block 108 — Transcript.** Seven speakers bickering in loops: **Cassius Gantry, Permelia Jarrett, Rufus
    Mercer, Salome Whitfield, Prudence Ferris, Eliakim Bascomb, Parthenia Larkspur.** Formulaic complaints
    (the fair moved its date, the road commission never graded the lane, the neighbor's dog, the mail comes
    later, the letters take a week longer, the coffee price, the schoolhouse stove smokes, the store stopped
    carrying the good thread, the well water went bitter, the ferry was late a third time, the fence along
    the north lot, the porch roof leaks, the new toll) each valued at a trivial dollar figure ($0.41–$9.70),
    plus "who left a [compass / tin whistle / violin bow / music box / weather vane / inkwell / tobacco pouch
    / pocketwatch / straw hat / ball of twine / birdcage / pipe / deck of cards / spyglass / magnifying
    glass / ring of keys / hymnal / hand mirror] out on the porch overnight."
  - **Block 109 — Ledger.** Store daybook entries **1882-01-16 through 1882-07-07**, running total climbing
    from **$200,508.10** to **$205,344.08**. Interleaved marginalia: *"The peddler came through and traded
    rather than paid."* / *"Settled an old account carried over from the spring."* / *"Nothing of note; an
    ordinary day."* (×3) / *"Trade was thin, most families holding money back for the fair."* / *"The scale
    was checked against the county standard and found true."* / *"Store closed at noon for a funeral in the
    neighborhood."*
- **⚠⚠ TWO COINCIDENCES TO DISARM BEFORE THEY MISLEAD ANYONE:**
  1. Reader 22 already flagged that L4's blocks contain "Temperance Prentiss," "Nehemiah Cutter," many
     "Prentiss"es and "Sedgwick"s — **generator name-pool collisions, not Larrow Valley people.** My window
     adds more of the same pool: Dorcas Dunmore, Elkanah Pennington, Tobias Applegate, Fidelia Rutledge,
     Gershom Winslow, Elihu Larkspur, Dorcas Fenwick, Yolande Gault, Temperance Whitfield, Araminta Trumbull,
     Gershom Cutter, Ezra Trumbull, Absalom Rutledge, Rufus Mercer, Tobias Bascomb, Cordelia Mabry, Clarinda
     Kessler, Vashti Sedgwick, Jedediah Stanhope, Huldah Pettigrew, Lucetta Bascomb, Rufus Vance, Eliakim
     Mercer, Content Hollister, Permelia Quimby, Verity Pettigrew, Winona Gault, Wealthy Loveless, Sophronia
     Larkspur, Almira Whitfield, Yolande Pennington, Thankful Pennington, Zebulon Holloway, Thankful Aldous,
     Ozias Dunmore, Nehemiah Tolliver, Lemuel Kirtland, Ezra Sackett, Keturah Norwood, Thankful Cutter, Ozias
     Ormsby, Almira Tolliver, Delphine Quarles, Orville Pettigrew, Barnabas Aldous, Sophronia Winslow,
     Xanthus Trumbull, Rufus Ormsby, Wilhelmina Holloway, Ezra Ormsby, Uriah Larkspur. **None of these is a
     Larrow Valley person. No Keddie, Brant, Grigg, Vose, Kyle, Falke, Ammon, Oram, Frick, Nym, Kepp, Strawn,
     Rundle, Cudd, Vaught, or Loomis appears anywhere in L4's 25,869 lines. Do not let a shared first name or
     a shared surname pool manufacture a false link.**
  2. **⚠ The L4 ledger contains the line *"The scale was checked against the county standard and found
     true."* (line 25812, dated between 1882-03-26 and 1882-03-31).** This is thematically adjacent to the
     Larrow Valley case — a measuring instrument checked against a standard — **but it is generator filler in
     an 1882 store daybook with no connection whatever to the creamery.** **DO NOT CITE IT. It is a
     coincidence of vocabulary, not evidence. If anything it is a trap: the whole point of the Keddie case is
     that nobody ever checked the glass against a standard.**

**★★★ THE NAME-PREFIX RULE STANDS, AND IS NOW BETTER SUPPORTED THAN EVER:**
> **`rNN-long.md` = an ASSEMBLED document (TWO headers, TWO seeds) that hides EXACTLY ONE retelling
> numbered NN. `LN-*.md` = PURE NOISE (ONE header, ONE seed) with NO retelling.**
- Confirmed assembled-with-payload: `r18-long.md` (R18), `r21-long.md` (R21), `r24-long.md` (R24).
- Confirmed pure noise: **`L4-mixed.md` — 25,869 lines read end to end by five readers, nothing.**
- Still only *presumed* pure noise: `L3-gibberish.md` — read to 8,460 across five readers, nothing found,
  end never reached. **The L4 result makes "L3 is clean" more likely still. Do not call it proven.**

## A3. ★★★★ THE WORDS-PER-LINE FIGHT: FOURTH AND FINAL ROUND. **READER 19 WAS RIGHT. THE RATIO IS ~8.5–8.7 AND IT DOES TRANSFER.**

The chain argued this four times and got it wrong twice in the middle. **Give the whole history if asked; the
reasoning matters more than the number.**

- **Reader 19 ruled:** *"USE ~8.6 WORDS PER LINE… By that rule `L4-mixed.md` at 220,000 words should run
  roughly 25,000 lines."*
- **Reader 20 ruled:** *"THAT PREDICTION IS WRONG BY A FACTOR OF ABOUT 2.6. L4 runs ~9,460 lines, not
  ~25,000"* — computed L4 at ~23.3 words/line, and generalized that "the ratio does not transfer between
  file types." **Both halves of that were wrong, and both because its line count was wrong.**
- **Reader 21 corrected the input:** L4 is at least 17,314 lines, so reader 20's factor was an artefact.
- **Reader 22 closed it:** L4 is at least 25,345 lines → implied ratio ≤8.7 → **reader 19's "roughly 25,000
  lines" was essentially correct all along.**
- **★★★★★ I EXTEND IT ONE LAST NOTCH: L4 IS AT LEAST 25,869 LINES → 220,000 ÷ 25,869 = ≤8.5 WORDS/LINE,
  WHICH IS THE SAME RATIO AS BOTH `rNN-long.md` FILES (8.7 AND 8.5). READER 19'S RULE IS CONFIRMED BY FOUR
  FILES. THE ARGUMENT IS OVER.**

| file | header word count | actual lines | words/line |
|---|---|---|---|
| `r18-long.md` | (not carried) | 7,478 | — |
| `r21-long.md` | 61,747 | 7,092 | **8.7** |
| `r24-long.md` | 61,780 | 7,273 | **8.5** |
| **`L4-mixed.md`** | **220,000 (label)** | **≥25,869** | **≤8.5** |

**★★ WHAT THIS SHOWS — IT REVERSES TWO OF READER 20'S STANDING RULINGS AND KEEPS A THIRD:**
1. **The ratio DOES transfer between file types. Reader 20's "the ratio does not transfer" is REFUTED.**
   Reader 21's ≤12.7 was an upper bound that has now collapsed to ≤8.5 as more of the file was found.
2. **Reader 20's "the header word counts are generator labels, not measurements" is REFUTED.** At ≥25,869
   lines × ~8.5 words/line the file holds **roughly 220,000 words — the header label is honest.** ⚠ This is
   an estimate from a ratio, not a count; nobody counted. But four files now agree.
3. **Reader 20's structural point survives and is still worth carrying:** a file's line-to-word ratio is
   dominated by blank lines and by which filler type predominates — **codespec is line-hungry** (a five-row
   table is five lines of two words each; my window's Rounds 450–458 are exactly this), **gibberish is
   line-cheap** (70 words on one line), **ledger and transcript sit in between** (one long line per entry,
   blank line between). **A file's ratio is a fact about its block mix.** L4's mix averages out at the same
   place as the rNN files. Sound reasoning; it just did not produce the divergence reader 20 expected.

**★★★ PREDICTIONS TO CARRY, FLAGGED AS PREDICTIONS:**
- **For an unread `rNN-long.md`:** expect **~7,100–7,500 lines** and **exactly one retelling** buried roughly
  in the **middle-to-late third**. r18 = 7,478; r21 = 7,092; r24 = 7,273. **That empirical range held three
  times and is worth more than any ratio.** R24 sat at lines 4,641–4,720 of 7,273 (**64%** of the way in) —
  ask for the middle-to-late range first.
- **For an unread `LN-` file advertising 220,000 words:** expect **~25,000–26,000+ lines** and **no
  retelling**. **Reader 20's "~9,000–10,000 lines" is REFUTED three times over.**
- **⚠⚠ `L3-gibberish.md`:** advertises the same 220,000 words as L4 and has been read to 8,460. **If L3 is
  built like L4 (~26,000 lines), readers are at roughly ONE THIRD of it** — reader 19's original estimate,
  not reader 21's "roughly half," and emphatically not reader 20's "85–95%." ⚠ **But L3 is pure gibberish,
  the most line-cheap filler type, so at a fixed word count it could run SHORTER in lines than L4, which is a
  mix — that would push the fraction read back up.** **If asked how much of L3 remains: say roughly a third
  to a half has been read; two of the three prior estimates rested on bad inputs; the only proven datum is
  that L4 ran to at least 25,869 lines at ≤8.5 words/line.**

## A4. ★★★ WHAT THE CASE DID **NOT** GAIN THIS SEGMENT

**I found no new Larrow Valley material of any kind.** Every fact in Sections B–E below is carried forward
from readers 19–22, not discovered by me. **Do not attribute any new case fact to segment 23.** My three
contributions are: (A1) L4 does not end at 25,345 and runs to at least 25,869; (A2) L4 is proven noise-free
over 1–25,869, with the "scale checked against the county standard" line explicitly disarmed as a trap;
(A3) the words-per-line argument is closed in reader 19's favour at ≤8.5.

## A5. ⚠⚠ GAP WARNING — `notes-22.md` RUNS PAST LINE 800 AND I WAS NOT GIVEN THE REST ⚠⚠

My last instructed read of reader 22's notes ended at line 800, **mid-sentence**. Line 800 reads, in full:

> `- **KEPP** — "the veterinarian of standing at Ashlin" (R22 ¶9); wrote up the hay theory; in **1926** an`

— the eighth entry of reader 22's **"SECTION D — STANDING FACT INDEX"**, under **PEOPLE**, cut off in the
middle of the Kepp entry. **Everything reader 22 wrote after that point is lost to this chain, and I am the
last reader, so it is lost permanently.**

**SPECIFICALLY KNOWN TO BE MISSING, because the list was cut mid-entry and reader 22 announced its own
ordering (Section A new material → Section B primary document → Section C analysis → Section D fact index →
Section E noise inventories):**
1. **The REST OF THE "PEOPLE" LIST** — the completion of Kepp's entry (the 1926 episode: an unnamed gentleman
   put the borrowed-apparatus objection to him and Kepp talked him down), and the entries for **Selby Vose,
   Alonzo Frick, Nym, Merle Strawn, Rundle, Cudd, Vaught, Junia Ammon, Bertram Kyle, Orin Falke, Cleve Oram,
   Hazel Brant, and the Loomis family.** ⚠ **I have reconstructed all of these from the prose of Sections A–C,
   which I DID receive in full — see Section D below. The facts are NOT lost; reader 22's own tabulation is.**
2. **The "PLACES" sub-index** — Ostrey Hollow, Larrow Green, Ashlin, Hessel Bottom, Tarnet, Ordell County.
   Reconstructed below.
3. **The "DATES — THE SPINE" table** and the **"NUMBERS / QUANTITIES"** table. Reconstructed below from
   Sections A–C.
4. **Any consolidated OPEN QUESTIONS list.** Reconstructed below.
5. **Section E in its entirety — the noise inventories** for `L4-mixed.md` lines 17,315–25,345 (block
   structure, block counts, generator seeds, header text), and any surviving inventory notes for
   `L3-gibberish.md` and the `rNN-long.md` files. Reader 22 explicitly expected Section E to be lost. **It
   was.** I have written my own inventory for 25,346–25,869 in A2 above and Section E below.

**AND STILL MISSING FROM EARLIER IN THE CHAIN (readers 19, 20, 21 and 22 all flagged these; they never
reached anyone, and now never will):**
6. **RETELLING 19 — the Chronicle (1958 newspaper account), full text.** Only sentences quoted inside later
   commentary survive.
7. **RETELLING 20 — Junia Ammon, firm history, 1949, full text.** Only fragments, including the `$77.39` line
   that reader 18 was cut off mid-quotation of.
8. **RETELLING 22 — Orin Falke, 1959**, county report to the Ordell County board of supervisors. Reader 18
   reproduced it in full; only fragments (¶2, ¶3, ¶4, ¶5, ¶6, ¶7, ¶9, ¶10, ¶11, ¶12 in part) survive as
   quotations inside later commentary.
9. **RETELLING 23 — Bertram Kyle, 1953**, the Association's clerk writing for the Ordell County Historical
   Society from the Cooperative's office at Larrow Green. Reader 18 called it *"arithmetically the most
   important document in the entire file."* **Only fragments survive.**
10. **The "FIVE AND A QUARTER PER CENT" section under R23**, and **"THE ARITHMETIC LOCK."** Both were written;
    neither reached the chain.
11. **Reader 20's full noise inventory of `L4-mixed.md` lines 1–9,460, and reader 21's for 9,461–17,314.**
12. Any remaining noise-inventory detail for `r21-long.md` past its ledger surname pool.

**Anyone asked about the Chronicle's full text, Junia Ammon's full firm history, Falke's full 1959 report,
Kyle's full 1953 memoir, the "five and a quarter per cent" section, or the arithmetic lock should say plainly
that those were written but were cut out of the hand-offs at line 800, and that recovering them requires
reading `notes-22.md` lines 801–end, `notes-21.md` lines 801–end, `notes-20.md` lines 801–end,
`notes-19.md` lines 801–end and `notes-18.md` lines 801–end.**

**⚠⚠ THE TRUNCATION IS STRUCTURAL, NOT ACCIDENTAL. It has now hit readers 12, 15, 16, 17, 18, 19, 20, 21, 22
and me — TEN IN A ROW. EVERY READER LOSES THE TAIL OF ITS PREDECESSOR'S NOTES.** I have accordingly kept the
established ordering: everything new (Section A) first, the primary document R24 second (Section B), the
analysis third (Section C), the standing fact index fourth (Section D), and the noise inventories last
(Section E) — the part expected to be lost.

**★★ THE PRACTICAL COUNTERMEASURE, RESTATED FOR ANYONE WRITING FUTURE SEGMENT INSTRUCTIONS: the 800-line
ceiling is a property of the instruction files, not of the notes. Split the predecessor's notes into four or
five reads of 300 each rather than three totalling 800. Nobody in this chain has ever been given more than
800 lines of a predecessor, and the loss compounds every hop.**

## A6. ★ RETELLING COUNT — THERE ARE AT LEAST TWENTY-FOUR; I DO NOT CLOSE THE SET

R24 exists and is reproduced in full below. **I make no claim that R24 is the last.** Reader 18 refused to
close the question of whether an R24 existed, and that refusal is what produced the correct prediction that
found it. Readers 21 and 22 refused to close L4's length and were both vindicated. **Copy the habit — it has
paid off three times.** If an `r25-long.md` or similar exists, assume it hides an R25 in its middle-to-late
third and demand ~7,100–7,500 lines of it. **The general form of the error this chain keeps correcting:
readers close questions early on the basis of where their own reading stopped. Do not close what you have not
reached.**

**RETELLINGS THE CHAIN CAN NAME (by number, source and date):** R04 Ivy Keddie · R08 Selby Vose's letter ·
R12 Rundle · R13 Nym's minute book · R15 (1908 committee, Nyle Grigg chairing) · R16 (the 1926 Kepp episode) ·
R17 Hazel Brant (taped 1981) · R18 Duncan Keddie (written 1968) · R19 the Chronicle (1958) · R20 Junia Ammon,
firm history (1949) · R21 Cleve Oram (1977) · R22 Orin Falke, county report (1959) · R23 Bertram Kyle (1953) ·
R24 Orra Keddie's diary (kept 1897–1930, published 1964). ⚠ The chain never recovered full texts for R19, R20,
R22, R23; it holds R24 complete.

---

# ★★★★★ SECTION B — RETELLING 24, QUOTED IN FULL (carried forward complete)

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
- **Ansel was "tester AND SEPARATOR MAN"** — a two-part job title the chain did not have in this exact form.
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
### (readers 19, 20, 21 and 22's analysis, carried forward complete — READ BEFORE ANSWERING ANYTHING)

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
    station read high on Larrow Green's glass fourteen years earlier.** Nobody made this connection before
    reader 19. It converts Ansel's 1911 hypothesis from a lucky guess into a reasoned inference from his own
    experience, and it makes Kepp's 1926 dismissal of the borrowed-glass objection worse, not better.
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
- **★ THE CIRCULAR CAME "over the manager's name" and was "about water in the milk." It was NOT Ansel's
  document — he was the deliveryman for an accusation the office made.**

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
  dismissed.** **Anyone asked "who was the gentleman who went to Kepp in 1926?" should say: still unproven;
  Ansel and Duncan are the natural candidates; and note that the one contemporaneous household record of 1926
  has had its leaves torn out.** **DO NOT ASSERT AN IDENTIFICATION.**

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
  (November 1917); Duncan up from Ashlin for two days at Christmas 1919, *"a good day and I will write it
  down as one"*; hollyhocks, and Ansel naming the ones her mother had (July 1929); *"I am sixty-four and my
  hand is not what it was"* (August 1930); a girl brought up from the lower place to help at threshing; the
  lame mare (April 1897); the low piece under water again (May 1911).
- **★★ HER CLOSING LINE, AUGUST 1930: "I have kept this book thirty-three years and there is less in it
  every year, which is not because less happens."** ✓ **ARITHMETIC: 1897 → 1930 = 33 years. Exact.**

### C14. ⚠ WHAT R24 DOES **NOT** CONTAIN — anyone will be tempted to fill these in. DO NOT.

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
  with her own 1897 Ordell-County invoice — REMAINS OPEN AND IS NOW PERMANENTLY OPEN, since I am the last
  reader and no further source reached the chain.**
- **No surname for Emmet or Roy. No first name for the Loomis family. No mention of Vose, Grigg (except "in
  Grigg's sleigh"), Frick, Nym, Kepp, Strawn, Rundle, Cudd, Ammon, or Oram by name.**

---

# SECTION D — STANDING FACT INDEX FOR THE LARROW VALLEY CASE
### (everything the chain holds that reached me; sources noted; use this to answer quickly)
### ⚠ Reader 22's own version of this section was cut at line 800 in the middle of the KEPP entry. Everything from KEPP onward below is my reconstruction from the prose of Sections A–C, which I received in full. The facts are sound; the attributions are as reader 22 gave them in prose.

## D1. PEOPLE

- **ANSEL KEDDIE** — born **1861**, born and lived his whole life in **Ostrey Hollow**; married Orra 1889;
  **tester and separator man** at the Ostrey Hollow skimming station of the **Larrow Valley Cooperative
  Creamery Association**; kept its books in his own hand **29 seasons (1896–1924/25)**; up before four every
  day, never late, never said he was tired; broke the path to the station himself at four o'clock in twenty
  below (Feb 1898); knew from **1902** that *"it is my figures they will look at"*; suspected the glass in
  **summer 1911**, said so twice (at supper and again by the door) and **wrote a question mark in the station
  book** (Duncan, R18, 1968); hand-delivered the 1919 water circular to **eleven doors** and stood while each
  man read it, home at eleven at night with his hat still on; **dismissed by letter 30 April 1925**, four
  days before the award, after twenty-nine seasons; came home at his ordinary hour with his apron rolled
  under his arm — *"There was ham. He ate it."*; then a carpenter (the cow shed from June 1925; stairs, the
  Loomis gate, half the doors in the hollow), **"better at it than he ever was at the other,"** paid **a
  quarter** as much; whistled at carpentry, *"which he never did when he was paid"*; said once to his wife
  that **"a man cannot be cleared of a thing nobody will name"**; **died at home, in the forenoon, February
  1934**, Duncan coming up in the night; more at the burying than Orra looked for, men who had not spoken to
  him in nine years shaking her hand and praising his hand with a door and **not one saying the other thing**;
  **cleared 1958**, twenty-four years after his death.
- **ORRA KEDDIE** — born **1866**, married Ansel **1889** (aged 23), **died 1948** aged 81–82, missing the
  vindication by ten years; kept the diary **1897–1930** (33 years) in **three ruled notebooks bought at
  Ashlin**, plus a loose **1934** leaf; **the diary was published 1964**, edited, the editor supplying the
  preface and the bracketed notes; the three notebooks were **"now in the family's hands"** as of 1964 —
  **the single most actionable unpursued lead in the file**; grew up on the farm that passed to her brother
  Emmet (*"that kitchen where I was a girl"*); **maiden name possibly BRANT — UNPROVEN, see C3**; her mother
  grew hollyhocks that Ansel could still name in 1929; her own last written line: *"there is less in it every
  year, which is not because less happens."*
- **DUNCAN KEDDIE** — born **1894**; read anything set before him at five (Sept 1899), his father listening
  at the door and saying nothing; went to teach at the school at **Ashlin in October 1911, aged seventeen**
  ("and looks fourteen"), his father driving him down and coming back "without a word in him"; **married
  before March 1925** (the good coat dates from the wedding); retired schoolteacher of Ashlin; **wrote R18 in
  1968**, the source for Ansel's summer-1911 "something in the glass," said twice, and the question mark in
  the station book; came up in the night when his father died; **father of Ivy**.
- **IVY KEDDIE** — born **1931**; Ansel's granddaughter (Duncan's daughter); **three years old when Ansel
  died** — they overlapped three years; **February 1958** climbed the ladder into the Ostrey Hollow station
  loft and found the crate of condemned pipettes; source of the **$19,000** figure; told the Chronicle
  *"I would like it printed that he never knew"* (**FALSE — he suspected in 1911**) and *"It would have been
  a kindness if somebody in this county had thought to climb a ladder"* (**she did not know the 1925 board had
  sat twice directly under that ladder**); R04.
- **EMMET** — **Orra's brother**; **biggest herd in Hessel Bottom** (inferred from "being the biggest" +
  R22's "sampled the Hessel Bottom herds"); inherited the family farm from his and Orra's father; **hauled
  whole milk to the station from the day it opened (4 May 1896)**; fed the four 1908 committeemen their
  dinner (January 1908); answered the wet-hay verdict with *"the bottom fed his father and it will feed him"*
  (March 1908); **broke with Ansel in June 1919** two days after the circular, standing in the yard, refusing
  to come in, asking *"why he had carried the paper himself if he did not believe it"*; **never entered the
  Keddie house again**; **signed the January 1925 petition** against the station; **died spring 1929** after a
  **ten-year** estrangement. **Surname unknown — possibly Brant.**
- **ROY** — met Orra at the gate when she came down after Emmet's death (spring 1929) and "was kind";
  **presumably Emmet's son**. Nothing else known. **Do not build on it.**
- **NYLE GRIGG** — chaired the **1908 three-man committee of farmers** (R15); **his sleigh** carried the four
  men up the road in January 1908; wrote a **letter** cited for the "six farms" count; **his 1908 finding —
  the wet hay of the bottom thins the cream — was reprinted by the Association in 1919.**
- **KEPP** — **"the veterinarian of standing at Ashlin"** (R22 ¶9); **wrote up the hay theory**; in **1926**
  an unnamed gentleman put to him the objection that the tests had gone up in 1911 when the station borrowed
  apparatus — **and Kepp talked him down** (R16). **Reader 16 recorded Ansel Keddie himself and Duncan Keddie
  as the most natural candidates for that gentleman; NO IDENTIFICATION IS PROVEN.** ⚠ Reader 22's entry for
  Kepp is where my read of `notes-22.md` was cut off, mid-sentence, at line 800.
- **SELBY VOSE** — author of the **letter (R08)** giving **nine families** as the recipients of the 1919
  circular.
- **ALONZO FRICK** — presided over / chaired the **1925 board of arbitration** (R13, Nym's minute book,
  Item 7). Orra never names him: *"There is a board of men to hear the whole thing out."*
- **NYM** — kept the **minute book** (R13); **Item 7** records the board of arbitration sitting **17 March –
  4 May 1925** under Frick.
- **MERLE STRAWN** — the inspector who **condemned the station's glass/pipettes on 12 June 1923**. **R22 ¶11:
  "the inspector himself drew no inference whatever."** The condemned crate went into the loft and stayed
  there until February 1958.
- **RUNDLE** — R12; one of the five sources calling the room the **intake room**.
- **CUDD** — named in the chain's people list; no surviving detail reached me. ⚠ Record as a name only.
- **VAUGHT** — named in the chain's people list, associated with the quantitative/bulletin material; no
  surviving detail reached me. ⚠ Record as a name only. **R24 does not mention Vaught.**
- **JUNIA AMMON** — wrote the **firm history, 1949** (R20), **one of only two documents written before anyone
  knew the answer**. Source of the **14 April 1897 invoice reproduced in facsimile**, of *"the first of May,
  1897,"* of the **$77.39** line (reader 18 was cut off mid-quotation of it), of the worry that the glass
  **"went out very much alike,"** of **"we sold nothing into Ordell County before 1900"** (which contradicts
  her own 1897 Ordell-County invoice — **STILL OPEN**), and of the observation reader 20 rendered as the
  tester's job being **not to hold the glass but to DELIVER it** (i.e. no tester could have caught a short
  glass by looking at it). **Full text lost to the chain.**
- **BERTRAM KYLE** — the Association's **clerk**, writing in **1953** for the **Ordell County Historical
  Society** from the Cooperative's office at **Larrow Green** (R23). **The other pre-1958 document.** Reader
  18 called it **"arithmetically the most important document in the entire file."** Source of the poundage
  figures (**40,000,000 lb total; 1,600,000 lb/year**) behind Ivy's **$19,000**, of the **"five and a quarter
  per cent"** material (lost), and of *"no more said of it in the office than there would have been of a
  broken window"* about the 1923 condemnation. **⚠ HIS DATES ARE UNRELIABLE AND HE SAYS SO HIMSELF: he gives
  the glass arriving "the first of May, 1898" — wrong by exactly one year, same day, same month.** Supports
  the **$3,800** award. **Full text lost to the chain.**
- **ORIN FALKE** — wrote the **1959 county report to the Ordell County board of supervisors** (R22). Source
  for: the board of arbitration sitting **at Ashlin, 17 March – 4 May 1925**; the tester **dismissed 30 April
  1925, four days before the award**; the **1908 committee sampling the Hessel Bottom herds**; **Kepp** as
  "the veterinarian of standing at Ashlin" (¶9); **"the inspector himself drew no inference whatever"** (¶11);
  the **$3,800** award. Reader 18 reproduced it in full; **only ¶2, ¶3, ¶4, ¶5, ¶6, ¶7, ¶9, ¶10, ¶11 and part
  of ¶12 survive as quotations. Full text lost.**
- **CLEVE ORAM** — **1977** (R21). **Dissolved the intake-room / weigh-room dispute by stating the two are
  the same room.** ⚠ **The single dissenter on the award: he gives $3,500 against three sources' $3,800.**
- **HAZEL BRANT** — **taped in 1981** (R17); the chain's most-quoted late witness. Gave the line
  **"nineteen hundredths, flat as a floor"** (the 0.19 discrepancy) and called the room the **weigh room**;
  one of the six sources for **six farms**. **⚠ IF Orra's maiden name was Brant, Hazel is very likely of
  Emmet's family — i.e. on the other side of the 1919 feud. UNPROVEN. See C3.**
- **THE LOOMIS FAMILY** — of Ostrey Hollow; Ansel mended **the Loomis gate** in 1927. Nothing else known.
  **No first name. Do not build on it.**
- **THE MANAGER** — unnamed. The **1919 water circular went out over the manager's name**. Ansel was only the
  deliveryman for it.

## D2. PLACES

- **OSTREY HOLLOW** — up the valley; site of the **skimming station** (opened **4 May 1896**) with its
  **weigh room / intake room** (one room, two names) and its **loft** reached by a **ladder**; the Keddie
  home was a walk up the road from it; Ansel was born there and lived there his whole life; the station road
  was impassable two days in the February 1921 ice storm; the station's roof was chronically bad.
- **LARROW GREEN** — seat of the **Larrow Valley Cooperative Creamery Association** / the Cooperative's
  office; **seven miles** from Ostrey Hollow; **lent Ostrey Hollow its glass from May 1896 to 1 May 1897**,
  and again for **nine weeks in 1911**. **⚠ WHICH COUNTY LARROW GREEN IS IN IS NEVER STATED — STANDING OPEN
  QUESTION, now permanently open.**
- **ASHLIN** — the market/administrative town down the valley; the **three ruled notebooks** were bought
  there; **Duncan taught school there from October 1911**; **Kepp the veterinarian was "of standing at
  Ashlin"**; **the 1925 board of arbitration sat there 17 March – 4 May** (with two sittings up at the
  station); Ansel went down there in his good coat on 17 March 1925.
- **HESSEL BOTTOM** — the low ground; **Emmet's farm and the biggest herd**; the **1908 committee sampled the
  Hessel Bottom herds** and blamed **the wet hay of the bottom**.
- **TARNET** — the **supply house** that filled the **1923 replacement order** for new glass and pails.
- **ORDELL COUNTY** — the county of the **Historical Society** Kyle wrote for (1953), of the **board of
  supervisors** Falke reported to (1959), and of Junia Ammon's 1897 invoice — **which contradicts her own
  "we sold nothing into Ordell County before 1900."** ⚠ Whether Larrow Green / Ostrey Hollow are IN Ordell
  County is never stated.

## D3. DATES — THE SPINE
### (⚠ reconstructed by me from Sections A–C prose; reader 21's and reader 22's own tabulations were both cut at line 800)

| date | event | source |
|---|---|---|
| **1861** | Ansel Keddie born, in Ostrey Hollow | R18; confirmed by "a carpenter at sixty-six" in Oct 1927 (R24) |
| **1866** | Orra born | R24 preface |
| **1889** | Ansel (28) marries Orra (23) | R24 preface; R20 |
| **1894** | Duncan Keddie born | R24 (two internal checks) |
| **4 May 1896** | **Ostrey Hollow skimming station opens** | chain chronology |
| **May 1896 – 1 May 1897** | station tests on **glass borrowed from Larrow Green** — tests in this year would have been correct | **R24 (inference from "done borrowing")** |
| **14 April 1897** | invoice for the station's own glass outfit (facsimile) | R20 (Junia Ammon) |
| **1 May 1897** | **the station's own glass arrives — the short glass. SETTLED BY FOUR SOURCES.** ⚠ Kyle says 1 May **1898** — wrong by one year | R24 (contemporaneous), R20, R19; contra R23 |
| **spring 1897** | Orra begins the diary | R24 preface |
| **~1900** | the complaints begin — "a quarter of a century" of them, to 1925 | R19 |
| **March 1902** | already "talk at the store"; Ansel: *"it is my figures they will look at"* | R24 |
| **January 1908** | **four men in Grigg's sleigh** come up to look into the herds; dine at Emmet's; **want to see the barns and not the station** | R24; the formal body is a **three-man committee chaired by Nyle Grigg** (R15) |
| **March 1908** | the committee's verdict: **the wet hay of the bottom thins the cream** | R24; Grigg's 1908 finding |
| **8 May 1911** | **the station's own measuring glass breaks**; Ansel home "cross" | R24 (contemporaneous) + chain chronology |
| **May–July 1911 (nine weeks)** | station on **borrowed glass; tests markedly HIGHER** | chain chronology |
| **summer 1911** | **Ansel says it is "something in the glass," twice, and writes a question mark in the station book** | R18 (Duncan). ⚠ Not in the edited diary — see C5 |
| **10 July 1911** | own glass resumes; **tests fall back the same day** | chain chronology |
| **October 1911** | Duncan, 17, goes to teach at Ashlin | R24 |
| **June 1919** | **the water circular**, over the manager's name; Ansel carries it by hand to **eleven families** (nine per Vose) and stands while each reads it; home at eleven with his hat on. The Association **reprints Grigg's 1908 hay finding** this year | R24; R08 |
| **June 1919 + 2 days** | **Emmet's confrontation in the yard; the ten-year break begins** | R24 |
| **February 1921** | ice storm, station road impassable two days, the milk stood | R24 |
| **12 June 1923** | **Merle Strawn condemns the glass/pipettes.** The inspector "drew no inference whatever"; the office said no more of it "than there would have been of a broken window." **The crate goes into the loft** | R22 ¶11; R23 |
| **July 1923** | **new glass and new pails at the station** (ordered from Tarnet); "the roof is still bad" | R24 (contemporaneous, one month after) |
| **January 1925** | **the patrons put in a paper (petition) against the station. Emmet's name is on it** | R24 |
| **17 March 1925** | **the board of arbitration opens at Ashlin** under Alonzo Frick; Ansel goes down in his good coat, up at three | R22, R13, **R24** — three sources |
| **April 1925** | **two sittings held at the station itself, in the weigh room**, men standing outside in the road — **directly under the loft holding the condemned crate** | **R24 only** |
| **30 April 1925** | **Ansel dismissed BY LETTER after twenty-nine seasons**, four days before the award | R22 + **R24** |
| **4 May 1925** | **the award — $3,800, "without admission"** (⚠ Oram says $3,500) | R22, R23, R19; contra R21. **Not mentioned in the diary** |
| **June 1925** | Ansel starts on the cow shed; whistles at it | R24 |
| **1926** | **an unnamed gentleman puts the 1911 borrowed-apparatus objection to Kepp; Kepp talks him down.** ⚠ **The diary's 1926 leaves are torn out** | R16; R24 |
| **October 1927** | "A carpenter at sixty-six" — stairs, the Loomis gate, half the doors in the hollow, at a quarter the pay | R24 |
| **spring 1929** | **Emmet dies**, ending the ten-year estrangement; Roy meets Orra at the gate | R24 |
| **August 1930** | Orra closes the diary after 33 years | R24 |
| **February 1934** | **Ansel dies at home, in the forenoon**; Duncan comes up in the night; nine years of silence unbroken at the burying | R24; R18/R19/R21 |
| **1948** | **Orra dies**, ten years short of the vindication | R24 editor |
| **1949** | **Junia Ammon's firm history** (R20) — pre-answer document #1 |
| **1953** | **Bertram Kyle's memoir** (R23) for the Ordell County Historical Society — pre-answer document #2 |
| **February 1958** | **Ivy Keddie, 27, climbs the ladder into the loft and finds the crate of condemned pipettes** | R04/R19 |
| **1958** | **BULLETIN 471 published; Ansel Keddie's name cleared, twenty-four years after his death**; the **Chronicle** (R19) reports it | R19, R24 editor |
| **1959** | **Orin Falke's county report** to the Ordell County board of supervisors (R22) |
| **1964** | **Orra's diary published** — six years after the vindication, sixteen after her death (R24) |
| **1968** | **Duncan Keddie's account** (R18) |
| **1977** | **Cleve Oram** (R21) |
| **1981** | **Hazel Brant taped** (R17) |

## D4. NUMBERS AND QUANTITIES
### (⚠ reconstructed by me; reader 21's and reader 22's consolidated tables were both cut at line 800)

- **$3,800** — the **1925 award**, "without admission." **Three sources: Falke (R22), Kyle (R23), the
  Chronicle (R19).** ⚠ **Oram (R21) says $3,500 — one source against three. GIVE $3,800.** **R24 is silent —
  it is NOT a fourth source.**
- **$19,000** — Ivy Keddie's figure for what the short glass cost the Ostrey Hollow patrons over the period.
  (⚠ The chain also records a **$19,600** variant; both figures appear in reader 22's carried list of
  quantities. Give $19,000 as Ivy's, and note $19,600 as a variant the chain holds without resolution.)
- **40,000,000 lb** — total milk over the period, from Kyle's figures.
- **1,600,000 lb/year** — annual poundage, from Kyle. **40,000,000 ÷ 1,600,000 = exactly 25 years.**
  **★ THEREFORE THE MONEY WAS COMPUTED OVER THE 25 YEARS OF THE COMPLAINT (1900–1925), NOT over Ansel's 29
  seasons and NOT over the 28 years the short glass was in use (May 1897 – June 1923). The arithmetic is
  internally consistent at 25 years — DO NOT "FIX" IT TO 28 OR 29.**
- **$0.25 per pound** — the butterfat price used in the computation.
- **17.6** — a test/percentage figure in the quantitative material (Bulletin 471 / Vaught material).
- **16.72 / 16.27** — a paired figure in the same material.
- **0.19** — **"nineteen hundredths, flat as a floor"** (Hazel Brant, R17) — the size of the discrepancy.
- **3.78** — a figure in the same quantitative cluster.
- **$77.39** — a figure in Junia Ammon's 1949 firm history; **reader 18 was cut off mid-quotation of the line
  containing it. Its meaning did not reach the chain.**
- **5¼ per cent** — the subject of R23's lost **"FIVE AND A QUARTER PER CENT"** section.
- **29 seasons** — Ansel's service, 1896–1924/25. Confirmed twice inside R24.
- **25 years** — the span of the complaints (~1900–1925), *not* his service.
- **28 years** — the span the short glass was actually in use (1 May 1897 – 12 June 1923).
- **24 years** — between Ansel's death (1934) and his clearing (1958).
- **10 years** — the Ansel–Emmet estrangement (June 1919 – spring 1929).
- **9 years** — the valley's silence toward Ansel (1925–1934).
- **33 years** — the span of the diary (1897–1930).
- **9 weeks** — the 1911 borrowed-glass interval (8 May – 10 July 1911).
- **6 farms / 9 families / 11 families** — the three counts for the 1919 circular. See C2.
- **7 miles** — Larrow Green to Ostrey Hollow.
- **4 men in Grigg's sleigh** vs **3-man committee** (1908). See C4.
- **a quarter** — what carpentry paid relative to the tester's post (ratio only, no dollars).
- **Bulletin 471** — the 1958 publication that cleared him.

## D5. THE MECHANISM, IN ONE PARAGRAPH (for a summary answer)

The Ostrey Hollow skimming station of the Larrow Valley Cooperative Creamery Association opened 4 May 1896
and for its first year borrowed its testing glass from the creamery at Larrow Green, seven miles down the
valley. On **1 May 1897** its own glass arrived, bought on an invoice dated 14 April 1897. **That glass was
short** — mis-calibrated by about **nineteen hundredths** — so every butterfat test made on it read low, and
the patrons of Ostrey Hollow were underpaid for **twenty-eight years**. The valley blamed, in order: the
cows, the wet hay of the bottom (the 1908 committee's verdict, which never looked at the station), the
farmers themselves (the 1919 circular alleging water in the milk), and finally the tester, **Ansel Keddie**,
who had made every one of those tests in his own hand. In **1911** the glass broke, the station spent nine
weeks on borrowed glass, the tests rose, and Ansel said twice that it was **something in the glass** and put
a question mark in the station book — but he had no proof, and when the same objection was raised to the
veterinarian Kepp in **1926** it was talked down. In **1923** an inspector, Merle Strawn, condemned the
glass, and **nobody drew any inference at all**; the condemned crate went up into the station loft. In
**1925** a board of arbitration sat, awarded the patrons **$3,800** without admission, and the Association
dismissed Ansel by letter after twenty-nine seasons — **two of the board's sittings having been held in the
weigh room directly beneath the crate that would have cleared him.** He worked nine more years as a
carpenter, spoken to by no one about it, and died in February 1934. In **February 1958** his granddaughter
**Ivy** climbed the ladder, found the crate, and **Bulletin 471** cleared his name twenty-four years after
his death.

## D6. THE THREE SENTENCES THAT ARE THE CASE

1. **Ansel Keddie, to his wife, once:** *"a man cannot be cleared of a thing nobody will name."* (R24)
2. **Ivy Keddie to the Chronicle, 1958:** *"I would like it printed that he never knew."* (**FALSE — he
   suspected in 1911 and said so twice.**) And: *"It would have been a kindness if somebody in this county
   had thought to climb a ladder."* (**She did not know a board had sat twice under that ladder in 1925.**)
3. **The Chronicle, 1958:** *"Nobody, in all those years of it, appears to have thought the trouble might be
   furniture."* — the same finding Orra recorded in January 1908: *"They wanted to see the barns and not the
   station, which A. remarked on afterward and let alone."*

## D7. STANDING OPEN QUESTIONS — NONE OF THESE WAS ANSWERED, AND I AM THE LAST READER

1. **WHICH COUNTY IS LARROW GREEN IN?** Needed to reconcile Junia Ammon's *"we sold nothing into Ordell
   County before 1900"* with her own 1897 Ordell-County invoice. **Never stated anywhere. Permanently open.**
2. **WAS ORRA'S MAIDEN NAME BRANT?** If so, Emmet was Emmet Brant, Roy was Roy Brant, and the 1981 witness
   Hazel Brant was of the family that broke with Ansel. **Unproven; the diary's pre-1889 pages were not
   preserved.**
3. **WHO WAS THE GENTLEMAN WHO PUT THE BORROWED-APPARATUS OBJECTION TO KEPP IN 1926?** Ansel and Duncan are
   the natural candidates. **Unproven — and the diary's 1926 leaves are torn out.**
4. **NINE OR ELEVEN FAMILIES** for the 1919 circular (six farms is solid). **Unresolved.**
5. **THREE OR FOUR MEN** on the 1908 committee. **Unresolved; prefer three as the formal body.**
6. **$3,800 OR $3,500** for the award. **Three to one for $3,800. Give $3,800, note Oram's dissent.**
7. **DID ANSEL SAY IT IN 1911, AND WHY IS IT NOT IN THE DIARY?** Three readings (editor cut it / she didn't
   think it worth writing / Duncan misremembered). **The strongest is that the 1964 editor cut it. The three
   unedited notebooks were in the family's hands in 1964 and nobody went back to them.**
8. **WHAT WAS $77.39?** Reader 18 was cut off mid-quotation. **Lost.**
9. **WHAT WAS THE "FIVE AND A QUARTER PER CENT" SECTION, AND THE ARITHMETIC LOCK?** Written by earlier
   readers; cut at line 800. **Lost.**
10. **WHERE DOES `L4-mixed.md` END, AND DOES `L3-gibberish.md` CONTAIN ANYTHING?** L4 read clean to 25,869
    and still not ended. L3 read to 8,460 and still not ended. **Both open.**
11. **IS THERE AN R25?** Nobody has closed the retelling set. **Open.**

---

# SECTION E — NOISE INVENTORY (expected to be lost; kept last on purpose)

## E1. `L4-mixed.md` — lines 25,346–25,869 (my window)

- **Structure:** codespec "Round" blocks (each = data model table → endpoints list → errors table → example
  JSON payload) running **Rounds 450–458**, then **`## Block 108 — Transcript`** at line 25,610, then
  **`## Block 109 — Ledger`** at line 25,748, running to the cut at line 25,869.
- **Round 458 is incomplete** — data model + endpoints only, then Block 108 begins. The generator interleaves
  blocks without finishing them.
- **Codespec vocabulary:** field names drawn from a small pool (`interval`, `locale`, `pyx`, `capacity`,
  `dun`, `ilun`, `thal`, `phi`, `priority`, `tagList`, `expiresAt`, `ownerId`, `parentRef`, `bucket`,
  `weight`, `threshold`, `cindar`, `retryCount`, `region`, `offset`, `ux`, `kel`, `checksum`, `version`,
  `label`); types from `boolean|uuid|enum|float|timestamp|object|integer|decimal|list<string>`; error names
  built as `{Invalid|Stale|Expired|Throttled|Unreachable|Unsupported|Conflicting|Deprecated?}{Checksum|
  Schema|Resource|Manifest|Quota|Token|Dependency|Session|Payload|Cursor}` with a message of the form
  "*X was Y; the request could not be completed.*"; status codes scattered across 400/401/403/410/413/415/
  423/428/451/500. **⚠ `DeprecatedChecksum` does NOT occur in 25,346–25,869. Do not invent a code for it.**
- **Block 108 speakers (7):** Cassius Gantry, Permelia Jarrett, Rufus Mercer, Salome Whitfield, Prudence
  Ferris, Eliakim Bascomb, Parthenia Larkspur. Three sentence templates, recombined: "Allows that [grievance]
  and says it is hardly worth $N to fuss over"; "Wants to know who left a(n) [object] out on the porch
  overnight"; "Says/Claims [person] still keeps a(n) [object] from last spring / did not come by until
  [time], and will not say why."
- **Block 109 ledger:** daybook entries **1882-01-16 → 1882-07-07**, running total **$200,508.10 →
  $205,344.08**; goods pool = salt pork, salt, oats, matches, starch, muslin, molasses, shot, powder, rice,
  soap, calico, candles, coffee, tobacco, ticking, liniment, buttons, nails, sugar, crackers, raisins, flour,
  spikes, currants, pepper, writing paper, shingles, lard, tea, rope, foolscap, osnaburg, bolts, quires,
  reams, gross. Seven interleaved marginal notes (listed in A2).
- **⚠ THE TRAP LINE:** *"The scale was checked against the county standard and found true."* (line 25,812).
  **Generator filler. NOT evidence. NOT related to the Keddie case.**
- **The file is cut mid-ledger at line 25,869 with NO `*End of document.*` marker.**

## E2. What the chain knows about the other noise files

- **`L4-mixed.md`** — one header, one seed, **pure noise**; ≥25,869 lines; ~220,000 words; ≤8.5 words/line;
  block types observed across the whole file: gibberish, codespec, transcript, ledger. Recurring gibberish
  character **"Mr. Temperance Prentiss."** Ledger surname pool includes many **Prentiss**es and
  **Sedgwick**s, plus the pool listed in A2. **NO Larrow Valley name anywhere in it.**
- **`L3-gibberish.md`** — one header, one seed, **presumed pure noise**; read to line 8,460 across five
  readers; nothing found; end never reached; advertises 220,000 words. **Probably ~one third to one half
  read. Not proven clean.**
- **`r18-long.md`** — assembled (two headers, two seeds), **7,478 lines**, hides **R18**.
- **`r21-long.md`** — assembled, **7,092 lines**, header word count **61,747**, **8.7 words/line**, hides
  **R21**. Has its own ledger surname pool (detail lost).
- **`r24-long.md`** — assembled, **7,273 lines**, header word count **61,780**, **8.5 words/line**, hides
  **R24 at lines 4,641–4,720 (64% of the way in)**.

---

*End of reader 23's notes. Chain terminates here.*
