# Story test 2.1 -- orchestrated runs

Generated: 2026-08-27

## Table 1 -- totals (score.json, with score-2.json in parentheses when it differs)

| Model | single | sequential | noisy |
|---|---|---|---|
| haiku | 57 (56) | 62 (63) | 54 (52) |
| sonnet | 76 (79) | 76 (77) | 81 |
| opus | 92 | 92 (94) | 86 |
| fable | 93 | 91 | 88 |

## Table 2 -- section profile per cell

| Model | Mode | Sections | Deductions |
|---|---|---|---|
| haiku | single | A 18 · B 8 · C 18 · D 12 · E 4 · F 7 · G 1 | -11 |
| haiku | sequential | A 21 · B 8 · C 16 · D 11 · E 5 · F 8 · G 3 | -10 |
| haiku | noisy | A 20 · B 5 · C 14 · D 12 · E 6 · F 8 · G 1 | -12 |
| sonnet | single | A 20 · B 8 · C 19 · D 14 · E 7 · F 8 · G 2 | -2 |
| sonnet | sequential | A 21 · B 8 · C 19 · D 13 · E 9 · F 10 · G 2 | -6 |
| sonnet | noisy | A 24 · B 10 · C 19 · D 11 · E 9 · F 10 · G 2 | -4 |
| opus | single | A 29 · B 10 · C 19 · D 15 · E 10 · F 10 · G 3 | -4 |
| opus | sequential | A 27 · B 10 · C 19 · D 14 · E 10 · F 10 · G 4 | -2 |
| opus | noisy | A 25 · B 9 · C 19 · D 15 · E 10 · F 10 · G 2 | -4 |
| fable | single | A 29 · B 10 · C 19 · D 15 · E 10 · F 10 · G 2 | -2 |
| fable | sequential | A 29 · B 10 · C 19 · D 13 · E 10 · F 10 · G 4 | -4 |
| fable | noisy | A 29 · B 10 · C 19 · D 12 · E 10 · F 10 · G 4 | -6 |

## Table 3 -- cost and volume per cell

| Model | Mode | Assistant turns | Input tokens | Output tokens | Thinking tokens | Segments | Wall-clock (s) | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| haiku | single | 9 | 520041 | 30537 | 18848 | 1 | 380.8 | 0.3436 |
| haiku | sequential | 44 | 2324877 | 29295 | 14071 | 1 | 526.1 | 0.5948 |
| haiku | noisy | 84 | 4409407 | 71413 | 29025 | 3 | 943.0 | 1.5172 |
| sonnet | single | 7 | 554262 | 57893 | 47314 | 1 | 659.6 | 1.1478 |
| sonnet | sequential | 39 | 2992191 | 69610 | 54234 | 1 | 848.7 | 1.9316 |
| sonnet | noisy | 79 | 6084156 | 130827 | 70413 | 3 | 1498.4 | 4.0641 |
| opus | single | 12 | 1067374 | 54525 | 31244 | 1 | 703.0 | 2.9112 |
| opus | sequential | 42 | 2944073 | 58000 | 34959 | 1 | 788.4 | 4.2637 |
| opus | noisy | 74 | 5449766 | 136225 | 60339 | 3 | 1732.7 | 10.0860 |
| fable | single | 8 | 576418 | 44176 | 29497 | 1 | 1286.5 | 5.0589 |
| fable | sequential | 42 | 2859223 | 71337 | 45736 | 1 | 1329.6 | 11.3332 |
| fable | noisy | 62 | 4128764 | 149900 | 74692 | 3 | 1639.5 | 23.6859 |

## Judge stability

- haiku/single: |total - total2| = 1
- haiku/sequential: |total - total2| = 1
- haiku/noisy: |total - total2| = 2
- sonnet/single: |total - total2| = 3
- sonnet/sequential: |total - total2| = 1
- sonnet/noisy: |total - total2| = 0
- opus/single: |total - total2| = 0
- opus/sequential: |total - total2| = 2
- opus/noisy: |total - total2| = 0
- fable/single: |total - total2| = 0
- fable/sequential: |total - total2| = 0
- fable/noisy: |total - total2| = 0

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
| sonnet | noisy | 2 |
| opus | single | 3 |
| opus | sequential | 2 |
| opus | noisy | 5 |
| fable | single | 1 |
| fable | sequential | 3 |
| fable | noisy | 2 |

### Noisy-mode notes word counts

| Model | notes-after-r04.md | notes-after-r08.md |
|---|---|---|
| haiku | 4454 | 10412 |
| sonnet | 6068 | 12543 |
| opus | 6879 | 16354 |
| fable | 6861 | 15909 |

### Caveats

The judge is an Opus subagent, the same model family as the systems under test, which is a potential source of bias in scoring. Sampling is not deterministic: each cell reflects a single run (n = 1), not an average over repeats. All results in this report are for version {label} of the story test material.
