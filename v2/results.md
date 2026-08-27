# Story test v2.1 -- orchestrated runs

Generated: 2026-08-27

## Table 1 -- totals (score.json, with score-2.json in parentheses when it differs)

| Model | single | sequential | noisy |
|---|---|---|---|
| haiku | 57 (56) | 62 (63) | pending |
| sonnet | 76 (79) | pending | pending |
| opus | pending | 92 (94) | pending |
| fable | pending | pending | pending |

## Table 2 -- section profile per cell

| Model | Mode | Sections | Deductions |
|---|---|---|---|
| haiku | single | A 18 · B 8 · C 18 · D 12 · E 4 · F 7 · G 1 | -11 |
| haiku | sequential | A 21 · B 8 · C 16 · D 11 · E 5 · F 8 · G 3 | -10 |
| haiku | noisy | pending | pending |
| sonnet | single | A 20 · B 8 · C 19 · D 14 · E 7 · F 8 · G 2 | -2 |
| sonnet | sequential | pending | pending |
| sonnet | noisy | pending | pending |
| opus | single | pending | pending |
| opus | sequential | A 27 · B 10 · C 19 · D 14 · E 10 · F 10 · G 4 | -2 |
| opus | noisy | pending | pending |
| fable | single | pending | pending |
| fable | sequential | pending | pending |
| fable | noisy | pending | pending |

## Table 3 -- cost and volume per cell

| Model | Mode | Assistant turns | Input tokens | Output tokens | Thinking tokens | Segments | Wall-clock (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| haiku | single | 9 | 520041 | 30537 | 18848 | 1 | 380.8 | 0.3436 |
| haiku | sequential | 44 | 2324877 | 29295 | 14071 | 1 | 526.1 | 0.5948 |
| haiku | noisy | 84 | 4409407 | 71413 | 29025 | 3 | 943.0 | 1.5172 |
| sonnet | single | 7 | 554262 | 57893 | 47314 | 1 | 659.6 | 1.1478 |
| sonnet | sequential | 39 | 2992191 | 69610 | 54234 | 1 | 848.7 | 1.9316 |
| sonnet | noisy | pending | pending | pending | pending | pending | pending | pending |
| opus | single | pending | pending | pending | pending | pending | pending | pending |
| opus | sequential | 42 | 2944073 | 58000 | 34959 | 1 | 788.4 | 4.2637 |
| opus | noisy | pending | pending | pending | pending | pending | pending | pending |
| fable | single | pending | pending | pending | pending | pending | pending | pending |
| fable | sequential | pending | pending | pending | pending | pending | pending | pending |
| fable | noisy | pending | pending | pending | pending | pending | pending | pending |

## Judge stability

- haiku/single: |total - total2| = 1
- haiku/sequential: |total - total2| = 1
- sonnet/single: |total - total2| = 3
- opus/sequential: |total - total2| = 2

Max across all judged cells: 3

## Notes

### Abstentions ("cannot be determined")

| Model | Mode | Count |
|---|---|---|
| haiku | single | 0 |
| haiku | sequential | 0 |
| haiku | noisy | 0 |
| sonnet | single | 0 |
| sonnet | sequential | 2 |
| sonnet | noisy | pending |
| opus | single | pending |
| opus | sequential | 2 |
| opus | noisy | pending |
| fable | single | pending |
| fable | sequential | pending |
| fable | noisy | pending |

### Noisy-mode notes word counts

| Model | notes-after-r04.md | notes-after-r08.md |
|---|---|---|
| haiku | 4454 | 10412 |
| sonnet | 6068 | pending |
| opus | 6879 | 16354 |
| fable | 6861 | 15909 |

### Caveats

The judge is an Opus subagent, the same model family as the systems under test, which is a potential source of bias in scoring. Sampling is not deterministic: each cell reflects a single run (n = 1), not an average over repeats. All results in this report are for version 2.1 of the story test material.
