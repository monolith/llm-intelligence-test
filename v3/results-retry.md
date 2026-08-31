# Story test v3 — can the cheap model be corrected up to the expensive one's accuracy?

**Question.** On batch 1 of the long variant, sonnet answers at 12–14 out of 34 and opus at 18–20.
If sonnet is told its answers are wrong and allowed to try again, does it reach opus's accuracy,
and what does getting there cost against simply having used opus?

Three correction regimes were run. None ever reveals a correct answer: the model must derive it.

---

## The three regimes

**1. Whole-sheet signal.** Re-run the final segment of sonnet's re-read chain with every rejected
sheet attached and the single statement that they were wrong. No item detail.

**2. Reviewer feedback, working from handover notes.** Each round, 25% of the currently-wrong
questions named as wrong and 25% of the correct ones confirmed, sampled with a fixed seed;
everything else declared unverified. Question labels only — never the judge's reasons, several of
which state the correct value outright.

**3. Reviewer feedback, inside one continuous session.** The same 25%/25% feedback, but the model
read the whole 1.5M-token corpus in a single live session — no handover notes of ours at all, the
model's own compaction doing the forgetting — and revised inside that same session without
re-reading. Confirmed from the raw transcript: **it compacted five times**, peaking at 929,056
tokens of context before each.

## Scores

| Regime | Round 0 | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|---|
| 1 — whole-sheet | 12 & 11 | 11 | 11 | 11 | **15 & 16** | 13 |
| 2 — reviewer, from notes | 12 | 11 | 9 | 11 | | |
| 3 — reviewer, live session | **14** | 8 | | | | |
| opus, one pass | 18 & 20 | | | | | |

## Cost

| | Turns | Tool calls | Cost | Best score |
|---|---|---|---|---|
| opus, chained readers + notes | 1,455 | 662 | $224.86 | 18 & 20 |
| sonnet, chained + notes | 1,350 | 616 | $76.55 | 12 & 11 |
| sonnet, regime 1 (pass + 5 retries) | **1,478** | **714** | $88.20 | 15 & 16 |
| sonnet, regime 2 (pass + 3 rounds) | 1,372 | 628 | $80.20 | 12 |
| sonnet, one live session | 1,293 | 546 | $158.45 | **14** |
| — its correction round | +3 | +1 | +$0.77 | 8 |

## What the three regimes agree on

**Correction does not converge.** Not once, in any regime, did sonnet approach 18. Regime 1
scattered (12, 11, 11, 11, 15, 13). Regime 2 returned to its start after dipping below it. Regime 3
fell from 14 to 8 in a single round.

**Revision costs more than it earns.** The mechanism is visible in the deductions, which rise every
time: regime 2 went −2 → −4, regime 3 went −4 → −7. Asked to revise, the model *expands*. In regime
3 it reported changing two answers; the sheet grew by 600 words, with 18 lines removed and 31 added.
Every added sentence is another opportunity to assert one of the planted errors, and this test
charges for that.

**Being told an answer is correct does not protect it.** In regime 2 the model twice rewrote an
answer that had been explicitly confirmed right, and lost the point — the second time after being
warned about that exact failure by name.

**Some points are simply gone.** Section C sat at 2/7 through every round of regime 2, and when
asked directly the model answered "cannot be determined" after searching for the figures. They did
not survive compaction, and no amount of retrying recovers them.

**The cheap model overspends the expensive one before it gets close.** Regime 1 exceeded opus on
turns (1,478 v 1,455) and tool calls (714 v 662) while still 3–5 points short. Dollars were the
only budget sonnet led on — and dollars are what a subscription does not meter.

## A separate finding: natural compaction beat our handover notes

Sonnet scored **14** reading the corpus in one live session and letting the harness compact it,
against **12** for the same model reading the same corpus through chained fresh readers passing
written notes. The notes design was ours; compaction is what actually happens. On this evidence the
notes construct was costing the model about two points, and the single-session condition is the
more faithful measurement.

It is not cheaper, though: the live session cost $158.45 against $76.55 for the chained version,
because a 900k-token context is re-sent on every turn where fresh readers start cheap each time.
Correction inside it, by contrast, is nearly free — $0.77 and 3 turns — since the reading is
already paid for.

## The unpriced cost

Every regime assumes something tells sonnet it is wrong. Nothing does that in production.
Detecting the errors costs something too — most plausibly a stronger model checking the work, which
is opus, which would have produced opus's answer on the first pass.

## Caveats

n = 1 per attempt; most attempts judged once, the regime-1 baseline and best attempt judged twice.
Regimes 1 and 2 work from a notes artifact rather than the sources; regime 3 does not, which is why
it is the more trustworthy of the three. Rounds stopped where they stopped; none is a proven ceiling.
