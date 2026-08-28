#!/usr/bin/env python3
"""gen_long_noise.py -- procedural generator for very long, meaning-free noise
documents used to fill an LLM's context window for v3 of the synthesis test.

Purpose
-------
Produce large (5,000 to 400,000+ word) markdown documents that are fluent and
plausible in register but carry no information relevant to the actual test
material (the "canon" of v3/answer-key/canon.md and the eight retellings).
The generated text competes for a model's attention the way a huge pile of
unrelated paperwork would, so that context compaction and retrieval can be
stress-tested at scale.

Design constraints
-------------------
* Standard library only. No network calls, no LLM calls -- generation must be
  free and fast.
* Deterministic: the same --seed always produces byte-identical output for a
  given --kind/--words combination.
* Streamed to disk: never holds the whole document in memory, so a
  300,000-word file generates in well under a minute using modest memory.
* Collision-safe: every invented proper noun, and every "distinctive" number
  or date the generator draws, is checked against a collision list built
  from v3/answer-key/canon.md (or any other file passed via --collisions)
  and re-drawn if it matches. This is a real, load-bearing check -- see
  tests/test_gen_long_noise.py for cases that force a collision and confirm
  it is avoided, not just "unlikely by chance".

Kinds
-----
ledger      -- a day-book of an invented business: dated lines with items,
               prices and running totals that actually add up, plus
               occasional narrative notes.
transcript  -- overheard conversation among named speakers: digressive,
               slot-filled sentences about objects, times, prices and
               grievances, with paragraph-level de-duplication.
gibberish   -- fluent, grammatical, meaning-free prose built from
               phrase-structure templates over word banks, with named
               "characters" that never resolve into a plot, under chapter
               headings, each numbered paragraph naming exactly one color.
codespec    -- a specification for an invented application: data models,
               endpoints, an error table and example JSON payloads, with
               identifiers built from syllable lists.
mixed       -- alternates the four kinds above in ~2,000-word blocks.

CLI
---
    python gen_long_noise.py --kind {ledger,transcript,gibberish,codespec,mixed} \
        --words N --seed S --out FILE [--collisions v3/answer-key/canon.md] \
        [--question]

With --question, after the file is written (the file itself is untouched --
"appends nothing"), one trivial, exactly-checkable surface question and its
answer are printed to stdout, computed from the content that was actually
generated, e.g.:

    Q: What is the total on the ledger line dated 1881-06-02?
    A: $118.42
"""

from __future__ import annotations

import argparse
import datetime
import itertools
import json
import random
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Word banks -- all invented, chosen to share no root with any name in
# v3/answer-key/canon.md (Larrow, Ostrey, Ordell, Ashlin, Hessel, Redlow,
# Alder, Vessey, Farland, Tarnet, Keddie, Brant, Vose, Cudd, Grigg, Strawn,
# Teague, Sill, Frick, Kepp, Vaught, Ammon, Loomis, Oram, Ansel, Orra, Emmet,
# Duncan, Ivy, Roy, Hazel, Gideon, Selby, Effie, Wilbur, Hobart, Merle, Nyle,
# Roland, Alonzo, Jerome, Rosalie, Leland, Junia, Marcus, Cleve). The runtime
# collision filter below is a second, load-bearing line of defense on top of
# this -- see load_collisions() and the safe_* helpers.
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "Orville", "Thaddeus", "Cassius", "Delphine", "Winona", "Cordelia",
    "Ambrose", "Silas", "Prudence", "Obadiah", "Verity", "Marcellus",
    "Theodosia", "Barnabas", "Content", "Jerusha", "Eliakim", "Rufus",
    "Thankful", "Zilpha", "Increase", "Philomena", "Ezra", "Araminta",
    "Jedediah", "Lucetta", "Nehemiah", "Permelia", "Ransom", "Sophronia",
    "Ichabod", "Vashti", "Cyrus", "Almira", "Elkanah", "Temperance",
    "Uriah", "Wealthy", "Zebulon", "Clarinda", "Absalom", "Dorcas",
    "Elihu", "Fidelia", "Gershom", "Huldah", "Josiah", "Keturah",
    "Lemuel", "Melinda", "Orpha", "Ozias", "Parthenia", "Reuben",
    "Salome", "Tobias", "Ursula", "Vernon", "Wilhelmina", "Xanthus",
    "Yolande", "Zadock",
]

LAST_NAMES = [
    "Holloway", "Winslow", "Trumbull", "Bascomb", "Cutter", "Pennington",
    "Sedgwick", "Aldous", "Ferris", "Gantry", "Hollister", "Ives",
    "Jessup", "Kirtland", "Larkspur", "Mabry", "Norwood", "Oakes",
    "Prentiss", "Quimby", "Ridgeway", "Stanhope", "Tolliver", "Underhill",
    "Vance", "Whitfield", "Yarrow", "Applegate", "Colby", "Dunmore",
    "Eastwick", "Fenwick", "Gault", "Hawthorne", "Isley", "Jarrett",
    "Kessler", "Loveless", "Mercer", "Nesbit", "Ormsby", "Pettigrew",
    "Quarles", "Rutledge", "Sackett", "Tarleton", "Upshaw", "Vail",
    "Winterbourne",
]

