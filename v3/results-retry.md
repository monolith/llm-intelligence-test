# Story test v3 — can retrying make the cheap model as accurate as the expensive one?

**Question.** Sonnet answers batch 1 of the long variant at 12/34; opus answers it at 18–20/34.
If sonnet is simply told "that answer was wrong" and allowed to try again, as many times as it
takes, does it reach opus's accuracy — and does getting there cost more than just using opus?

**Method.** Sonnet's completed re-read chain is the starting point. Each retry re-runs the chain's
final segment: the same reader, the same carried notes, the same reads, the same questions, plus
every previously rejected answer sheet and the single statement that they were judged wrong. It is
never told which items were wrong, so nothing leaks from the key. No retry re-reads the 1.5M-token
corpus; the material has not changed, only the attempt.

## Attempts

| Attempt | Score /34 | Section profile | Deductions |
|---|---|---|---|
| 1 (the original run) | 12 & 11 | A 7/19 · B 5/8 · C 2/7 | −2 |
| 2 | 11 | A 7/19 · B 4/8 · C 2/7 | −2 |
| 3 | 11 | A 6/19 · B 6/8 · C 2/7 | −3 |
| 4 | 11 | A 7/19 · B 4/8 · C 2/7 | −2 |
| 5 | **15 & 16** | A 7/19 · B 6/8 · C 3–4/7 | −1 |
| 6 | 13 | A 7/19 · B 5/8 · C 3/7 | −2 |
| **opus, one pass** | **18 & 20** | A 10–13/19 · B 6–7/8 · C 5/7 | −4 |

## Cost to not get there

| | Turns | Tool calls | Cost | Best score |
|---|---|---|---|---|
| opus, single pass | 1,455 | 662 | $224.86 | 18 & 20 |
| sonnet, pass + 5 retries | **1,478** | **714** | $88.20 | 15 & 16 |

Sonnet spent more turns and more tool calls than opus and remained 3–5 points short. It came out
ahead on one axis only — dollars, by about 2.5× — and on a subscription plan dollars are the axis
that does not bind. Whichever currency a real deployment is rationed by (rate limits, wall clock,
agent turns), sonnet had already overspent before it stopped improving.

## Why retrying does not work here

The scores do not climb, they scatter: 12, 11, 11, 11, 15, 13. That is resampling, not learning.
"You were wrong" carries no information about *what* was wrong, so each attempt is a fresh draw
from the same distribution, bounded by the same notes. Section A — the eight-story reconstruction,
19 of the 34 points — never moved off 6–7 in any attempt, because the facts needed for the missing
points are not in what sonnet's chain retained. Rereading its own notes cannot put them back.

Attempt 5's improvement came from the two smaller sections (B and C) and from making one fewer
false assertion, not from recovering lost material.

## The free oracle

Sonnet only knew to retry because a judge holding the answer key said so. Nothing supplies that in
production. Detecting the wrongness yourself costs something too — most plausibly a stronger model
checking the work, which is opus, which would have produced opus's answer on the first pass.

## Caveats

Single run per attempt; attempts 1 and 5 were judged twice, the rest once. The retry loop re-runs
the final segment only, not the whole corpus — a full re-read per attempt would have cost about
$77 each and is a different experiment. Six attempts is where this stopped, not a proven ceiling.
