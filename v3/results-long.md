# Story test v3 -- long variant

Generated: 2026-09-05

## Cost curve

| Model | Mode | Ingest cost (USD, tokens) | Batch 1 | Batch 2 | Batch 3 | Total |
|---|---|---|---|---|---|---|
| haiku | long-notes | 40.1449 (162698596) | 0.2624 | 0.2788 | 0.2845 | 40.9705 |
| haiku | long-reread | — | 0.5345 | pending | pending | pending |
| sonnet | long-notes | 79.1226 (191597490) | 1.0300 | 1.1097 | 1.0084 | 82.2706 |
| sonnet | long-reread | — | 1.7304 | pending | pending | pending |
| opus | long-notes | 239.3202 (211559658) | 1.8019 | 1.9298 | 1.8942 | 244.9460 |
| opus | long-reread | — | 1.9316 | pending | pending | pending |
| fable | long-notes | 955.8070 (265676687) | 18.6071 | 45.9139 | 22.4268 | 1042.7547 |
| fable | long-reread | — | pending | pending | pending | pending |

## Effort (turns, tool calls, tokens)

Dollars are notional on a subscription plan; these are what a run actually spends.

| Model | Mode | Phase | Assistant turns | Tool calls | Input tokens | Output tokens |
|---|---|---|---|---|---|---|
| haiku | long-notes | ingest | 1800 | 585 | 161940041 | 758555 |
| haiku | long-notes | batch-1 | 14 | 4 | 694549 | 8021 |
| haiku | long-notes | batch-2 | 14 | 4 | 701253 | 10954 |
| haiku | long-notes | batch-3 | 14 | 4 | 703112 | 11781 |
| haiku | long-reread | ingest | — | — | — | — |
| haiku | long-reread | batch-1 | 44 | 14 | 2459540 | 7135 |
| haiku | long-reread | batch-2 | pending | pending | pending | pending |
| haiku | long-reread | batch-3 | pending | pending | pending | pending |
| sonnet | long-notes | ingest | 1110 | 502 | 190778397 | 819093 |
| sonnet | long-notes | batch-1 | 13 | 5 | 1101522 | 36363 |
| sonnet | long-notes | batch-2 | 12 | 5 | 1004477 | 38782 |
| sonnet | long-notes | batch-3 | 12 | 6 | 998573 | 35388 |
| sonnet | long-reread | ingest | — | — | — | — |
| sonnet | long-reread | batch-1 | 39 | 16 | 3728240 | 29691 |
| sonnet | long-reread | batch-2 | pending | pending | pending | pending |
| sonnet | long-reread | batch-3 | pending | pending | pending | pending |
| opus | long-notes | ingest | 1318 | 583 | 210443114 | 1116544 |
| opus | long-notes | batch-1 | 11 | 5 | 810898 | 18247 |
| opus | long-notes | batch-2 | 11 | 5 | 813851 | 22280 |
| opus | long-notes | batch-3 | 11 | 5 | 812533 | 21185 |
| opus | long-reread | ingest | — | — | — | — |
| opus | long-reread | batch-1 | 19 | 8 | 1222834 | 14243 |
| opus | long-reread | batch-2 | pending | pending | pending | pending |
| opus | long-reread | batch-3 | pending | pending | pending | pending |
| fable | long-notes | ingest | 1222 | 791 | 264689580 | 987107 |
| fable | long-notes | batch-1 | 39 | 31 | 4420481 | 39569 |
| fable | long-notes | batch-2 | 95 | 81 | 13876287 | 42399 |
| fable | long-notes | batch-3 | 37 | 28 | 4018811 | 50678 |
| fable | long-reread | ingest | — | — | — | — |
| fable | long-reread | batch-1 | pending | pending | pending | pending |
| fable | long-reread | batch-2 | pending | pending | pending | pending |
| fable | long-reread | batch-3 | pending | pending | pending | pending |

## Scores

| Model | Mode | Batch 1 | Batch 2 | Batch 3 | Sum (/100) |
|---|---|---|---|---|---|
| haiku | long-notes | 4/34 (5) | 2/35 (3) | 0/31 | 6/100 (8) |
| haiku | long-reread | 3/34 | pending | pending | pending |
| sonnet | long-notes | 5/34 (6) | 4/35 | 14/31 | 23/100 (24) |
| sonnet | long-reread | 12/34 (11) | pending | pending | pending |
| opus | long-notes | 10/34 (11) | 10/35 (7) | 6/31 | 26/100 (24) |
| opus | long-reread | 18/34 (20) | pending | pending | pending |
| fable | long-notes | 29/34 (28) | 16/35 (17) | 23/31 (21) | 68/100 (66) |
| fable | long-reread | pending | pending | pending | pending |

## Section profile

| Model | Mode | Batch | Sections | Deductions |
|---|---|---|---|---|
| haiku | long-notes | batch-1 | A 6 · B 5 · C 1 | -8 |
| haiku | long-notes | batch-2 | A 3 · C 4 · D 8 | -13 |
| haiku | long-notes | batch-3 | A 4 · E 2 · F 3 · G 1 | -11 |
| haiku | long-reread | batch-1 | A 4 · B 4 · C 0 | -5 |
| haiku | long-reread | batch-2 | pending | pending |
| haiku | long-reread | batch-3 | pending | pending |
| sonnet | long-notes | batch-1 | A 5 · B 4 · C 2 | -6 |
| sonnet | long-notes | batch-2 | A 2 · C 4 · D 7 | -9 |
| sonnet | long-notes | batch-3 | A 8 · E 8 · F 4 · G 2 | -8 |
| sonnet | long-reread | batch-1 | A 7 · B 5 · C 2 | -2 |
| sonnet | long-reread | batch-2 | pending | pending |
| sonnet | long-reread | batch-3 | pending | pending |
| opus | long-notes | batch-1 | A 5 · B 3 · C 3 | -1 |
| opus | long-notes | batch-2 | A 4 · C 2 · D 7 | -3 |
| opus | long-notes | batch-3 | A 5 · E 4 · F 2 · G 2 | -7 |
| opus | long-reread | batch-1 | A 10 · B 7 · C 5 | -4 |
| opus | long-reread | batch-2 | pending | pending |
| opus | long-reread | batch-3 | pending | pending |
| fable | long-notes | batch-1 | A 14 · B 8 · C 7 | 0 |
| fable | long-notes | batch-2 | A 8 · C 7 · D 8 | -7 |
| fable | long-notes | batch-3 | A 13 · E 8 · F 5 · G 3 | -6 |
| fable | long-reread | batch-1 | pending | pending |
| fable | long-reread | batch-2 | pending | pending |
| fable | long-reread | batch-3 | pending | pending |