PLACE_NAMES = [
    "Millhaven", "Copperfield Junction", "Barrow's Notch", "Fenwick Crossing",
    "Duskwater", "Grayling Falls", "Norrow's Bend", "Thorncliff", "Wexford",
    "Elderslie", "Bramton", "Cutbank", "Hallow Reach", "Pinnacle Hollow",
    "Sourwood", "Quillan Forge", "Rook's Landing", "Sable Crossing",
    "Nettlebrook", "Fernwell", "Sparrow Creek", "Kettleford", "Longshade",
    "Whistler's Reach", "Grimstone", "Oatfield", "Candlewick", "Ridgeford",
    "Stonebridge", "Cooper's Landing",
]

BUSINESS_KINDS = [
    "General Store", "Feed & Grain", "Mercantile", "Trading Post",
    "Supply House", "Dry Goods", "Hardware Company", "Cooperage",
    "Chandlery", "Apothecary",
]

VENUE_KINDS = [
    "Depot", "Boarding House", "Exchange", "Waiting Room", "Tavern",
    "Freight Office", "Reading Room", "Livery Stable",
]

LEDGER_ITEMS = [
    ("kegs", "nails"), ("bolts", "osnaburg"), ("sacks", "flour"),
    ("pounds", "coffee"), ("yards", "calico"), ("boxes", "candles"),
    ("barrels", "salt pork"), ("gross", "buttons"), ("reams", "foolscap"),
    ("pounds", "tobacco"), ("gallons", "molasses"), ("bushels", "oats"),
    ("coils", "rope"), ("cakes", "soap"), ("boxes", "matches"),
    ("quires", "writing paper"), ("bottles", "liniment"), ("pounds", "shot"),
    ("kegs", "powder"), ("yards", "flannel"), ("pounds", "tea"),
    ("boxes", "raisins"), ("sacks", "salt"), ("bundles", "shingles"),
    ("pounds", "lard"), ("boxes", "starch"), ("pounds", "rice"),
    ("gallons", "vinegar"), ("pounds", "sugar"), ("yards", "muslin"),
    ("pounds", "currants"), ("kegs", "spikes"), ("boxes", "crackers"),
    ("yards", "ticking"), ("pounds", "pepper"), ("boxes", "buttons"),
]

LEDGER_NOTES = [
    "The roads were bad and few came in.",
    "Rain kept off the hay and trade was brisk.",
    "A stranger passed through and settled his account in coin.",
    "The scale was checked against the county standard and found true.",
    "No custom before noon; the bridge was under repair.",
    "Word came that the mill upriver had shut for want of water.",
    "Settled an old account carried over from the spring.",
    "The stove smoked all forenoon and the front room was closed.",
    "A dispute over an old charge was settled by splitting the difference.",
    "The peddler came through and traded rather than paid.",
    "Store closed at noon for a funeral in the neighborhood.",
    "Trade was thin, most families holding money back for the fair.",
    "The clerk misfigured a bill and the error was caught before it left the counter.",
    "Nothing of note; an ordinary day.",
    "A committee called about the school tax and stayed talking past closing.",
]

TRANSCRIPT_GRIEVANCES = [
    "the price of coffee has gone up again",
    "the ferry was late a third time this month",
    "nobody has fixed the fence along the north lot",
    "the mail comes later every week",
    "the well water has gone bitter since the digging up the road",
    "the new toll is more than the old one by half",
    "the schoolhouse stove still smokes",
    "the roof over the porch leaks worse every rain",
    "the neighbor's dog gets into the garden nightly",
    "the account has not been settled since spring",
    "the road commission never came to grade the lane",
    "the store has stopped carrying the good thread",
    "the letters take a week longer than they used to",
    "the fair moved its date without telling anyone",
]

TRANSCRIPT_TIMES = [
    "a quarter past six", "half past nine", "just before noon",
    "close to midnight", "around four", "well after supper",
    "before the bell", "some time past ten", "nearly dusk",
    "before the first frost", "not long after sunrise",
]

OBJECTS = [
    "a lantern", "a pocketwatch", "a fiddle", "a compass", "a hand mirror",
    "a tin whistle", "a deck of cards", "a walking stick", "a barometer",
    "a hymnal", "a ball of twine", "a horseshoe", "a pipe", "a spyglass",
    "a music box", "a ring of keys", "a straw hat", "a fishing creel",
    "a birdcage", "an inkwell", "a magnifying glass", "a tobacco pouch",
    "a bundle of letters", "a violin bow", "a weather vane",
]

G_TITLES = ["Mr.", "Mrs.", "Doctor", "the Widow", "young", "old", "Professor", "the Reverend"]

G_NOUNS = [
    "lattice", "threshold", "cipher", "interval", "remainder", "aperture",
    "cadence", "horizon", "argument", "residue", "fracture", "semblance",
    "current", "archive", "margin", "vestige", "corridor", "index",
    "filament", "undertow",
]

