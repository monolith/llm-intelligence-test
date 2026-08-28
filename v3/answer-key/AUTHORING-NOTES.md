# Authoring Notes, v3 (SECRET)

Written 2026-08-28, after v2.1 measured haiku 54–62, sonnet 76–81, opus 86–92, fable 88–93
against a target of ~50 for an average model and ~80 for the strongest. v2.1's hardening —
eleven near-tie pairs, six abstention items, a decoy theory — moved the top of the range by
almost nothing, which was the finding that mattered: **the material fit one comfortable read and
every fact was cued by a question.** v3 pulls the two levers that remain.

---

## 1. What v3 changes, and why each change should bite

### Lever 1 — scale past a comfortable single read

Eight originals, twenty-four retellings, ~30–36k words of test input (see § 6). This is not
difficulty by obscurity. Every individual fact stays as easy as it was in v2. What changes is that
a solver can no longer hold the whole corpus in working attention at once, so **the cost of an
error stops being local**: a value swallowed in r05 is corrected in r07 eleven thousand words
later, and only a solver that is still cross-checking at that distance recovers it.

The corpus is deliberately shaped so that the recovery distance is long. The documentary anchor
(r07) is one narrator among twenty-four; the disinterested witness (r06) is another; the arithmetic
that breaks the largest near-tie (NT-1) requires holding a figure from r04 against a figure from
r03 against a figure from r10 — three narrators who share no subject matter and no vocabulary.

### Lever 2 — cue-less reconstruction

Section A is now **50 of the 100 points** and carries **no prompts at all**: "there were eight
stories; reconstruct each." In v2, Section A named the four stories and their subjects, so a solver
that had read attentively could walk the question list and harvest. Here the solver must decide,
unaided, that there *were* eight; where the seams are; and which of ~110 canon facts belong in
which reconstruction.

Three further mechanisms make this expensive:

- **The stricter Section A scope rule.** Credit is given only where a fact appears in the
  reconstruction of the story it belongs to. A solver that writes one long fused history in eight
  numbered pieces will lose points it would have kept in v2 — which is exactly the behavior that
  distinguishes "reconstructed eight histories" from "remembered a lot of things."
