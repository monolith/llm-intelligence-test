# Story test v3 — full scoresheet

Two judges per cell; `a & b` means the judges differed. Dollars are notional on a
subscription plan and are shown for API users; turns and tool calls are what a run
actually spends. Token counts include cache reads.

| Model | Variant | Round | Score | Tokens | Turns | Tool calls | Cost (USD) |
|---|---|---|---|---|---|---|---|
| haiku | short | single | 45/100 | 1.2M in / 35k out | 16 | 6 | $0.54 |
| haiku | short | sequential | 63 & 66 /100 | 5.9M in / 38k out | 89 | 29 | $1.12 |
| haiku | short | noisy | 46 & 49 /100 | 10.9M in / 93k out | 174 | 59 | $2.57 |
| sonnet | short | single | 60 & 61 /100 | 2.1M in / 130k out | 17 | 7 | $2.93 |
| sonnet | short | sequential | 69 & 61 /100 | 8.7M in / 81k out | 84 | 29 | $4.21 |
| sonnet | short | noisy | 61 & 66 /100 | 14.5M in / 150k out | 151 | 60 | $7.37 |
| opus | short | single | 77 & 79 /100 | 1.5M in / 68k out | 14 | 6 | $4.85 |
| opus | short | sequential | 73 & 77 /100 | 7.7M in / 71k out | 83 | 29 | $8.58 |
| opus | short | noisy | 83 & 81 /100 | 13.4M in / 93k out | 140 | 61 | $14.37 |
| fable | short | single | 84 & 82 /100 | 1.4M in / 71k out | 12 | 6 | $9.12 |
| fable | short | sequential | 83 & 81 /100 | 6.9M in / 82k out | 83 | 29 | $14.81 |
| fable | short | noisy | 81/100 | 13.9M in / 184k out | 147 | 62 | $35.97 |
| haiku | long / read once | ingest (35 segments) | — | 161.9M in / 759k out | 1800 | 585 | $40.14 |
| haiku | long / read once | batch 1 | 4 & 5 /34 | 0.7M in / 8k out | 14 | 4 | $0.26 |
| haiku | long / read once | batch 2 | 2 & 3 /35 | 0.7M in / 11k out | 14 | 4 | $0.28 |
| haiku | long / read once | batch 3 | 0/31 | 0.7M in / 12k out | 14 | 4 | $0.28 |
| sonnet | long / read once | ingest (21 segments) | — | 190.8M in / 819k out | 1110 | 502 | $79.12 |
| sonnet | long / read once | batch 1 | 5 & 6 /34 | 1.1M in / 36k out | 13 | 5 | $1.03 |
| sonnet | long / read once | batch 2 | 4/35 | 1.0M in / 39k out | 12 | 5 | $1.11 |
| sonnet | long / read once | batch 3 | 14/31 | 1.0M in / 35k out | 12 | 6 | $1.01 |
| opus | long / read once | ingest (23 segments) | — | 210.4M in / 1117k out | 1318 | 583 | $239.32 |
| opus | long / read once | batch 1 | 10 & 11 /34 | 0.8M in / 18k out | 11 | 5 | $1.80 |
| opus | long / read once | batch 2 | 10 & 7 /35 | 0.8M in / 22k out | 11 | 5 | $1.93 |
| opus | long / read once | batch 3 | 6/31 | 0.8M in / 21k out | 11 | 5 | $1.89 |
| fable | long / read once | ingest (24 segments) | — | 264.7M in / 987k out | 1222 | 791 | $955.81 |
| fable | long / read once | batch 1 | 29 & 28 /34 | 4.4M in / 40k out | 39 | 31 | $18.61 |
| fable | long / read once | batch 2 | 16 & 17 /35 | 13.9M in / 42k out | 95 | 81 | $45.91 |
| fable | long / read once | batch 3 | 23 & 21 /31 | 4.0M in / 51k out | 37 | 28 | $22.43 |
| haiku | long / re-read | batch 1 (35 segments) | 3/34 | 181.0M in / 316k out | 2207 | 716 | $35.05 |
| haiku | long / re-read | batch 2 | not run | — | — | — | — |
| haiku | long / re-read | batch 3 | not run | — | — | — | — |
| sonnet | long / re-read | batch 1 (21 segments) | 12 & 11 /34 | 218.9M in / 546k out | 1350 | 616 | $76.55 |
| sonnet | long / re-read | batch 2 | not run | — | — | — | — |
| sonnet | long / re-read | batch 3 | not run | — | — | — | — |
| opus | long / re-read | batch 1 (23 segments) | 18 & 20 /34 | 222.5M in / 883k out | 1455 | 662 | $224.86 |
| opus | long / re-read | batch 2 | not run | — | — | — | — |
| opus | long / re-read | batch 3 | not run | — | — | — | — |
| fable | long / re-read | batch 1 | not run | — | — | — | — |
| fable | long / re-read | batch 2 | not run | — | — | — | — |
| fable | long / re-read | batch 3 | not run | — | — | — | — |