G_NOUNS2 = [
    "vessel", "channel", "register", "fold", "seam", "hinge", "bearing",
    "reservoir", "frame", "signal", "fissure", "gradient", "chamber",
    "circuit", "span",
]

G_VERBS = [
    "drifted", "resolved", "contested", "unfolded", "receded", "gathered",
    "dissolved", "persisted", "wavered", "aligned", "diverged",
    "accumulated", "lingered", "transformed", "collapsed", "extended",
    "mirrored", "suspended", "traversed", "echoed",
]

G_ADJ = [
    "tacit", "oblique", "provisional", "latent", "recursive", "brittle",
    "luminous", "indistinct", "residual", "asymmetric", "threadbare",
    "incidental", "spectral", "tangential", "inexact", "unstable",
    "marginal", "faint", "errant", "circular",
]

G_ADV = [
    "quietly", "obliquely", "provisionally", "nearly", "faintly",
    "gradually", "abruptly", "seemingly", "endlessly", "precisely",
    "vaguely", "steadily", "improbably", "silently", "unevenly",
]

G_CONNECT = [
    "and yet", "meanwhile", "in consequence", "notwithstanding",
    "for that reason", "all the same", "in the interval",
    "by the same token", "as it happened", "in spite of this",
    "or so it seemed", "which is to say",
]

COLORS = [
    "crimson", "cerulean", "ochre", "vermilion", "indigo", "saffron",
    "russet", "teal", "magenta", "umber", "periwinkle", "chartreuse",
    "mauve", "sepia", "turquoise", "amber", "slate", "violet", "coral",
    "ivory",
]

SYLLABLES = [
    "zar", "kel", "tor", "dun", "phi", "ryn", "wex", "bol", "fen", "ux",
    "quor", "dral", "nis", "thal", "yor", "zeph", "corv", "ilun", "mox",
    "pelu", "girn", "hask", "jov", "kesh", "lorn", "mynt", "nabu", "oxel",
    "pyx", "quen", "rilk", "sov", "trex", "ulm", "vek", "wyrn", "xand",
    "yult", "zorn", "brol", "cindar",
]

FIELD_NOUNS = [
    "id", "label", "status", "weight", "offset", "capacity", "threshold",
    "priority", "checksum", "interval", "payloadSize", "retryCount",
    "expiresAt", "ownerId", "parentRef", "tagList", "version", "locale",
    "region", "bucket",
]

FIELD_TYPES = [
    "string", "integer", "boolean", "timestamp", "decimal", "enum",
    "uuid", "list<string>", "object", "float",
]

HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]

ENDPOINT_VERBS = [
    "creates", "retrieves", "updates", "deletes", "archives",
    "synchronizes", "validates", "queues", "cancels", "reindexes",
]

ERROR_ADJ = [
    "Stale", "Malformed", "Unsupported", "Duplicate", "Expired", "Locked",
    "Unreachable", "Invalid", "Missing", "Conflicting", "Throttled",
    "Deprecated",
]

ERROR_NOUN = [
    "Token", "Payload", "Resource", "Schema", "Session", "Cursor",
    "Quota", "Dependency", "Manifest", "Handshake", "Checksum", "Endpoint",
]

HTTP_CODES = [400, 401, 403, 404, 409, 410, 412, 413, 415, 422, 423, 428, 429, 451, 500, 502, 503, 504]

PAYLOAD_STATUSES = ["pending", "complete", "failed", "queued"]

# ---------------------------------------------------------------------------
# Collision list
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June", "July",
    "August", "September", "October", "November", "December",
]
MONTH_INDEX = {name: i + 1 for i, name in enumerate(MONTH_NAMES)}
_MONTHS_PATTERN = "|".join(MONTH_NAMES)

# Common capitalized (sentence-start / function) words that must NOT be
# treated as forbidden proper nouns just because they happen to start a
# sentence in canon.md.
_STOPLIST = {
    "the", "this", "that", "these", "those", "it", "its", "they", "them",
    "their", "he", "she", "we", "you", "i", "a", "an", "and", "but", "or",
    "if", "when", "while", "because", "since", "after", "before", "during",
    "until", "although", "however", "therefore", "thus", "then", "now",
    "here", "there", "also", "both", "each", "every", "some", "many",
    "most", "few", "several", "all", "no", "none", "not", "only", "just",
    "even", "still", "yet", "already", "again", "once", "twice", "first",
    "second", "third", "last", "next", "other", "another", "same", "such",
    "so", "very", "too", "quite", "rather", "almost", "about", "above",
    "across", "against", "among", "around", "at", "behind", "below",
    "beneath", "beside", "between", "beyond", "by", "down", "for", "from",
    "in", "into", "near", "of", "off", "on", "onto", "out", "over",
    "through", "to", "toward", "under", "up", "upon", "with", "within",
    "without", "his", "her", "our", "my", "your", "whose", "which", "who",
    "whom", "what", "where", "why", "how", "yes", "well", "nothing",
    "something", "everything", "anything", "one", "two", "three", "four",
    "five", "six", "seven", "eight", "nine", "ten", "was", "were", "is",
    "are", "be", "been", "being", "has", "have", "had", "did", "does",
    "do", "can", "could", "will", "would", "shall", "should", "may",
    "might", "must", "as", "than", "whether", "either", "neither", "nor",
    "let", "having", "said", "says", "including", "any", "whatever",
}


