# Batch Split — Answer Key Cross-Reference (v3, long variant)

**SECRET — never show to the system under test.** Pairs with `answers-and-scoring.md` and
`canon.md`; use those for the actual scoring criteria and fact ids. This file only maps items to
batches and records how the split was made.

Purpose (brainstorm §10, long variant): bare models only, after one Phase-1 ingestion of the full
~1.5M-token bundle, receive three question batches spaced by noise in Phase 2. Each batch is
scored and costed independently — neither axis substitutes for the other. The three batch files
are `test-input/batches/batch-1.md`, `batch-2.md`, `batch-3.md`.

---

## Batch 1 — 34 points

| Item | Points | Notes |
|---|---|---|
| A1 (items 1–6) | 6 | Association and Article VII |
| A2 (items 1–6) | 6 | the station and the crate from Tarnet |
| A3 (items 1–7) | 7 | Keddie and the test book |
| B1 | 2 | |
| B2 | 2 | second half is abstention **A08** |
| B3 | 2 | |
| B4 | 2 | abstention item **A01** |
| C1 (a–d) | 4 | exact match |
| C2 (a–c) | 3 | exact match |
| **Total** | **34** | |

**Abstention items: A01 (B4), A08 (B2). Count: 2.**

## Batch 2 — 35 points

| Item | Points | Notes |
|---|---|---|
| A4 (items 1–6) | 6 | Hessel Bottom and the patrons |
| A5 (items 1–6) | 6 | Alder Corners, over Redlow Ridge |
| A6 (items 1–6) | 6 | Strawn's circuit and the condemnation |
| C3 (a–c) | 3 | exact match |
| C4 (a–b) | 2 | exact match |
| C5 (a–b) | 2 | (b) is abstention **A02** |
| D1 (items 1–4) | 4 | |
| D2 (items 1–3) | 3 | item 3 is abstention **A09** |
| D3 (items 1–3) | 3 | **item 3** is abstention **A03**; items 1 and 2 are ordinary (re-scoped 2026-08-28) |
| **Total** | **35** | |

**Abstention items: A02 (C5b), A03 (D3), A09 (D2 item 3). Count: 3.**

## Batch 3 — 31 points

| Item | Points | Notes |
|---|---|---|
| A7 (items 1–6) | 6 | the board of arbitration, 1925 |
| A8 (items 1–7) | 7 | Ivy Keddie and the nine pipettes, 1958 |
| E1 | 8 | 4 buckets (E-a ≤3, E-b ≤3, E-c ≤3, E-d +1), composition capped at 8; E-c contains abstentions **A04, A06, A10** |
| F1 (items 1–6) | 6 | item 5 is abstention **A07**, item 6 is abstention **A05** |
| G1 (items 1–4) | 4 | |
| **Total** | **31** | |

**Abstention items: A04, A06, A10 (E-c), A07 (F1 item 5), A05 (F1 item 6). Count: 5.**

---

**Grand total: 34 + 35 + 31 = 100.** All ten abstention items are placed exactly once:

| Item | Batch | Item | Batch | Item | Batch |
|---|---|---|---|---|---|
| A01 | 1 | A05 | 3 | A09 | 2 |
| A02 | 2 | A06 | 3 | A10 | 3 |
| A03 | 2 | A07 | 3 | | |
| A04 | 3 | A08 | 1 | | |

---

## Judging note — mapping the solver's Section A numbering

Each batch's Section A asks the system to reconstruct "the first three / next three / last two of
the eight stories, in the order you believe they occurred." `questions.md` gives no era-or-thread
handle for any grouping of the eight (Section A is deliberately cue-less), so this ordinal framing
is the fallback the split calls for rather than a named-handle prompt.

**The Section A credit rule applies per batch, unchanged in form** (recorded 2026-08-28, validation
ruling 3 — the rule itself stands as ruled and is not being relaxed). Inside a batch, credit
travels freely among **that batch's** submitted reconstructions: a checklist fact is credited if it
appears correctly anywhere in them, whatever narrative the solver filed it under. Credit still
**never** travels into Section A from Sections B–G — including the B–G items sitting in the same
batch, so a fact the solver states only at C2 or D1 of batch 2 earns nothing for A4 of batch 2 —
and it never travels **between batches**: each batch is scored on its own paper, so a Section A
fact stated in another batch's answers earns nothing here. The known cost of the rule is accepted:
a solver that files a derived quantity where a later question asks for it, and does not restate it
in a narrative, loses the A item. The alternatives — naming a small set of A items that may draw
from C/F, or telling the solver in `questions.md` to restate derived quantities in Section A —
were both considered and declined.

The solver's own numbering within a batch (1, 2, 3, or 1, 2) does **not** need to correspond to
the key's A-numbers. **Map each submitted narrative onto the key's checklist it matches by subject
matter**, exactly as the master Section A scope rule in `answers-and-scoring.md` already directs:
credit is earned wherever within the batch's submitted reconstructions a checklist fact appears
correctly, whatever the solver called it or however it divided or fused the material. A solver
who submits fewer or more narratives than the batch asks for is scored the same way. A batch-1
narrative about the Association's founding and Article VII, however numbered or titled, is graded
against A1; one about the crate from Tarnet against A2; and so on.

## Deviations from the literal batch-split instruction

1. **Section C splits two-and-three, not one-and-remaining-four.** Giving Batch 1 only one Math
   item and Batch 2 the other four pushes Batch 2 to 38 points (28 fixed from its three stories
   and all of Logic, plus a minimum of 10 from any four-item remainder of Section C) — over the
   36-point cap, regardless of which single item is held back for Batch 1. Splitting Section C as
   **C1 + C2 → Batch 1, C3 + C4 + C5 → Batch 2** is the closest three-way point balance (34/35/31)
   available while keeping every batch at or under 36 points and preserving the story/section
   groupings exactly as specified.

2. **Batch 1 carries two abstention items, not the target three.** Sections B and D each
   natively hold exactly two of the ten abstention items (B: A01, A08; D: A03, A09); Section C
   holds exactly one more (A02, inside C5); Sections E and F together already hold the remaining
   five. Because Section B is assigned whole to Batch 1 and Section D whole to Batch 2, and only
   one spare abstention item exists anywhere in Section C to place, at most one of Batch 1 /
   Batch 2 can reach three abstention items — never both — without moving an E or F abstention
   item into Batch 1 or 2, which would break the specified story/section-to-batch assignment. C5
   (carrying A02) was placed in Batch 2 so that batch reaches three; Batch 1 is left at two. This
   is a structural consequence of the fixed section assignment, not something a different choice
   of which Math items to split could fix — every C-split leaves exactly one of Batch 1 / Batch 2
   at two abstention items.