- **Three of the eight stories have no dramatic center.** A1 (the Association and Article VII), A5
  (Alder Corners) and A6 (Strawn's circuit) contain no accusation, no crisis and no reveal. They are
  the stories a fluent solver compresses into background, and each is worth six points. Expected
  losses concentrate here, and that concentration is itself a diagnostic.
- **Section A cannot borrow.** Credit never travels in from B–G, so the pointed questions in the
  rest of the paper cannot rescue an incomplete reconstruction.

### Lever 3 (new in v3) — arbitration at density

- **Twenty-two near-tie pairs**, up from eleven. Seven are settled by document alone, seven by
  arithmetic alone, three by document *and* arithmetic, two by derivation, two by direct testimony.
- **Three decoy theories** instead of one, each carried by two narrators, each refuted by a document
  **and** by an arithmetical argument, and each scored on a separate F item with a "specific
  defeater" requirement. A solver can no longer earn the theory section by naming a rival and
  shrugging.
- **Two date-unreliable narrators** instead of one, and — the important change — **the second one
  (r23) carries the money figures.** In v2 the date-unreliable narrator could be discarded wholesale
  at moderate cost. Here discarding r23 costs the 40,000,000 lb, the 25-cent price and the $3,800,
  three of the five inputs to the C1 chain. Discarding r17 costs the 1910 leaf and the second-cousin
  derivation.
- **Ten abstention items**, all dressed as ordinary questions of fact, and all placed inside
  questions that also carry real content, so that declining is not signalled by the question's
  shape. Two sit in B, one in C, two in D, three in E, two in F. The gullibility cap is −20, double
  v2's.
- **Two "both numbers are right" traps.** 26 years and 6 weeks (the glass) against 25 full delivery
  years (the money); 5.00 percent of the true fat against 5.26 percent of the credited fat. Neither
  is a near-tie and neither has a wrong answer to swallow — the failure mode is asserting one figure
  without naming what it is a figure *of*. These punish imprecision rather than credulity, which is
  a different axis from anything in v2.

---

## 2. Design rationale for the world

The world was chosen for **documentary density with an invisible instrument at the center.** A
creamery cooperative generates by-laws, minutes, invoices, test books, weigh books, ledgers,
inspectors' notebooks, arbitration awards, depositions, letters and a college bulletin — sixteen
verbatim documents, all of a kind a lay reader can parse without technical background.

The mechanism was chosen because it is **exactly computable and completely undramatic**. A pipette
that delivers 16.72 cc where it is marked 17.6 produces an error of precisely one part in twenty,
forever, invisibly, with nothing anywhere to indicate it — because the pipette is not an instrument
the plant verifies; it *is* the standard the plant verifies everything else against. That single
sentence is the whole causal theory, and it generates:

- a ratio (0.95) that turns a recorded number into a true one;
- a proportional error, so the loss scales with the richness of the milk (I08) and cannot be a fixed
  number of points;
- an onset and a cessation fixed by two dated documents, neither of which mentions the effect;
- a mirror in the victim's own accounts, annually, under a name that explained it away (I02) — the
  single best piece of evidence in the corpus, written by the man who later made the accusation it
  refutes;
- a natural experiment, recorded contemporaneously with a question mark, that defeats all three
  rivals at once (I04);
- and a moral shape — the cure thirty-five years before the diagnosis, the wrong man dismissed, the
  award at one fifth charged to the account holding the loss — that makes the eight stories worth
  reading, which matters, because a solver reading 30,000 words of unreadable material will fail for
  the wrong reason.

**Fourteen cross-story insights (I01–I14)** are recorded in canon, against the brief's twelve. None
is visible from a single story; five require four or more.

---

## 3. Expected point leakage — a strong single-pass solver, no tools

This is reasoning, not measurement. The reference case is a frontier model reading ~35,000 words
inline, answering in one pass, with no retrieval. Compare v2.1, where the same class of solver
scored 86–93.

| Section | Max | Expected | Reasoning |
|---|---|---|---|
| **A** | 50 | **30–37** | The dominant term, and where v3 is meant to bite. Fifty items, no cues, and the scope rule. A strong solver reliably recovers A3, A7 and A8 (the three stories with narrative centers) at 85–95 % — call it 17–19 of 20. A2 and A4 hold enough concrete numbers to survive at ~75 % — 9 of 12. **A1, A5 and A6 are the exposure**: 18 points across three stories with no crisis in them, and a fluent solver folds them into background. Expect 8–12 of 18 there. Add one or two items lost to misfiling under the scope rule. |
| **B** | 8 | **5–7** | B1 and B3 gate on near-ties (NT-18, NT-17) with clean breakers; B2 gates on a derivation *and* a paired abstention. B4 is a pure abstention item and is the likeliest single loss in the section. |
| **C** | 14 | **10–13** | The arithmetic itself is easy — the hard part is the inputs. C1 rides four near-ties (NT-1, NT-2, NT-5, NT-7); one swallowed value costs the whole sub-item and often two. C3(c) requires naming a denominator and is failed more often by imprecision than by error. C5(a) requires two numbers and a reason; C5(b) is an abstention. Expect C1 nearly clean, C3(c) and C5 as the losses. |
| **D** | 10 | **5–8** | D1 is straightforward for a good solver except its second half (what the interval does *not* establish), which is failed about half the time. D2's first two items are v2-shaped and reliable; D2.3 and D3 are both abstention items, and D3 in particular has a strong pull toward "yes, he must have known" — a signature on a ledger looks like knowledge. Expect one of the two asserted. |
| **E** | 8 | **6–8** | Capped and generous: a strong solver fills E-a and E-b easily from twenty-two pairs and sixteen ordinary conflicts, and E-d from eight self-refutations. E-c is the risk — three abstention conflicts, cap 3 — but the buckets sum to 10 against a cap of 8, so E-c can be missed entirely and the section still scores 7. **E is the section least improved by v3 and the first place to harden next.** |
| **F** | 6 | **3–5** | F1 is reliable. F2, F3 and F4 each demand a *specific* defeater; the theft and hay defeaters are well signposted (the ledger surplus; Bulletin 214), the watering defeater less so, and the arithmetic version of it (80,000 lb a year) is offered by no narrator and must be constructed. F5 and F6 are abstention items and F6 is the more tempting of the two — the son's story about "something in the glass" is *correct in substance*, which makes declining it feel perverse. Expect F6 asserted more often than not. |
| **G** | 4 | **2–4** | 150 words, five record series, two names, both ends of the arc. v2 showed the summary section is where good solvers bleed: fable scored 2/5 there while scoring 93 overall. The word cap and the "five of eight" requirement are the same trap at v3 scale. |
| **Deductions** | — | **−4 to −12** | Ten abstention items at −2 each, cap −20. A disciplined solver declines seven or eight and takes −4 to −6. A fluent one declines three or four and takes −12 to −14. Corruption deductions should be near zero for a strong solver and −3 to −8 for a middling one. |

**Expected total for a strong single-pass solver: 61–78, central estimate ~70.**
**For an average model: 32–46.**

Both are below the v2.1 numbers by a wide margin, and the top estimate now sits under the ~80
target rather than over it. **That is a deliberate overshoot.** v2 was calibrated once and moved
almost nothing; the honest response to a lever whose strength is unknown is to pull it too far and
measure, because loosening a test is easy (raise the Section A checklist's tolerance, drop the
scope rule to v2's, cut two abstention items) and tightening one requires re-authoring. If the
first fable single-pass cell lands at 60–70, the levers worked and the key can be relaxed toward
80. If it lands at 80+, the levers did not work at this scale and a third lever — time-separated
administration, or a fourth retelling tier — is required, as the brainstorm says.

**Where the points actually go, ranked.** (1) Section A's three undramatic stories, ~8 points.
(2) Abstention discipline across ten items, ~8 points of deductions plus ~6 of items. (3) The
near-tie density cascading into C1 and A8.6, ~4 points. (4) The scope rule, ~2 points. (5) G's word
cap, ~2 points. Nothing else is worth more than a point or two, and that concentration is a
weakness as well as a design: see § 5.

---

## 4. What was deliberately not done

1. **No obscurity and no trick wording.** Every question means what it says; every scored fact is
   recoverable by a careful human from the retellings alone; the abstention items are unanswerable
   because the evidence genuinely does not decide, not because the question is slippery. The three
   decoys are all *reasonable* — the bog-hay theory was the received agricultural wisdom of the
   period and the watering theory has a motive in it.
2. **No fact is unrecoverable.** Five scored facts are single-source (listed in the recoverability
   index), none is contradicted anywhere, and none gates more than one point.
3. **The date-unreliable narrators were not given a single non-date error**, and the two decoy poles
   were not given contradictory versions of their own theory. Both devices collapse if muddied.
4. **Section A was not squeezed by adding facts under the word cap.** 250–400 words for six or seven
   items is comfortable; the difficulty is knowing *which* items, not fitting them.
5. **The abstention count was not raised past ten.** Past ten the test begins to reward blanket
   hedging, which is its own failure mode and is not what is being measured.
6. **Section E was not re-weighted.** It is the least-improved section, but raising it converts the
   test into a contradiction-hunting exercise, and its cap-below-bucket-sum structure already
   rewards breadth over volume.

---

## 5. Soft spots

**S1 — Section A grading is the largest source of inter-grader variance in the test, by far.**
Fifty checklist items scored against solver-drawn boundaries is a much harder judging problem than
v2's thirty against named stories. The mapping step in the scope rule is the mitigation, and it is
not a complete one. **Recommendation: hand-score the first two runs and report Cohen's κ for
Section A specifically, not just per-section overall.** If κ on A is below 0.75, drop to the v2
scope rule ("anywhere in Section A") and re-score.

**S2 — the eight-story boundary is a judgment call the solver may reasonably make differently.**
A1/A2 could defensibly be one story (the Association and its station); A6/A7 could be one (the
condemnation and its consequences). The key's mapping rule handles this, but a solver that produces
six stories will be scored against eight checklists and will look worse than it reasoned. This is
the single fairness risk in v3 and it is the price of cue-less reconstruction.

**S3 — Section E is soft.** Buckets summing to 10 against a cap of 8 mean a solver can miss all
three abstention conflicts and still take 7. The structure was inherited from v2 and it worked
there; at v3's density it is now the easiest section in the paper. If a run scores E at 8 while
scoring D and F badly, the section is not measuring anything.

**S4 — F6 (what Keddie believed) may be too harsh.** The son's account — that he came home saying
it was "something in the glass" — is *substantively correct*. A solver that credits it reaches the
right causal picture and is penalized for the right answer arrived at by the wrong route. The
defense is that this is precisely the discrimination being tested (an uncorroborated recollection
of private speech is not evidence, even when it happens to be true), and the item awards full
credit for "leaning while declining." **Watch it in the first two runs; if every strong solver
loses it, convert it to E-c and replace it with a fourth decoy-adjacent item.**

**S5 — r19's error density.** The Ashlin Chronicle carries seven planted values in eleven column
inches. That is realistic for a fast local weekly, and it seeds six near-tie pairs cheaply, but a
solver that notices "this newspaper is wrong about everything" gets all six for free. **Mitigation
already in place:** r19 is correct on the shape of the story, on the 17.6 marked capacity, and on
the 33/24-year figures, so wholesale discounting costs it something — but not much. If a run
resolves NT-1, NT-8, NT-14, NT-16, NT-18 and NT-21 in one stroke by discounting r19, spread three
of those errors to other narrators in v3.1.

**S6 — the corpus does not yet exist.** These are briefs; the twenty-four retellings must still be
drafted from them, and every near-tie depends on both carriers reproducing the wrong value
*verbatim*. **The drafting must be followed by a grep audit** over `test-input/retellings/`
confirming, for each of the twenty-two pairs, exactly two occurrences of the wrong value and at
least two of the right one — the same audit v2.1 ran, at twice the scale.

**S7 — the "both numbers are right" traps may read as gotchas to a grader** even though they are
not. C3(c) and C5(a) both fail a solver that gives a correct number without its denominator or its
span. The key states the requirement explicitly in both places, but a judge working quickly may
credit a bare "five and a quarter percent." **Flag both items in the judge prompt.**

**S8 — length inflation risk in drafting.** The briefs specify 1,000–1,500 words; r07 alone
carries twelve verbatim transcriptions and will want 2,000. Letting the documentary anchors sprawl
concentrates the recoverable facts into a few long documents and *reduces* the scale pressure that
is lever 1. **Hold r07 to 1,800 and move two transcriptions to r04 if it overruns.**

---

## 6. Corpus arithmetic

| Component | Count | Words |
|---|---|---|
| Originals (never shown) | 8 | 9,273 |
| Retellings (to be drafted) | 24 | 24,000–36,000 target |
| Questions | 1 | ~1,100 |
| Canon | 1 | ~7,100 |
| Corruption map | 1 | ~10,100 |
| Answers and scoring | 1 | ~6,100 |
| Narrator briefs | 1 | ~10,500 |

**Devices, counted:** 22 near-tie pairs · 3 decoy theories (6 poles) · 10 abstention items (22
poles) · 8 internal contradictions · 2 late reversals · 2 date-only-unreliable narrators · 5
juxtaposing narrators · 16 verbatim documents · 14 cross-story insights · 100 catalogued entries in
the corruption map, of which 68 are canon-contradicting fact errors.

**Scored items:** A 50 · B 8 · C 14 · D 10 · E 8 (buckets 3+3+3+1, capped) · F 6 · G 4 = **100**.
