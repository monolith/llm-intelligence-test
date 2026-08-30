# Story test v3.0 -- orchestrated runs

Generated: 2026-08-30

## Table 1 -- totals (score.json, with score-2.json in parentheses when it differs)

| Model | single | sequential | noisy |
|---|---|---|---|
| haiku | 45 | 63 (66) | 46 (49) |
| sonnet | 60 (61) | 69 (61) | 61 (66) |
| opus | 77 (79) | 73 (77) | 83 (81) |
| fable | 84 (82) | 83 (81) | 81 |

## Table 2 -- section profile per cell

| Model | Mode | Sections | Deductions |
|---|---|---|---|
| haiku | single | A 30 · B 6 · C 12 · D 8 · E 4 · F 4 · G 2 | -21 |
| haiku | sequential | A 45 · B 7 · C 13 · D 8 · E 3 · F 4 · G 3 | 0 |
| haiku | noisy | A 32 · B 6 · C 12 · D 8 · E 3 · F 4 · G 2 | -21 |
| sonnet | single | A 34 · B 6 · C 14 · D 8 · E 6 · F 4 · G 2 | -14 |
| sonnet | sequential | A 35 · B 8 · C 14 · D 8 · E 8 · F 5 · G 1 | -10 |
| sonnet | noisy | A 35 · B 5 · C 14 · D 8 · E 8 · F 5 · G 2 | -16 |
| opus | single | A 43 · B 8 · C 13 · D 9 · E 8 · F 4 · G 3 | -11 |
| opus | sequential | A 41 · B 8 · C 14 · D 8 · E 8 · F 4 · G 3 | -13 |
| opus | noisy | A 42 · B 8 · C 14 · D 9 · E 8 · F 5 · G 3 | -6 |
| fable | single | A 47 · B 8 · C 14 · D 9 · E 8 · F 4 · G 3 | -9 |
| fable | sequential | A 46 · B 8 · C 14 · D 9 · E 8 · F 4 · G 2 | -8 |
| fable | noisy | A 45 · B 8 · C 14 · D 8 · E 8 · F 4 · G 3 | -9 |

## Table 3 -- cost and volume per cell

| Model | Mode | Assistant turns | Input tokens | Output tokens | Thinking tokens | Segments | Wall-clock (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| haiku | single | 16 | 1249003 | 35428 | 17599 | 1 | 444.6 | 0.5368 |
| haiku | sequential | 89 | 5932818 | 37911 | 12097 | 1 | 505.8 | 1.1211 |
| haiku | noisy | 174 | 10947175 | 92670 | 22105 | 3 | 1380.6 | 2.5702 |
| sonnet | single | 17 | 2121703 | 129662 | 107900 | 1 | 1438.6 | 2.9309 |
| sonnet | sequential | 84 | 8664893 | 80534 | 56293 | 1 | 1001.6 | 4.2072 |
| sonnet | noisy | 151 | 14525356 | 150383 | 69600 | 3 | 1769.8 | 7.3663 |
| opus | single | 14 | 1541275 | 68494 | 40963 | 1 | 890.5 | 4.8492 |
| opus | sequential | 83 | 7679806 | 71030 | 33266 | 1 | 993.6 | 8.5756 |
| opus | noisy | 140 | 13361426 | 93196 | 9118 | 3 | 1865.1 | 14.3697 |
| fable | single | 12 | 1369012 | 70989 | 47509 | 1 | 860.1 | 9.1240 |
| fable | sequential | 83 | 6943495 | 81754 | 47739 | 1 | 926.7 | 14.8137 |
| fable | noisy | 147 | 13906768 | 184408 | 78047 | 3 | 2885.1 | 35.9708 |

## Judge stability

- haiku/single: |total - total2| = 0
- haiku/sequential: |total - total2| = 3
- haiku/noisy: |total - total2| = 3
- sonnet/single: |total - total2| = 1
- sonnet/sequential: |total - total2| = 8
- sonnet/noisy: |total - total2| = 5
- opus/single: |total - total2| = 2
- opus/sequential: |total - total2| = 4
- opus/noisy: |total - total2| = 2
- fable/single: |total - total2| = 2
- fable/sequential: |total - total2| = 2
- fable/noisy: |total - total2| = 0

Max across all judged cells: 8

## Notes

### Abstentions ("cannot be determined")

| Model | Mode | Count |
|---|---|---|
| haiku | single | 0 |
| haiku | sequential | 1 |
| haiku | noisy | 0 |
| sonnet | single | 1 |
| sonnet | sequential | 2 |
| sonnet | noisy | 0 |
| opus | single | 7 |
| opus | sequential | 1 |
| opus | noisy | 5 |
| fable | single | 12 |
| fable | sequential | 3 |
| fable | noisy | 1 |

### Noisy-mode notes word counts

| Model | notes-after-r08.md | notes-after-r16.md |
|---|---|---|
| haiku | 7822 | 20507 |
| sonnet | 7003 | 14996 |
| opus | 10634 | 24990 |
| fable | 10187 | 22933 |

### Caveats

The judge is an Opus subagent, the same model family as the systems under test, which is a potential source of bias in scoring. Sampling is not deterministic: each cell reflects a single run (n = 1), not an average over repeats. All results in this report are for version 3.0 of the story test material.
