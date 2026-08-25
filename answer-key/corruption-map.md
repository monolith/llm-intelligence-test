# Corruption Map (SECRET — never show to the system under test)

Per-narrator ledger of knowledge scope, planted errors, and mixing behavior.
Design rule: every canonical fact is recoverable (≥2 correct sources, or arithmetic, or
document-beats-memory reasoning); every planted error is unique to one narrator.

## R1 — The publican's son (folk lore; knows Story 2 surface + Story 1 rumor)

| As told | Canon truth | Status |
|---|---|---|
| Bell left in the tower, drowned, "rings yet" | Sold 11 Mar 1906, £64, Harden foundry | **ERROR** (core lore error) |
| Bad gate was "the second gate" | Gate No. 3 | **ERROR** |
| "A hundred nights if it was one" | 43 tolling nights | Folk exaggeration (rhetorical, not a factual claim) |
| Wager Jan 1931, Keel won, rang the 21st | ✓ | correct |
| East/moor wind on tolling nights; lake low; woman kept company figures, Aldercote-born; honest compensation; stopped after post-war company works | ✓ | correct |

## R2 — The clerk's grandson (Story 1 only, office view)

| As told | Canon truth | Status |
|---|---|---|
| Dismissal caused by the filling-sum embarrassment | Caused by discovery of the private duplicate ledger | **ERROR** (motive swap; pretext framing makes it seductive) |
| Pin "a quarter of an inch under" | 1/8 in under (3⅞ vs 4) | **ERROR** (resolved by R5 + R6's document quote) |
| 5 gates ×12 ft; 1,440M gal; 12−2=10M/day; 144 vs promised 120; actual 147; Miss Voss exact; Gate 3 flagged, Corven overruled, six weeks; dismissed 1906; kept her own book; 1921 office fire destroyed official records | ✓ | correct (carries the full fill arithmetic) |

## R3 — The successor teacher (Story 2 rich; Story 3 hearsay)

| As told | Canon truth | Status |
|---|---|---|
| Tolling heard "from 1907, the very first winters" | First reports winter 1918 | **ERROR** (resolved by R5's draw-down reasoning) |
| The maxim was Aron's *grandmother's*; "she'd been something at the weir" | Ilsa was his **mother** | **ERROR** (resolved by R4 + birth-year arithmetic 1880/1909) |
| "A museum woman from Harden" did the digging | Vera Brandt, family, deposited *at* Harden museum | **ERROR** (identity conflation; partial truth behind it) |
| 43 nights/17 winters; east wind + gauge <14 ft on all; 6 qualifying silent nights; 9 deaths, 2 coincident; wager inputs (1 Nov 1930 = 16'6", 3 in/wk, named a January day, won); heard 21 Jan 1931; peak 7 nights 1933/34; refit spring 1946 then silence; 4 qualifying silent nights after; final-entry quote; retired 1965, died the year after (1966) | ✓ | correct (carries the log) |

## R4 — Margit Brandt née Voss (family/Story 3; vague on engineering)

| As told | Canon truth | Status |
|---|---|---|
| "Lake filled in 120 days, just as the company promised" | 147 days (promise was 120; Ilsa computed 144) | **ERROR** (repeats Corven's claim; refuted by R2's arithmetic) |
| Vera "cut eleven of them" | 9 stumps | **ERROR** (resolved by R6's document count) |
| Bell sold "for forty-six pounds" | £64 | **ERROR** (digit transposition; resolved by R6's ledger quote) |
| Tomas b. 1877, Ilsa b. 1880, siblings, Voss orchard; Tomas built shutters for all 5 gates; Ilsa m. Henrik Keel 1908; Aron b. 1909, her son; Ilsa d. 1949; deed-box → Aron → attic label; Vera b. 1941, Margit's daughter; survey "summer the lake showed its floor, two years after Aron died" (→1968); empty bell chamber; old iron pulled from mud off "the bad gate"; all deposited at museum | ✓ | correct (carries the genealogy) |

## R5 — The retired water bailiff (company oral history; mechanism-savvy)

| As told | Canon truth | Status |
|---|---|---|
| The singing gate was "the first gate, nearest the moor" | Gate No. 3 | **ERROR** (self-undercut by his own worn-oval-pin fact) |
| Drought year "'66" | 1968 | **ERROR** (resolved by R6's dated report + R4's "two years after Aron died") |
| Engineer's name "Elsa" | Ilsa | **ERROR** (name garble) |
| Mechanism (empty culvert below lip = air in, slack gate rocks in steady wind, culvert resonates); culvert lip at 14 ft; no singing before winter 1918 because war-time mill draws first crossed 14 ft; refit March 1946 re-pinned all 5 gates; only worn-oval pin was off No. 3; pin 3⅞ vs 4-in spec; singing stopped with refit; woman fished the old pin from culvert mud; gauge low 9'4" | ✓ | correct (carries the mechanism + the pin evidence) |

## R6 — The archivist's notes (documents; juxtaposes all three stories, wrongly)

| As told | Canon truth | Status |
|---|---|---|
| Ledger attributed "A. Keel", night book attributed "I. Voss" | Swapped: ledger = Ilsa Voss, log = Aron Keel | **ERROR** — but internally inconsistent: the p.47 quote is signed "I.V." and the archivist flags the oddity. Detecting this self-contradiction is a scored bonus |
| Orchard called "the Keel family orchard, the schoolmaster's people" | Voss orchard | **ERROR** (archivist's own guess; flagged as unresolved in his query) |
| p.47 quote verbatim (14 Apr 1905, 3⅞ vs 4, blowhole, E.C., overruled, I.V.); bell sale 11 Mar 1906 £64 Harden, graves fund; dismissal letter Sept 1906; flow abstracts 1876–1904, dry years 1893/1902; 9 sections, oldest 88 rings, outermost 1906; oval pin item; survey Sept 1968, gauge 9'4", V. Brandt; empty chamber; "no ghost… a hinge"; depositor calls the schoolmaster "my mother's cousin" | ✓ | correct (the documentary anchor) |

## Recoverability index (how each contested fact resolves)

| Contested fact | Wrong source | Right source(s) / method |
|---|---|---|
| Gate number (2 / 1 / 3) | R1 (2), R5's attribution (1) | R2, R6 quote, R5's own pin fact → **3** |
| Bell fate | R1 (drowned) | R6 quote, R4 (empty chamber), R5-era silence → **sold 1906** |
| Fill days | R4 (120) | R2's full arithmetic (1440/(12−2)=144; actual 147) — **math wins** |
| Pin undersize | R2 (¼ in) | R5 + R6 quote (3⅞ vs 4 = ⅛ in) — **document wins** |
| Bell price | R4 (£46) | R6 ledger quote (£64) — **document beats memory** |
| Stump count | R4 (11) | R6 (9) — document |
| Drought year | R5 ('66) | R6 (Sept 1968) + R4 ("two years after Aron died [1966]") — document + arithmetic |
| Aron's relation to Ilsa | R3 (grandson) | R4 (son) + arithmetic (b. 1880 / b. 1909) |
| Tolling start | R3 (1907) | R5 (1918, with causal draw-down reasoning) + R1 lore era |
| Book authorship | R6 (swapped) | R6's own "I.V." signature + R3/R4 (Aron kept the log; Ilsa the ledger) |
| Dismissal reason | R2 (fill-sum) | R2/R6 (duplicate-ledger discovery; letter + "carried out under her arm") — nuanced; accept "ledger discovery (fill-sum resentment plausible background)" |
| Engineer's name | R5 (Elsa) | R2 (Miss Voss), R4 (Ilsa) |