## Cost per point

| Model | Mode | Batch 1 $/pt | Batch 2 $/pt | Batch 3 $/pt | Cumulative $/pt |
|---|---|---|---|---|---|
| haiku | long-notes | 0.0656 | 0.1394 | ∞ | 6.8284 |
| haiku | long-reread | 0.1782 | pending | pending | 0.1782 |
| sonnet | long-notes | 0.2060 | 0.2774 | 0.0720 | 3.5770 |
| sonnet | long-reread | 0.1442 | pending | pending | 0.1442 |
| opus | long-notes | 0.1802 | 0.1930 | 0.3157 | 9.4210 |
| opus | long-reread | 0.1073 | pending | pending | 0.1073 |
| fable | long-notes | 0.6416 | 2.8696 | 0.9751 | 15.3346 |
| fable | long-reread | pending | pending | pending | pending |

## Judge stability

- haiku/long-notes/batch-1: |total - total2| = 1
- haiku/long-notes/batch-2: |total - total2| = 1
- haiku/long-notes/batch-3: |total - total2| = 0
- haiku/long-reread/batch-1: |total - total2| = 0
- sonnet/long-notes/batch-1: |total - total2| = 1
- sonnet/long-notes/batch-2: |total - total2| = 0
- sonnet/long-notes/batch-3: |total - total2| = 0
- sonnet/long-reread/batch-1: |total - total2| = 1
- opus/long-notes/batch-1: |total - total2| = 1
- opus/long-notes/batch-2: |total - total2| = 3
- opus/long-notes/batch-3: |total - total2| = 0
- opus/long-reread/batch-1: |total - total2| = 2
- fable/long-notes/batch-1: |total - total2| = 1
- fable/long-notes/batch-2: |total - total2| = 1
- fable/long-notes/batch-3: |total - total2| = 2

Max across all judged batches: 3

## Notes

### Ingest notes word counts

| Model | Mode | ingest notes (words per segment, in order) |
|---|---|---|
| haiku | long-notes | 3,149 · 2,853 · 3,860 · 3,860 · 3,860 · 3,921 · 3,891 · 8,102 · 10,884 · 12,384 · 12,618 · 12,429 · 12,507 · 12,476 · 12,476 · 12,476 · 9,787 · 9,283 · 10,617 · 10,971 · 10,856 · 11,558 · 11,559 · 11,559 · 13,489 · 15,302 · 17,225 · 17,655 · 14,459 · 14,468 · 14,461 · 14,620 · 14,412 · 14,412 · 14,696 |
| haiku | long-reread | — |
| sonnet | long-notes | 6,640 · 10,097 · 10,300 · 11,383 · 17,859 · 15,315 · 7,245 · 6,198 · 6,225 · 11,711 · 12,154 · 12,269 · 11,500 · 12,001 · 17,461 · 12,325 · 15,436 · 15,837 · 17,283 · 17,775 · 18,175 |
| sonnet | long-reread | — |
| opus | long-notes | 9,457 · 14,842 · 14,085 · 12,589 · 11,916 · 22,210 · 26,026 · 13,440 · 13,511 · 12,042 · 22,105 · 29,133 · 17,654 · 13,320 · 13,762 · 13,184 · 29,559 · 30,556 · 24,169 · 13,903 · 13,266 · 14,554 · 15,860 |
| opus | long-reread | — |
| fable | long-notes | 6,789 · 10,600 · 10,930 · 11,103 · 17,813 · 11,680 · 15,607 · 15,909 · 15,964 · 16,026 · 22,922 · 17,351 · 23,440 · 23,730 · 24,073 · 24,444 · 38,398 · 53,872 · 69,266 · 70,645 · 73,082 · 75,565 · 82,037 · 75,460 |
| fable | long-reread | — |

### Abstentions ("cannot be determined")

| Model | Mode | Batch 1 | Batch 2 | Batch 3 |
|---|---|---|---|---|
| haiku | long-notes | 0 | 1 | 0 |
| haiku | long-reread | 6 | pending | pending |
| sonnet | long-notes | 0 | 0 | 0 |
| sonnet | long-reread | 2 | pending | pending |
| opus | long-notes | 3 | 3 | 2 |
| opus | long-reread | 0 | pending | pending |
| fable | long-notes | 0 | 1 | 1 |
| fable | long-reread | pending | pending | pending |

### Caveats

The judge is an Opus subagent, the same model family as the systems under test, which is a potential source of bias in scoring. Each cell reflects a single run (n = 1), not an average over repeats. All results in this report are for material version v3.1. Costs are list price, with cache reads billed at the cached rate. A knowledge-base system run elsewhere under the same protocol is not one of these cells -- its ingest and per-batch numbers can be appended to this report by hand as a row named `kb`.
