# What we tested, and what we found — for someone new to all this

You are looking at the results of a reading test given to four AI language models. This page
explains what the test is, why it was built the way it was, what the numbers mean, and what we
learned. No background in AI is assumed. Where a technical word is unavoidable it is explained
the first time it appears.

---

## 1. Three words you need

**Model.** A language model is a program that reads text and writes text back. The four tested
here — Haiku, Sonnet, Opus and Fable — are four sizes of the same family, from smallest and
cheapest to largest and most expensive. Think of four employees at four pay grades.

**Context.** A model can only "see" a limited amount of text at once — its context. Everything it
is currently reading and everything it has recently written has to fit in that space. Once the
space is full, something has to go. The largest models here can hold roughly a million words'
worth; that sounds like a lot until you hand one a filing cabinet.

**Compaction.** When the context fills up, the model (or the software running it) squeezes what
it has read into a shorter summary and carries on from the summary. The original text is gone;
only the summary remains. This is compaction. It is the single most important idea on this page,
because everything we found turns on what survives it.

An everyday picture: a night watchman reads the day's incident reports, and at the end of his
shift writes a handover note for the next watchman, who never sees the reports themselves. Three
shifts later, if something is missing, it went missing in a handover note.

---

## 2. The test

We wrote a history — eight interlocking stories about a farming valley a century ago: a dairy
cooperative, a testing scandal, an arbitration, a family feud. The stories are original; they
exist nowhere on the internet, so no model could have memorized them.

Then we had **twenty-four narrators retell** that history. Each narrator knew only part of it.
Each got some things right and some things wrong. Several ran different stories together. And we
planted specific false claims in specific narrators — a wrong year here, a wrong dollar figure
there — so that a careful reader comparing the accounts could catch them.

The model is given the twenty-four retellings and **never the original eight stories.** Its job is
to work out what actually happened: reconstruct the eight stories, resolve the contradictions
between narrators, compute a few figures from the numbers scattered across the accounts, and —
this matters — say "the sources don't settle this" where they genuinely don't.

A hundred-point answer key scores it. Points are lost for **asserting a planted error as fact.**
Hedging ("one account says X, but the ledger says Y") is fine; confident repetition of a lie costs
a point. So the test rewards care, not just recall.

### Two sizes

**Short.** All twenty-four retellings together are about 37,000 words. That fits in one context
with room to spare. This measures how well the model reasons when it can see everything.

**Long.** The same twenty-four retellings, but eight of them are buried inside 62,000-word
documents of unrelated filler, and four further noise documents of 220,000 words each are dropped
in between — old ledgers, transcripts of overheard chatter, nonsense prose. About 1.5 million
words in total. **This cannot fit.** The model has to read it in pieces and compact as it goes. This
measures what survives.

That contrast — same questions, same material, one version fits and one doesn't — is the whole
design.

---

## 3. What we found

### Finding 1 — When everything fits, you get what you pay for

Short version, scored out of 100, mean of three runs each (two graders per run):

| | Haiku | Sonnet | Opus | Fable |
|---|---|---|---|---|
| all at once | 45 | 63 | 79 | 84 |
| delivered one document at a time | 51 | 64 | 76 | 82 |
| with unrelated documents mixed in | 51 | 63 | 76 | 82 |

Bigger model, better score, roughly in proportion to price. Fable, the most expensive, nearly
doubles Haiku, the cheapest. The order never changed across nine administrations, with one
exception: Opus beat Fable once, by one point. No surprises.

### Finding 2 — When it doesn't fit, everyone collapses

Same models, same material, long version:

| | Haiku | Sonnet | Opus |
|---|---|---|---|
| after compaction | 6 | 23 | 26 |

Every model lost between two-thirds and seven-eighths of its score. The largest effect in the
entire study is not which model you choose — it is whether the material fits. **Haiku with
everything in view (45) beats Opus after compaction (26).**

If you take one practical thing from this page: making the material fit is worth more than
upgrading the model.

### Finding 3 — They don't get vague, they get confidently wrong

You might expect a model that has lost most of what it read to say "I'm not sure." That is not
what happens. In the long version, every model lost heavily to the penalty for stating planted
errors as fact. Haiku's third batch earned ten points and lost eleven, ending at zero.

The same models, given the same material in the short version, had correctly hedged on those same
errors. After compaction they no longer had the evidence — and asserted the error anyway, at full
confidence. There is nothing on the surface of the answer to tell you which claims are which.

### Finding 4 — The cheap model isn't cheap when the work is hard

