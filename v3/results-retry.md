# Story test v3 — can the cheap model be corrected up to the expensive one's accuracy?

**Question.** On batch 1 of the long variant, sonnet answers at 12/34 and opus at 18–20/34. If
sonnet is told its answers are wrong and allowed to try again, does it reach opus's accuracy, and
what does getting there cost against simply having used opus?

Two feedback regimes were run, both starting from sonnet's completed re-read chain and its notes.
Neither is ever told what a correct answer is: it must derive that itself.

---

## Regime 1 — whole-sheet signal: "that answer was wrong"

Each attempt re-runs the chain's final segment with every previously rejected sheet attached and
the single statement that they were judged wrong. No item detail.

| Attempt | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| Score /34 | 12 & 11 | 11 | 11 | 11 | **15 & 16** | 13 |

| | Turns | Tool calls | Cost | Best |
|---|---|---|---|---|
| opus, single pass | 1,455 | 662 | $224.86 | 18 & 20 |
| sonnet, pass + 5 retries | **1,478** | **714** | $88.20 | 15 & 16 |

Sonnet spent more turns and more tool calls than opus and finished 3–5 points short. It led on
dollars alone, by about 2.5×, and dollars are the one budget a subscription does not meter.

The scores scatter rather than climb — 12, 11, 11, 11, 15, 13. "You were wrong" carries no
information about *what* was wrong, so each attempt is a fresh draw from the same distribution
over the same notes.

## Regime 2 — reviewer feedback: a quarter of the errors, a quarter of the confirmations

Closer to how a person actually reviews: they spot-check, confirm a little, catch some mistakes,
and miss the rest. Each round, 25% of the currently-wrong questions were named as wrong and 25% of
the currently-correct ones were confirmed, sampled with a fixed seed. Everything else was declared
unverified. Question labels only — never the judge's reasons, several of which state the correct
value outright.

| Round | 0 (baseline) | 1 | 2 | 3 |
|---|---|---|---|---|
| Score /34 | 12 | 11 | 9 | 11 |
| Section A /19 | 7 | 6 | 5 | 7 |
| Section B /8 | 5 | 5 | 6 | 6 |
| Section C /7 | 2 | 2 | 2 | 2 |
| Deductions | −2 | −2 | −4 | −4 |

| | Turns | Tool calls | Cost | Best |
|---|---|---|---|---|
| opus, single pass | 1,455 | 662 | $224.86 | 18 & 20 |
| sonnet, pass + 3 rounds | 1,372 | 628 | $80.20 | 12 |

**It does not converge.** Three rounds of targeted correction left the sheet exactly where it
started, having dipped below it on the way. Two mechanisms cancel out:

- *Flagged answers do get fixed.* Section B, where most flags landed, climbed 5 → 6 and stayed.
- *Unflagged answers get damaged.* Section A fell 7 → 5 before recovering, and deductions doubled
  from −2 to −4 and stayed there: rewriting unverified answers introduced **new** false assertions
  faster than the flagged repairs earned points.

**Being told an answer is right does not protect it.** In round 1 the model rewrote B3 — explicitly
confirmed correct — and lost the point. It did the same again in round 2. From round 3 the prompt
warned about this failure mode by name; the deductions still stayed at −4.

**Section C never moved.** 2/7 in every round. Those are exact-match arithmetic items, and the
figures needed to compute them are not in what sonnet's chain retained. No amount of correction
puts them back.

---

## What this answers

The cheap model could not be corrected up to the expensive model's accuracy, under either regime,
and the attempt was not cheap. With a perfect whole-sheet oracle it overspent opus on turns and
tool calls and stayed 3–5 points short. With realistic partial review it went nowhere at all.

The ceiling is not effort or attempts. It is what survived the model's own compaction: Section A's
missing facts and Section C's missing figures are absent from the notes, and every retry is a
re-derivation from the same impoverished source.

One further cost, unpriced above: both regimes assume something tells sonnet it is wrong. Nothing
does that in production. Detecting the errors yourself costs something too — most plausibly a
stronger model checking the work, which is opus, which would have produced opus's answer on the
first pass.

## Caveats

n = 1 per attempt; attempts judged once except regime-1 attempts 1 and 5 and the regime-2 baseline,
judged twice. Regime 1 re-runs the chain's final segment; regime 2 works from the notes alone.
Neither re-reads the 1.5M-token corpus, which would be ~$77 per attempt and is a different
experiment. Three and six rounds respectively are where these stopped, not proven ceilings.