def _clean_markdown(text: str) -> str:
    """Strip fenced/inline code and light markdown punctuation so the
    proper-noun and number scanners see plain prose word boundaries."""
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"`[^`]*`", " ", text)
    text = re.sub(r"[*_>#|]", " ", text)
    return text


def _norm_number(raw: str) -> float:
    cleaned = raw.replace("$", "").replace(",", "").strip()
    return round(float(cleaned), 4)


def _norm_date_dmy(raw: str) -> tuple:
    day_s, month_s, year_s = raw.split()
    return (int(year_s), MONTH_INDEX[month_s], int(day_s))


def _norm_date_mdy(raw: str) -> tuple:
    parts = raw.replace(",", "").split()
    month_s, day_s, year_s = parts[0], parts[1], parts[2]
    return (int(year_s), MONTH_INDEX[month_s], int(day_s))


def empty_collisions() -> dict:
    return {"phrases": set(), "numbers": set(), "dates": set()}


def load_collisions(path) -> dict:
    """Build the collision list from a fact sheet (normally
    v3/answer-key/canon.md). Returns a dict with three sets:

    - "phrases": lower-cased proper-noun phrases (people, places,
      organizations) that must never appear verbatim in generated output.
    - "numbers": distinctive numeric values (decimals, currency amounts,
      comma-grouped thousands) as floats.
    - "dates": distinctive full calendar dates as (year, month, day)
      tuples, plus literal year-range strings such as "1896-1924".

    Deliberately does NOT block bare small integers or bare years -- those
    are far too common to be "distinctive" and blocking them would make
    ordinary period prose impossible to generate.
    """
    if not path:
        return empty_collisions()
    text = Path(path).read_text(encoding="utf-8")
    clean = _clean_markdown(text)

    phrases = set()
    word = r"[A-Z][A-Za-z']*"
    pattern = re.compile(
        rf"\b{word}(?:-{word})*(?:\s+(?:&\s+)?{word}(?:-{word})*){{0,4}}\b"
    )
    for m in pattern.finditer(clean):
        phrase = " ".join(m.group(0).split())
        words = phrase.split()
        if len(words) == 1 and words[0].lower() in _STOPLIST:
            continue
        if len(phrase) < 3:
            continue
        phrases.add(phrase.lower())

    numbers = set()
    for m in re.finditer(r"\$\s?\d[\d,]*(?:\.\d+)?", clean):
        numbers.add(_norm_number(m.group(0)))
    for m in re.finditer(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b", clean):
        numbers.add(_norm_number(m.group(0)))
    for m in re.finditer(r"\b\d+\.\d+\b", clean):
        numbers.add(_norm_number(m.group(0)))

    dates = set()
    for m in re.finditer(rf"\b\d{{1,2}}\s+(?:{_MONTHS_PATTERN})\s+\d{{4}}\b", clean):
        dates.add(_norm_date_dmy(m.group(0)))
    for m in re.finditer(rf"\b(?:{_MONTHS_PATTERN})\s+\d{{1,2}},?\s+\d{{4}}\b", clean):
        dates.add(_norm_date_mdy(m.group(0)))
    for m in re.finditer(r"\b\d{4}[-–]\d{4}\b", clean):
        dates.add(("range", m.group(0).replace("-", "–")))

    return {"phrases": phrases, "numbers": numbers, "dates": dates}


# ---------------------------------------------------------------------------
# Collision-safe draw helpers
# ---------------------------------------------------------------------------

def safe_choice(rng: random.Random, seq, collisions: dict, key=lambda x: x, max_tries: int = 60):
    """rng.choice(seq), re-drawn until key(candidate) is not a blocked phrase."""
    candidate = None
    for _ in range(max_tries):
        candidate = rng.choice(seq)
        if key(candidate).lower() not in collisions["phrases"]:
            return candidate
    filtered = [c for c in seq if key(c).lower() not in collisions["phrases"]]
    return rng.choice(filtered) if filtered else candidate


def safe_full_name(rng: random.Random, firsts, lasts, collisions: dict, max_tries: int = 60) -> str:
    for _ in range(max_tries):
        first = rng.choice(firsts)
        last = rng.choice(lasts)
        full = f"{first} {last}"
        if (
            first.lower() not in collisions["phrases"]
            and last.lower() not in collisions["phrases"]
            and full.lower() not in collisions["phrases"]
        ):
            return full
    filtered_firsts = [n for n in firsts if n.lower() not in collisions["phrases"]] or firsts
    filtered_lasts = [n for n in lasts if n.lower() not in collisions["phrases"]] or lasts
    return f"{rng.choice(filtered_firsts)} {rng.choice(filtered_lasts)}"


def safe_amount(rng: random.Random, low: float, high: float, collisions: dict, decimals: int = 2, max_tries: int = 60) -> float:
    value = round(rng.uniform(low, high), decimals)
    for _ in range(max_tries):
        if value not in collisions["numbers"]:
            return value
        value = round(rng.uniform(low, high), decimals)
    return value


def _identifier(rng: random.Random, collisions: dict, n: int = 2, style: str = "Pascal", max_tries: int = 30) -> str:
    ident = ""
    for _ in range(max_tries):
        parts = [rng.choice(SYLLABLES).capitalize() for _ in range(n)]
        ident = "".join(parts)
        if style == "camel" and ident:
            ident = ident[0].lower() + ident[1:]
        if ident.lower() not in collisions["phrases"]:
            return ident
    return ident


def _syll_word(rng: random.Random, n: int = 1) -> str:
    return "".join(rng.choice(SYLLABLES) for _ in range(n))


def advance_date(state: dict, rng: random.Random, collisions: dict, min_days: int = 1, max_days: int = 5) -> datetime.date:
    """Move the shared ledger date cursor forward and skip any exact
    calendar date that appears in the collision list."""
    cur = state["date_cursor"]
    for _ in range(30):
        cur = cur + datetime.timedelta(days=rng.randint(min_days, max_days))
        if (cur.year, cur.month, cur.day) not in collisions["dates"]:
            break
    state["date_cursor"] = cur
    return cur


def word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# ledger
# ---------------------------------------------------------------------------

def _safe_item(rng: random.Random, collisions: dict, max_tries: int = 20):
    """Draw (unit, item, qty, price, subtotal) such that neither the price
    nor the computed subtotal (qty * price, which safe_amount alone cannot
    guard) collides with a distinctive canon number."""
    unit = item = ""
    qty, price, sub = 1, 0.02, 0.02
    for _ in range(max_tries):
        unit, item = rng.choice(LEDGER_ITEMS)
        qty = rng.randint(1, 48)
        price = safe_amount(rng, 0.02, 3.75, collisions)
        sub = round(qty * price, 2)
        if sub not in collisions["numbers"]:
            return unit, item, qty, price, sub
    return unit, item, qty, price, sub


def _make_ledger_items(rng: random.Random, collisions: dict, max_tries: int = 20):
    parts, day_total = [], 0.0
    for _ in range(max_tries):
        parts = []
        subtotals = []
        for _ in range(rng.randint(1, 3)):
            unit, item, qty, price, sub = _safe_item(rng, collisions)
            subtotals.append(sub)
            parts.append(f"{qty} {unit} {item} @ ${price:.2f} (${sub:.2f})")
        day_total = round(sum(subtotals), 2)
        if day_total not in collisions["numbers"]:
            return parts, day_total
    return parts, day_total


def generate_ledger(f, rng: random.Random, target_words: int, collisions: dict, state: dict, firsts, lasts) -> int:
    written = 0
    iterations = 0
    max_iterations = target_words * 4 + 200
    while written < target_words and iterations < max_iterations:
        iterations += 1
        if state.get("ledger_started") and rng.random() < 0.12:
            note = rng.choice(LEDGER_NOTES)
            text = f"*{note}*"
            f.write(text + "\n\n")
            written += word_count(text)
            continue
        state["ledger_started"] = True
        date = advance_date(state, rng, collisions)
        customer = safe_full_name(rng, firsts, lasts, collisions)
        running_total = state.get("ledger_running_total", 0.0)
        for _ in range(20):
            parts, day_total = _make_ledger_items(rng, collisions)
            candidate_total = round(running_total + day_total, 2)
            if candidate_total not in collisions["numbers"]:
                running_total = candidate_total
                break
        state["ledger_running_total"] = running_total
        line = (
            f"- **{date.isoformat()}** — of {customer}, "
            + ", ".join(parts)
            + f"; day total ${day_total:.2f}; running total ${running_total:.2f}."
        )
        f.write(line + "\n\n")
        written += word_count(line)
        state.setdefault("ledger_entries", []).append((date.isoformat(), f"{running_total:.2f}"))
    return written


# ---------------------------------------------------------------------------
# transcript
# ---------------------------------------------------------------------------

def _record_first_mention(state: dict, obj: str, speaker: str) -> None:
    fm = state.setdefault("transcript_first_mention", {})
    if obj not in fm:
        fm[obj] = speaker


def _transcript_sentence(rng: random.Random, speaker: str, other: str, collisions: dict, state: dict) -> str:
    choice = rng.randint(0, 4)
    if choice == 0:
        obj = rng.choice(OBJECTS)
        _record_first_mention(state, obj, speaker)
        return f"Says {other} still keeps {obj} from last spring and has never once mentioned it."
    if choice == 1:
        grievance = rng.choice(TRANSCRIPT_GRIEVANCES)
        price = safe_amount(rng, 0.05, 9.95, collisions)
        return f"Allows that {grievance}, and says it is hardly worth ${price:.2f} to fuss over."
    if choice == 2:
        t = rng.choice(TRANSCRIPT_TIMES)
        return f"Claims {other} did not come by until {t}, and will not say why."
    if choice == 3:
        obj = rng.choice(OBJECTS)
        _record_first_mention(state, obj, speaker)
        return f"Wants to know who left {obj} out on the porch overnight."
    grievance = rng.choice(TRANSCRIPT_GRIEVANCES)
    return f"Will not let it go that {grievance}, though {other} has heard enough of it."


def generate_transcript(f, rng: random.Random, target_words: int, collisions: dict, state: dict, firsts, lasts) -> int:
    speakers = state.get("transcript_speakers")
    if not speakers:
        speakers = [safe_full_name(rng, firsts, lasts, collisions) for _ in range(rng.randint(4, 7))]
        state["transcript_speakers"] = speakers
    seen = state.setdefault("transcript_seen", set())
    written = 0
    iterations = 0
    max_iterations = target_words * 4 + 200
    while written < target_words and iterations < max_iterations:
        iterations += 1
        speaker = rng.choice(speakers)
        others = [s for s in speakers if s != speaker] or [speaker]
        other = rng.choice(others)
        n_sent = rng.randint(1, 2)
        sentences = [_transcript_sentence(rng, speaker, other, collisions, state) for _ in range(n_sent)]
        text = " ".join(sentences)
        tries = 0
        while text in seen and tries < 5:
            sentences = [_transcript_sentence(rng, speaker, other, collisions, state) for _ in range(n_sent)]
            text = " ".join(sentences)
            tries += 1
        seen.add(text)
        line = f"**{speaker}:** {text}"
        f.write(line + "\n\n")
        written += word_count(line)
    return written


# ---------------------------------------------------------------------------
# gibberish
# ---------------------------------------------------------------------------

def _g_sentence_with_color(rng: random.Random, character: str):
    color = rng.choice(COLORS)
    text = (
        f"The {rng.choice(G_ADJ)} {rng.choice(G_NOUNS)} {rng.choice(G_ADV)} "
        f"{rng.choice(G_VERBS)} the {color} {rng.choice(G_NOUNS2)}, "
        f"{rng.choice(G_CONNECT)} {character} {rng.choice(G_VERBS)} {rng.choice(G_ADV)}."
    )
    return text, color


def _g_sentence_plain(rng: random.Random, character: str) -> str:
    return (
        f"{character} {rng.choice(G_ADV)} {rng.choice(G_VERBS)} the {rng.choice(G_ADJ)} "
        f"{rng.choice(G_NOUNS)} toward the {rng.choice(G_NOUNS2)}, "
        f"{rng.choice(G_CONNECT)} it {rng.choice(G_VERBS)} without {rng.choice(G_NOUNS)}."
    )


def _g_paragraph(rng: random.Random, characters) -> tuple:
    color_character = rng.choice(characters)
    color_sentence, color = _g_sentence_with_color(rng, color_character)
    n_plain = rng.randint(2, 3)
    plain_sentences = [_g_sentence_plain(rng, rng.choice(characters)) for _ in range(n_plain)]
    half = n_plain // 2
    all_sentences = plain_sentences[:half] + [color_sentence] + plain_sentences[half:]
    return " ".join(all_sentences), color


def generate_gibberish(f, rng: random.Random, target_words: int, collisions: dict, state: dict, firsts, lasts) -> int:
    characters = state.get("g_characters")
    if not characters:
        characters = []
        for _ in range(rng.randint(4, 8)):
            name = safe_full_name(rng, firsts, lasts, collisions)
            characters.append(f"{rng.choice(G_TITLES)} {name}" if rng.random() < 0.5 else name)
        state["g_characters"] = characters
    para_colors = state.setdefault("gibberish_para_colors", {})
    seen = state.setdefault("gibberish_seen", set())
    para_since_chapter = state.get("g_para_since_chapter", 999)
    chapter_num = state.get("g_chapter_num", 0)
    next_chapter_at = state.get("g_next_chapter_at", 0)

    written = 0
    iterations = 0
    max_iterations = target_words * 3 + 200
    while written < target_words and iterations < max_iterations:
        iterations += 1
        if para_since_chapter >= next_chapter_at:
            chapter_num += 1
            heading = f"## Chapter {chapter_num} — {rng.choice(G_ADJ).capitalize()} {rng.choice(G_NOUNS).capitalize()}"
            f.write(heading + "\n\n")
            written += word_count(heading)
            para_since_chapter = 0
            next_chapter_at = rng.randint(4, 8)
            continue
        body, color = _g_paragraph(rng, characters)
        pnum = state.get("para_counter", 0) + 1
        state["para_counter"] = pnum
        text = f"¶{pnum}. {body}"
        tries = 0
        while text in seen and tries < 5:
            body, color = _g_paragraph(rng, characters)
            text = f"¶{pnum}. {body}"
            tries += 1
        seen.add(text)
        f.write(text + "\n\n")
        written += word_count(text)
        para_colors[pnum] = color
        para_since_chapter += 1

    state["g_para_since_chapter"] = para_since_chapter
    state["g_chapter_num"] = chapter_num
    state["g_next_chapter_at"] = next_chapter_at
    return written


# ---------------------------------------------------------------------------
# codespec
# ---------------------------------------------------------------------------

def _codespec_model_block(rng, collisions, used_models):
    name = _identifier(rng, collisions, n=2)
    tries = 0
    while name in used_models and tries < 10:
        name = _identifier(rng, collisions, n=2)
        tries += 1
    used_models.add(name)
    lines = [f"### Data model: `{name}`", "", "| field | type |", "|---|---|"]
    for _ in range(rng.randint(3, 6)):
        if rng.random() < 0.6:
            fname = rng.choice(FIELD_NOUNS)
        else:
            fname = _identifier(rng, collisions, n=1, style="camel")
        ftype = rng.choice(FIELD_TYPES)
        lines.append(f"| `{fname}` | {ftype} |")
    return "\n".join(lines)


def _codespec_endpoint_line(rng):
    method = rng.choice(HTTP_METHODS)
    path = "/" + "/".join(_syll_word(rng, 2) for _ in range(rng.randint(2, 3)))
    return (
        f"- `{method} {path}`: {rng.choice(ENDPOINT_VERBS)} the "
        f"{rng.choice(FIELD_NOUNS)} for a given {_syll_word(rng, 2)}."
    )


def _codespec_error_table(rng, used_errors, n_rows):
    lines = ["| error | code | message |", "|---|---|---|"]
    for _ in range(n_rows):
        adj = rng.choice(ERROR_ADJ)
        noun = rng.choice(ERROR_NOUN)
        name = f"{adj}{noun}"
        tries = 0
        while name in used_errors and tries < 30:
            adj = rng.choice(ERROR_ADJ)
            noun = rng.choice(ERROR_NOUN)
            name = f"{adj}{noun}"
            tries += 1
        code = rng.choice(HTTP_CODES)
        message = f"{noun} was {adj.lower()}; the request could not be completed."
        used_errors[name] = code
        lines.append(f"| `{name}` | {code} | {message} |")
    return "\n".join(lines)


def _codespec_payload_block(rng):
    payload_obj = {
        _syll_word(rng, 2): rng.choice(FIELD_NOUNS),
        _syll_word(rng, 2): rng.randint(1, 999),
        "status": rng.choice(PAYLOAD_STATUSES),
    }
    return "```json\n" + json.dumps(payload_obj, indent=2) + "\n```"


def generate_codespec(f, rng: random.Random, target_words: int, collisions: dict, state: dict, firsts, lasts) -> int:
    written = 0
    if not state.get("codespec_app_name"):
        state["codespec_app_name"] = _identifier(rng, collisions, n=2)
    if not state.get("codespec_intro_written"):
        app_name = state["codespec_app_name"]
        state["codespec_intro_written"] = True
        header = (
            f"## Specification: {app_name}\n\n"
            f"An internal interface specification for the invented {app_name} service. "
            "This document describes no real system, product or API."
        )
        f.write(header + "\n\n")
        written += word_count(header)

    used_models = state.setdefault("codespec_models", set())
    used_errors = state.setdefault("codespec_errors", {})

    iterations = 0
    max_iterations = target_words // 3 + 80
    while written < target_words and iterations < max_iterations:
        iterations += 1
        round_num = state.get("codespec_round", 0) + 1
        state["codespec_round"] = round_num

        model_block = _codespec_model_block(rng, collisions, used_models)
        section = f"### Round {round_num} — data model\n\n{model_block}"
        f.write(section + "\n\n")
        written += word_count(section)
        if written >= target_words:
            break

        endpoints_block = "\n".join(_codespec_endpoint_line(rng) for _ in range(2))
        section = f"### Round {round_num} — endpoints\n\n{endpoints_block}"
        f.write(section + "\n\n")
        written += word_count(section)
        if written >= target_words:
            break

        error_table = _codespec_error_table(rng, used_errors, 2)
        section = f"### Round {round_num} — errors\n\n{error_table}"
        f.write(section + "\n\n")
        written += word_count(section)
        if written >= target_words:
            break

        payload_block = _codespec_payload_block(rng)
        section = f"### Round {round_num} — example payload\n\n{payload_block}"
        f.write(section + "\n\n")
        written += word_count(section)

    return written


# ---------------------------------------------------------------------------
# mixed
# ---------------------------------------------------------------------------

_KIND_FUNCS = {
    "ledger": generate_ledger,
    "transcript": generate_transcript,
    "gibberish": generate_gibberish,
    "codespec": generate_codespec,
}


def generate_mixed(f, rng: random.Random, target_words: int, collisions: dict, state: dict, firsts, lasts) -> int:
    order = ["ledger", "transcript", "gibberish", "codespec"]
    rng.shuffle(order)
    kinds_cycle = itertools.cycle(order)
    block_target = 2000
    written = 0
    block_num = 0
    max_blocks = max(4, target_words // 20 + 20)
    while written < target_words and block_num < max_blocks:
        block_num += 1
        kind = next(kinds_cycle)
        remaining = target_words - written
        this_target = max(20, min(block_target, remaining))
        heading = f"## Block {block_num} — {kind.capitalize()}"
        f.write(heading + "\n\n")
        written += word_count(heading)
        if written >= target_words:
            break
        written += _KIND_FUNCS[kind](f, rng, this_target, collisions, state, firsts, lasts)
    return written


_ALL_KIND_FUNCS = dict(_KIND_FUNCS, mixed=generate_mixed)


# ---------------------------------------------------------------------------
# --question support
# ---------------------------------------------------------------------------

def build_question(kind: str, rng: random.Random, state: dict):
    """Return (question, answer) computed from the shared generation state,
    or None if nothing was recorded (only possible for a tiny --words)."""
    available = []
    if state.get("ledger_entries"):
        available.append("ledger")
    if state.get("transcript_first_mention"):
        available.append("transcript")
    if state.get("gibberish_para_colors"):
        available.append("gibberish")
    if state.get("codespec_errors"):
        available.append("codespec")
    if not available:
        return None

    chosen = kind if kind in available else rng.choice(available)

    if chosen == "ledger":
        date, total = rng.choice(state["ledger_entries"])
        return (f"What is the total on the ledger line dated {date}?", f"${total}")

    if chosen == "transcript":
        obj, speaker = rng.choice(list(state["transcript_first_mention"].items()))
        return (f"Which speaker mentions {obj} first?", speaker)

    if chosen == "gibberish":
        pnum, color = rng.choice(list(state["gibberish_para_colors"].items()))
        return (f"What color is named in paragraph {pnum}?", color)

    # codespec
    name, code = rng.choice(list(state["codespec_errors"].items()))
    return (f"What HTTP status code is assigned to the `{name}` error in the spec?", str(code))


# ---------------------------------------------------------------------------
# Titles
# ---------------------------------------------------------------------------

def make_title(rng: random.Random, kind: str, collisions: dict, state: dict) -> str:
    place = safe_choice(rng, PLACE_NAMES, collisions)
    if kind == "ledger":
        return f"{place} {rng.choice(BUSINESS_KINDS)} Day-Book"
    if kind == "transcript":
        return f"Overheard at the {place} {rng.choice(VENUE_KINDS)}"
    if kind == "gibberish":
        return f"{rng.choice(G_ADJ).capitalize()} {rng.choice(G_NOUNS).capitalize()}: A Chronicle"
    if kind == "codespec":
        # Generate the app name once here and stash it in the shared state so
        # generate_codespec() reuses the same name instead of drawing a
        # second, different one for its own "## Specification: ..." line.
        app = _identifier(rng, collisions, n=2)
        state["codespec_app_name"] = app
        return f"{app} Interface Specification"
    return f"Miscellany of {place} County"


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------

def generate(kind: str, words: int, seed: int, out_path, collisions_path=None, question: bool = False):
    if words <= 0:
        raise ValueError("words must be a positive integer")
    if kind not in _ALL_KIND_FUNCS:
        raise ValueError(f"unknown kind: {kind!r}")

    rng = random.Random(seed)
    collisions = load_collisions(collisions_path)

    start_year = rng.randint(1858, 1912)
    start_month = rng.randint(1, 12)
    start_day = rng.randint(1, 28)
    state = {"date_cursor": datetime.date(start_year, start_month, start_day)}

    title = make_title(rng, kind, collisions, state)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    total_words = 0
    with out_path.open("w", encoding="utf-8", newline="\n") as f:
        header = f"# {title} — generated noise ({kind}, {words} words, seed {seed})"
        f.write(header + "\n\n")
        total_words += word_count(header)
        total_words += _ALL_KIND_FUNCS[kind](f, rng, words, collisions, state, FIRST_NAMES, LAST_NAMES)

    qa = build_question(kind, rng, state) if question else None
    if question:
        if qa:
            print(f"Q: {qa[0]}")
            print(f"A: {qa[1]}")
        else:
            print("Q: (no checkable fact was generated at this word count)")
            print("A: (none)")

    return total_words, qa


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gen_long_noise.py",
        description="Generate long, meaning-free noise documents for v3 context-stress testing.",
    )
    p.add_argument("--kind", required=True, choices=["ledger", "transcript", "gibberish", "codespec", "mixed"])
    p.add_argument("--words", required=True, type=int, help="target word count (5,000 to 400,000+)")
    p.add_argument("--seed", required=True, type=int, help="deterministic RNG seed")
    p.add_argument("--out", required=True, help="output markdown file path")
    p.add_argument(
        "--collisions",
        default=None,
        help="path to a fact sheet (e.g. v3/answer-key/canon.md) whose proper nouns, "
        "dates and distinctive numbers must never be generated",
    )
    p.add_argument(
        "--question",
        action="store_true",
        help="after writing --out, print one trivial, exactly-checkable question and "
        "answer about the generated content (the file itself is not modified)",
    )
    return p


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.words <= 0:
        print("error: --words must be a positive integer", file=sys.stderr)
        return 2
    generate(args.kind, args.words, args.seed, args.out, args.collisions, args.question)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