Cost per correct point (API prices; on a subscription plan the currency is turns, and the picture
is the same):

| | Short version | Long version |
|---|---|---|
| Haiku | $0.012 per point | **$6.83 per point** |
| Sonnet | $0.049 | **$3.58** |
| Opus | $0.063 | $9.42 |

When the work fits, Haiku is by far the best value. When it doesn't, the ordering **inverts**:
Haiku costs nearly twice as much per correct point as Sonnet. It needed 35 reading passes to
Sonnet's 21 for the identical material, because its usable working space is smaller — and then
scored a quarter as much.

### Finding 5 — You can't fix it by trying again

We took Sonnet's answers and told it they were wrong, in three different ways: "the whole sheet
is wrong, try again"; "these specific questions are wrong"; and inside one continuous session
with the material still partly in view. Six attempts, four rounds, and two rounds respectively.

It never reached Opus's score. In two of the three, it got *worse*, because each revision added
text and each addition was another chance to assert a planted error. And by the time it had
retried enough, it had spent more turns and more tool calls than Opus used to get the right
answer the first time.

The ceiling isn't effort. When asked directly about the figures it kept getting wrong, Sonnet said
"cannot be determined" — the numbers hadn't survived its compaction, and no amount of retrying puts
them back.

### Finding 6 — Reading is expensive; asking is nearly free

Sonnet read the entire 1.5-million-word corpus in one sitting: about $158 and 1,300 turns. Asking
it a follow-up question afterwards cost $0.77 and 3 turns.

Two hundred to one. Any system that pays the reading cost once and stays available to answer
questions is attacking the right half of the bill.

---

## 4. How to read a number like "83 & 81"

Every answer sheet was marked by **two independent graders**, each holding the answer key,
neither seeing the other's marks. "83 & 81" means grader one gave 83 and grader two gave 81. Where
one number is shown, they agreed.

The gap between the two graders is the marking error bar. Across all twelve short cells it ranged
from 0 to 8 points out of 100. So: a 20-point difference between two models is real; a 5-point
difference is inside the noise.

**What that number does not tell you** is what happens if the same model takes the test a second
time. Models are not deterministic — the same question can get a somewhat different answer. So
the short version was run three times per cell. The three larger models landed within a few
points of themselves each time; Haiku did not — one of its administrations scored 64 once and 45
twice. The companion report `QUANT.md` gives every mean with its interval, so that claims like
"Opus beats Sonnet" carry an error bar instead of a single point (it is 13 points, give or take
4).

---

## 5. What we are not claiming

- **One run per cell** in the long version (the short version has three). The direction
  (collapse under compaction) is not in doubt — it is the largest effect in the study — but the
  exact numbers would move on a re-run.
- **One kind of task.** This is synthesis from unreliable sources with planted traps. A model
  that is bad at this may be fine at writing code or summarizing a memo.
- **One family of models**, at one moment in time. Version changes matter: an earlier Fable
  refused to complete the long version at all (an automated safety check misfired on it); the
  current one runs it fine.
- **Graders are also models.** Two Opus instances did the marking. They agree closely with each
  other and with a hand-scored sample, but they are not human graders.

---

## 6. How to run it yourself

Everything needed is in this repository, and none of it requires our scripts. A person with a
chat window can repeat the short version in an afternoon.

The rule that makes results comparable: **the model gets the material and the questions, and
nothing else.** Never the answer key, never the original stories, never a hint about which
documents are noise.

**Short version, by hand:**
1. Paste the whole of `test-input/bundle-single.md` (retellings then questions) into one message.
   Ask for the answer sheet in three parts (Section A stories 1–4; stories 5–8 plus Section B;
   Sections C–G) — a single reply tends to get cut off.
2. Score it against `answer-key/answers-and-scoring.md`, item by item. Exact-match items take no
   near misses; abstention items score only if the answer abstains; every planted error asserted
   as fact costs a point. Have two people score independently and report both.

**Long version, by hand:** the same, but deliver the retellings one at a time in the order in
`distractors/ORDER.md`, with the distractors in between, using the 62,000-word versions in
`test-input/long/` for eight of them and the four noise documents in `distractors/long/` after r06,
r12, r18 and r24. Start a fresh chat whenever the current one is nearly full, carrying across only
what the model wrote down. Expect twenty or more restarts.

The full protocol, the scripts that automate it, and every mistake we made and fixed along the
way are in `harness/PROTOCOL-LONG.md`. The mistakes are documented on purpose: several of the
early numbers were wrong because of them, and a reader should be able to see exactly which.
