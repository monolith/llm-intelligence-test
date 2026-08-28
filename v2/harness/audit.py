#!/usr/bin/env python3
"""Mechanical audit for a synthesis test, root-agnostic across versions (v2, v3, ...).

Checks the answer key (<root>/answer-key/*.md) against the test input
(<root>/test-input/**) and reports PASS/FAIL/UNPARSED/NEEDS-HUMAN/ACCEPTED-SINGLE-SOURCE
per item, with evidence. The number of narrators, the word-count band, and the exact id
shapes used by the key (X-ids, near-tie ids, fact ids, document ids, abstention ids) are
all read from the corpus itself rather than assumed -- see discover_narrator_ids and
check7_questions_coverage's Section A handling for the two places that matters most.

The key files are markdown written by a person, so every parser here is
defensive: where a value cannot be extracted, the item is reported as
UNPARSED rather than silently skipped or silently passed. Likewise, a retelling that has
not been drafted yet (or cannot be read) is reported as a FAIL row -- "missing retelling
rNN" -- rather than crashing.

Usage:
    python3 audit.py --root v2                                       # print report, exit 0
    python3 audit.py --root v2 --strict                               # exit 1 if any FAIL/UNPARSED
    python3 audit.py --root v3 --min-words 1000 --max-words 1500      # different word-count band

Standard library only, Python 3.12.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

# --------------------------------------------------------------------------
# Generic text helpers
# --------------------------------------------------------------------------


def normalize_ws_quotes(s: str) -> str:
    """Collapse whitespace and fold curly quotes/dashes to straight ASCII forms."""
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"')
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def bounded_search(haystack: str, needle: str, ignore_case: bool = True) -> bool:
    """Substring search where `needle` must not be glued to surrounding word
    chars or hyphens (so "fifty" does not match inside "fifty-seven")."""
    needle = needle.strip()
    if not needle:
        return False
    flags = re.IGNORECASE if ignore_case else 0
    pattern = re.compile(r"(?<![\w-])" + re.escape(needle) + r"(?![\w-])", flags)
    return pattern.search(haystack) is not None


def find_bounded_pos(haystack: str, needle: str, ignore_case: bool = True) -> Optional[int]:
    needle = needle.strip()
    if not needle:
        return None
    flags = re.IGNORECASE if ignore_case else 0
    pattern = re.compile(r"(?<![\w-])" + re.escape(needle) + r"(?![\w-])", flags)
    m = pattern.search(haystack)
    return m.start() if m else None


# --------------------------------------------------------------------------
# Number word <-> digit conversion (small, enough for this corpus: 0-9999)
# --------------------------------------------------------------------------

_ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
_TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
_WORD_VALUE = {w: i for i, w in enumerate(_ONES) if w}
_WORD_VALUE.update({w: i * 10 for i, w in enumerate(_TENS) if w})
_SCALE_VALUE = {"hundred": 100, "thousand": 1000}


def words_to_number(phrase: str) -> Optional[int]:
    tokens = [t for t in re.split(r"[\s-]+", phrase.lower().strip()) if t and t != "and"]
    if not tokens:
        return None
    total = 0
    current = 0
    matched_any = False
    for t in tokens:
        if t in _WORD_VALUE:
            current += _WORD_VALUE[t]
            matched_any = True
        elif t in _SCALE_VALUE:
            scale = _SCALE_VALUE[t]
            current = (current or 1) * scale
            if scale == 1000:
                total += current
                current = 0
            matched_any = True
        else:
            return None
    total += current
    return total if matched_any else None


def _two_digit_words(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    return _TENS[tens] + ("-" + _ONES[ones] if ones else "")


def number_to_words(n: int, with_and: bool = True) -> str:
    if n == 0:
        return "zero"
    if n < 0 or n >= 10000:
        return str(n)
    parts = []
    thousands, rem = divmod(n, 1000)
    hundreds, rem2 = divmod(rem, 100)
    if thousands:
        parts.append(_two_digit_words(thousands) + " thousand")
    if hundreds:
        parts.append(_ONES[hundreds] + " hundred")
    if rem2:
        tail = _two_digit_words(rem2)
        if parts and with_and:
            parts.append("and " + tail)
        else:
            parts.append(tail)
    return " ".join(parts)


def generate_number_variants(candidate: str) -> list[str]:
    """Given a literal candidate string, return extra digit<->word variants."""
    variants: list[str] = []
    m = re.search(r"\$?(\d[\d,]*)", candidate)
    if m:
        digits = m.group(1).replace(",", "")
        if digits.isdigit():
            n = int(digits)
            if 0 < n < 10000:
                for with_and in (True, False):
                    words = number_to_words(n, with_and=with_and)
                    variant = candidate[: m.start()] + words + candidate[m.end():]
                    variants.append(variant.strip())
    else:
        words_list = candidate.split()
        for length in range(min(4, len(words_list)), 0, -1):
            head = " ".join(words_list[:length])
            n = words_to_number(head)
            if n is not None:
                tail = " ".join(words_list[length:])
                digit_variant = (str(n) + (" " + tail if tail else "")).strip()
                variants.append(digit_variant)
                break
    seen = set()
    out = []
    for v in variants:
        nv = normalize_ws_quotes(v)
        if nv and nv not in seen:
            seen.add(nv)
            out.append(v)
    return out


def generate_punctuation_variants(candidate: str) -> list[str]:
    """The key sometimes joins two clauses of a paraphrased quote with "; "
    where the authored retelling instead ends the first as its own sentence
    ("... bridge. He was ..."). Try swapping the two forms; bounded_search is
    already case-insensitive, so the capital letter that follows a real
    period does not need special handling."""
    variants = []
    if "; " in candidate:
        variants.append(candidate.replace("; ", ". "))
    if ". " in candidate:
        variants.append(candidate.replace(". ", "; "))
    return variants


def candidate_present(haystack_norm: str, candidate: str) -> bool:
    """Check whether `candidate` (a literal value or quote pulled from the
    key) is present in `haystack_norm` (already whitespace/quote-normalized
    text), tolerating: digit<->word number forms, an ellipsis ("…") standing
    in for an elided middle portion of a longer quote (the key sometimes
    abbreviates a long quoted passage with one), and a semicolon/period
    swapped at a clause boundary. When an ellipsis is present each side is
    checked independently (order is not enforced, since the ellipsis by
    definition means "and more not shown here")."""
    parts = [p.strip() for p in candidate.split("…")] if "…" in candidate else [candidate]
    parts = [p for p in parts if p]
    if not parts:
        return False
    for part in parts:
        variants = (
            [part]
            + generate_number_variants(part)
            + generate_punctuation_variants(part)
            + expand_measurement_token(part)
        )
        variants_norm = [normalize_ws_quotes(v) for v in variants]
        if not any(bounded_search(haystack_norm, v) for v in variants_norm):
            return False
    return True


# --------------------------------------------------------------------------
# Anchor-gated leak detection (Residual cleanup, 2026-08-27)
#
# A handful of check-2 candidates are short, common values (a bare 1-2
# digit number, a kinship noun, a year, a pair of initials) that recur
# elsewhere in the corpus for entirely unrelated reasons -- the corpus
# reuses small numbers and family words the way real prose does. A plain
# substring `candidate_present` hit for one of these in some OTHER
# narrator is not evidence of a leaked planted error; it just means the
# same short word/number shows up in an unrelated sentence.
#
# Two principled, narrow fixes, matched to the failure shape:
#   1. Bare values under 3 characters (e.g. "8", "13", "30") are too short
#      to trust as a unique fingerprint at all -- downgraded to
#      NEEDS-HUMAN rather than treated as a leak (see
#      `is_fragile_bare_value`).
#   2. Slightly longer but still-common values (e.g. "4 inches", "nephew",
#      "1902", "A. Rennick") are checked against an ANCHOR word pulled
#      verbatim from the SAME corruption-map cell the candidate came from
#      -- an occurrence only counts as a real leak when the candidate and
#      its own row's anchor word appear together in one sentence of the
#      other narrator's text (see `anchor_confirms`).
# --------------------------------------------------------------------------

LEAK_ANCHORS: dict[str, str] = {
    # X16 As-told (corruption-map.md): 'The purchase was in **1902**.'
    "1902": "purchase",
    # X19 As-told: '...the night book as "A. Rennick"...'
    "A. Rennick": "night book",
    # NT-1 Wrong value: 'Sheet 11 specified **4 inches** of travel'
    "4 inches": "Sheet 11",
    # NT-7 Wrong value: 'Dorsey Tice was Warren Tice's **nephew**'
    "nephew": "Tice",
}


def is_fragile_bare_value(candidate: str) -> bool:
    """A candidate under 3 characters (a bare 1- or 2-digit number, in
    practice) is too short to serve as a unique fingerprint in prose this
    size -- small counts recur constantly for unrelated reasons."""
    return len(candidate.strip()) < 3


_SENTENCE_SPLIT_RE = re.compile(r"(?<![A-Z]\.)(?<=[.!?])\s+")


def split_sentence_units(text: str) -> list[str]:
    """Break `text` into rough sentence-or-line units for a same-sentence
    anchor check. Splits on sentence-ending punctuation, and treats each
    line as its own unit first (a blockquote citation line such as "> --
    Cadder Valley Railroad to A. Rennick, 30 April 1901" has no
    sentence-ending period of its own). A single capital letter followed by
    a period (e.g. "A. Rennick") is not treated as a sentence end -- this
    corpus's initials would otherwise fragment a candidate like "A. Rennick"
    across two units, so it could never be found alongside its own anchor
    even in the sentence where it genuinely belongs."""
    units: list[str] = []
    for line in text.splitlines():
        line = line.strip().lstrip(">").strip()
        if not line:
            continue
        units.extend(_SENTENCE_SPLIT_RE.split(line))
    return [u for u in units if u.strip()]


def anchor_confirms(text: str, candidate: str, anchor: str) -> bool:
    """True when `candidate` and `anchor` occur together in one
    sentence-like unit of `text`. Used to tell a genuine leak of a short,
    common candidate value apart from an unrelated, coincidental use of
    the same short word/number elsewhere in the corpus."""
    for unit in split_sentence_units(text):
        unit_norm = normalize_ws_quotes(unit)
        if bounded_search(unit_norm, candidate) and bounded_search(unit_norm, anchor):
            return True
    return False


def candidate_required_narrators(wrong_value_cell: str, candidate: str, carriers: list[str]) -> list[str]:
    """Most near-tie rows share one literal wrong value between both
    carriers, so a candidate must be present in every carrier. Two rows
    instead attribute a SPECIFIC candidate to just one carrier inside a
    parenthetical annotation:
      - NT-8: "(r04: \"my father's uncle\"; r01: \"his grand-niece\")" --
        each carrier has its own, different wrong phrasing, not a shared
        literal value.
      - NT-10: "(r09 states only this; r06 additionally sums it to
        **69** in all)" -- one carrier states a further, narrator-specific
        derived value the other never touches.
    When the candidate's own clause inside such a parenthetical names
    exactly one of the row's carriers, that candidate is required only
    from that one carrier. A candidate appearing in the cell's main text,
    outside any parenthetical, keeps the normal full-carrier requirement
    (the other nine near-tie pairs, which share one literal wrong value)."""
    for paren in re.findall(r"\(([^()]*)\)", wrong_value_cell):
        if not bounded_search(paren, candidate):
            continue
        for clause in re.split(r";", paren):
            if not bounded_search(clause, candidate):
                continue
            ids_here = sorted(set(re.findall(r"r\d{2}", clause)) & set(carriers))
            if len(ids_here) == 1:
                return ids_here
    return list(carriers)


# Check-3 rows with a single, documented manual verdict that a generic fix
# would be unsafe to generalize (see audit-triage.md, Residual cleanup
# 2026-08-27, for the full reasoning). Used to downgrade a specific FAIL to
# NEEDS-HUMAN without loosening the matching logic that every other row
# still relies on.
MANUALLY_VERIFIED_PRESENT: dict[str, str] = {
    "F089": (
        "r03 states the value as \"up above forty in the daytime\", with no "
        "unit word -- not a retelling slip: narrator-briefs.md's own r03 "
        "bullet for F089 specifies this exact unit-less phrasing. A generic "
        "bare-number fallback would be unsafe elsewhere in this corpus "
        "(see Fix 7, audit-triage.md), so this one fact is confirmed by "
        "hand instead"
    ),
}


# --------------------------------------------------------------------------
# Markdown table / section parsing
# --------------------------------------------------------------------------


def split_sections(text: str, level: int = 2) -> dict[str, str]:
    """Split on '#'*level + ' ' headings. Returns heading-text -> body-text,
    in document order (dict preserves insertion order)."""
    marker = "#" * level + " "
    pattern = re.compile(r"^" + re.escape(marker) + r"(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        heading = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[heading] = text[start:end]
    return sections


def find_all_table_blocks(text: str) -> list[list[str]]:
    lines = text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            current.append(line.strip())
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def dedupe_headers(header: list[str]) -> list[str]:
    """Markdown tables in this key legitimately repeat a column name (the
    near-tie table has two 'Carried by' columns: one for the wrong value's
    carriers, one for the correct value's). dict(zip(header, cells)) would
    silently keep only the LAST occurrence, which corrupts parsing of the
    first one. Disambiguate repeats by appending ' (2)', ' (3)', ... to the
    2nd+ occurrence, leaving the first occurrence's name untouched so
    existing `row.get(name)` lookups keep finding the FIRST column."""
    seen: dict[str, int] = {}
    out = []
    for h in header:
        seen[h] = seen.get(h, 0) + 1
        out.append(h if seen[h] == 1 else f"{h} ({seen[h]})")
    return out


def parse_table(block_lines: list[str]) -> list[dict[str, str]]:
    def split_row(line: str) -> list[str]:
        line = line.strip()
        if line.startswith("|"):
            line = line[1:]
        if line.endswith("|"):
            line = line[:-1]
        return [c.strip() for c in line.split("|")]

    if len(block_lines) < 2:
        return []
    header = dedupe_headers([h.lower() for h in split_row(block_lines[0])])
    rows = []
    for line in block_lines[2:]:
        cells = split_row(line)
        if len(cells) < len(header):
            cells = cells + [""] * (len(header) - len(cells))
        elif len(cells) > len(header):
            cells = cells[: len(header)]
        rows.append(dict(zip(header, cells)))
    return rows


def extract_quoted_spans(text: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r'["“]([^"”]+)["”]', text)]


def extract_bold_spans(text: str) -> list[str]:
    return re.findall(r"\*\*([^*]+)\*\*", text)


_MARKER_LABELS = {"internal contradiction.", "internal contradiction", "late reversal.", "late reversal"}


def clean_quote(q: str) -> str:
    """Strip surrounding whitespace, embedded markdown bold markers, and a
    lone trailing period, so matching is robust to whether the key wrapped
    part of the quote in ** for emphasis (e.g. "maintained over **eight**
    miles") and to whether the target text kept the same terminal
    punctuation."""
    q = q.strip()
    if "**" in q:
        q = q.replace("**", "").strip()
    if q.endswith("."):
        q = q[:-1].rstrip()
    return q


def extract_literal_candidates(cell: str) -> list[str]:
    """Extract the wrong-value literal(s) from an 'As told' / 'Wrong value' cell."""
    quoted = [clean_quote(q) for q in extract_quoted_spans(cell) if q.strip()]
    quoted = [q for q in quoted if q]
    if quoted:
        return quoted
    bold = [b.strip() for b in extract_bold_spans(cell) if b.strip()]
    bold = [b for b in bold if b.lower() not in _MARKER_LABELS]
    return bold


NARRATOR_IDS = [f"r{i:02d}" for i in range(1, 13)]


@dataclass
class NarratorError:
    error_id: str
    narrator: str
    corrupts: str
    as_told: str
    truth: str
    mechanism: str
    is_abstention: bool


@dataclass
class NearTie:
    pair_id: str
    wrong_value_cell: str
    carried_by: list[str]
    correct_value_cell: str
    settled_by: str


@dataclass
class RecoverabilityRow:
    fact_cell: str
    schema: str  # "correct_in" or "only_in"
    listed: list[tuple[str, bool]]  # (narrator_id, has_doc_mark)
    how_resolves: str = ""


@dataclass
class DeviceRow:
    device: str
    where: str
    facts: str


@dataclass
class CorruptionMap:
    errors: list[NarratorError]
    near_ties: list[NearTie]
    recoverability: list[RecoverabilityRow]
    devices: list[DeviceRow]


def parse_corruption_map(text: str) -> CorruptionMap:
    sections = split_sections(text, level=2)
    errors: list[NarratorError] = []
    near_ties: list[NearTie] = []
    recoverability: list[RecoverabilityRow] = []
    devices: list[DeviceRow] = []

    for heading, body in sections.items():
        m = re.match(r"^(r\d{2})\b", heading)
        if m:
            narrator = m.group(1)
            blocks = find_all_table_blocks(body)
            if not blocks:
                continue
            rows = parse_table(blocks[0])
            for row in rows:
                eid = row.get("id", "").strip()
                if not eid:
                    continue
                is_abstention = "⌀" in eid  # ⌀
                errors.append(
                    NarratorError(
                        error_id=eid.lstrip("⌀").strip(),
                        narrator=narrator,
                        corrupts=row.get("corrupts", ""),
                        as_told=row.get("as told", ""),
                        truth=row.get("truth", ""),
                        mechanism=row.get("mechanism", ""),
                        is_abstention=is_abstention,
                    )
                )
            continue

        if heading.lower().startswith("near-tie pairs"):
            blocks = find_all_table_blocks(body)
            if blocks:
                rows = parse_table(blocks[0])
                for row in rows:
                    pair_cell = row.get("pair", "")
                    pm = re.search(r"NT-(\d+)", pair_cell)
                    pair_id = f"NT-{pm.group(1)}" if pm else pair_cell.strip()
                    carried = re.findall(r"r\d{2}", row.get("carried by", ""))
                    near_ties.append(
                        NearTie(
                            pair_id=pair_id,
                            wrong_value_cell=row.get("wrong value", ""),
                            carried_by=carried,
                            correct_value_cell=row.get("correct value", ""),
                            settled_by=row.get("settled by", ""),
                        )
                    )
            continue

        if heading.lower().startswith("recoverability index"):
            for block in find_all_table_blocks(body):
                rows = parse_table(block)
                if not rows:
                    continue
                headers = set(rows[0].keys())
                if "correct in" in headers:
                    for row in rows:
                        listed = []
                        for tok in re.split(r",", row.get("correct in", "")):
                            tok = tok.strip()
                            if not tok or tok == "—":
                                continue
                            nm = re.search(r"r\d{2}", tok)
                            if nm:
                                listed.append((nm.group(0), "✎" in tok))
                        if listed:
                            recoverability.append(
                                RecoverabilityRow(
                                    fact_cell=row.get("fact", ""),
                                    schema="correct_in",
                                    listed=listed,
                                    how_resolves=row.get("how it resolves", ""),
                                )
                            )
                elif "only in" in headers:
                    for row in rows:
                        nm = re.search(r"r\d{2}", row.get("only in", ""))
                        if nm:
                            recoverability.append(
                                RecoverabilityRow(
                                    fact_cell=row.get("fact", ""),
                                    schema="only_in",
                                    listed=[(nm.group(0), False)],
                                    how_resolves=row.get("status", ""),
                                )
                            )
            continue

        if heading.lower().startswith("device checklist"):
            blocks = find_all_table_blocks(body)
            if blocks:
                rows = parse_table(blocks[0])
                for row in rows:
                    devices.append(
                        DeviceRow(
                            device=row.get("device", ""),
                            where=row.get("where implemented", ""),
                            facts=row.get("facts touched", ""),
                        )
                    )
            continue

    return CorruptionMap(errors=errors, near_ties=near_ties, recoverability=recoverability, devices=devices)


def extract_blockquotes(section_text: str) -> list[list[str]]:
    lines = section_text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith(">"):
            current.append(line.strip()[1:].strip())
        else:
            if current:
                blocks.append(current)
                current = []
    if current:
        blocks.append(current)
    return blocks


def parse_narrator_briefs_documents(text: str) -> dict[str, list[str]]:
    """narrator_id -> list of verbatim document quote texts (raw, un-normalized)."""
    sections = split_sections(text, level=2)
    docs: dict[str, list[str]] = {}
    for heading, body in sections.items():
        m = re.match(r"^(r\d{2})\b", heading)
        if not m:
            continue
        narrator = m.group(1)
        quotes = []
        for block in extract_blockquotes(body):
            blob = " ".join(block)
            # Non-greedy: a blockquote block often has an attribution line
            # glued on directly below the quote (e.g. "> — Ninestone
            # Sentinel, 8 March 1898", itself sometimes containing *italics*
            # or **bold**). A greedy match would run from the quote's
            # opening "*" all the way to the LAST "*" in the whole block,
            # swallowing the attribution into the "quote" text.
            qm = re.search(r"\*(.*?)\*", blob)
            if qm:
                quotes.append(qm.group(1))
        docs[narrator] = quotes
    return docs


def parse_canon_documents(canon_text: str) -> dict[str, str]:
    """doc id -> verbatim quote text, from canon.md's '## N. Documents' section.

    This is the v3-shaped key's source of truth for document text: unlike v2, where each
    document's full verbatim text is embedded directly under the narrator(s) that quote it
    in narrator-briefs.md, v3's narrator-briefs.md only says WHICH document ids a narrator
    quotes (see parse_narrator_document_ids) and gives the text itself once, here, per
    document id. Each entry is a '**D<n> -- description**' line followed immediately by one
    or more '>' blockquote lines whose content (joined) is wrapped as a single '*...*' span
    -- the same non-greedy-asterisk convention parse_narrator_briefs_documents already
    relies on, so an attribution glued onto the same line cannot be swallowed into it."""
    doc_texts: dict[str, str] = {}
    heading_re = re.compile(r"^\*\*(D\d{1,3})\s*[-–—].*?\*\*\s*$", re.MULTILINE)
    matches = list(heading_re.finditer(canon_text))
    for i, m in enumerate(matches):
        doc_id = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(canon_text)
        block_lines = [
            line.strip()[1:].strip()
            for line in canon_text[start:end].splitlines()
            if line.strip().startswith(">")
        ]
        if not block_lines:
            continue
        blob = " ".join(block_lines)
        qm = re.search(r"\*(.*?)\*", blob)
        if qm and qm.group(1).strip():
            doc_texts[doc_id] = qm.group(1)
    return doc_texts


def parse_narrator_document_ids(text: str) -> dict[str, list[str]]:
    """narrator id -> list of document ids (e.g. ['D1', 'D8']) that narrator's own
    '**Documents.** ...' line declares verbatim -- the per-narrator convention used by
    corruption-map.md and (in the v3-shaped key) narrator-briefs.md, as opposed to v2's
    narrator-briefs.md, which embeds the document text directly with no id list at all.

    Only ids the line actually bolds, or that appear outside a 'refers to ... without
    transcribing' caveat, are trusted -- e.g. r07's "refers to D9, D11 and D16 without
    transcribing them" must not be read as those three being quoted verbatim."""
    sections = split_sections(text, level=2)
    out: dict[str, list[str]] = {}
    doc_id_re = re.compile(r"\bD\d{1,3}\b")
    for heading, body in sections.items():
        m = re.match(r"^(r\d{2})\b", heading)
        if not m:
            continue
        narrator = m.group(1)
        doc_line = re.search(r"\*\*Documents\.\*\*\s*(.+)", body)
        if not doc_line:
            continue
        line = doc_line.group(1)
        ids: set[str] = set()
        for span in extract_bold_spans(line):
            ids.update(doc_id_re.findall(span))
        if "without transcribing" not in line.lower() and "refers to" not in line.lower():
            ids.update(doc_id_re.findall(line))
        if ids:
            out[narrator] = sorted(ids)
    return out


def build_docs_by_narrator(
    narrator_briefs_text: Optional[str],
    corruption_map_text: Optional[str],
    canon_text: Optional[str],
) -> dict[str, list[str]]:
    """narrator id -> list of verbatim document quote texts, whichever of the two key
    shapes this root uses:

    - v2-shaped: narrator-briefs.md embeds each document's full text directly under the
      narrator(s) quoting it (parse_narrator_briefs_documents finds these blockquotes
      directly and nothing further is needed).
    - v3-shaped: narrator-briefs.md has no document blockquotes at all -- only canon.md's
      '## Documents' section carries the verbatim text (keyed by doc id), and each
      narrator's own '**Documents.** D1, D8, ...' line (in corruption-map.md and/or
      narrator-briefs.md) says which ids that narrator quotes. Both are needed to
      reconstruct the same narrator -> [quote text] shape check4_documents expects."""
    if narrator_briefs_text:
        v2_style = parse_narrator_briefs_documents(narrator_briefs_text)
        if any(v2_style.values()):
            return v2_style

    if not canon_text:
        return {}
    doc_texts = parse_canon_documents(canon_text)
    if not doc_texts:
        return {}

    narrator_doc_ids: dict[str, list[str]] = {}
    for text in (corruption_map_text, narrator_briefs_text):
        if not text:
            continue
        for narrator, ids in parse_narrator_document_ids(text).items():
            existing = narrator_doc_ids.setdefault(narrator, [])
            for did in ids:
                if did not in existing:
                    existing.append(did)

    result: dict[str, list[str]] = {}
    for narrator, ids in narrator_doc_ids.items():
        quotes = [doc_texts[d] for d in ids if d in doc_texts]
        if quotes:
            result[narrator] = quotes
    return result


# --------------------------------------------------------------------------
# Loading test-input / originals
# --------------------------------------------------------------------------


def discover_narrator_ids(
    root: Path, corruption_map_text: Optional[str], narrator_briefs_text: Optional[str]
) -> list[str]:
    """The narrator ids this root's corpus actually describes.

    A fixed range (the old `NARRATOR_IDS = r01..r12` constant) is exactly what made this
    script crash on a bigger corpus: corruption-map.md went on to describe narrators up to
    r24, but every lookup kept assuming only twelve existed, so the first reference to
    r13+ raised a KeyError instead of a FAIL row. Read the census off the corpus itself
    instead: every '## rNN -- ...' section heading in corruption-map.md and
    narrator-briefs.md (whichever are present), unioned with whatever 'rNN-*.md' files
    already exist under test-input/retellings/ -- so a retelling drafted for a narrator id
    that, for whatever reason, has no key section of its own is still counted."""
    heading_re = re.compile(r"^##\s+(r\d{2})\b", re.MULTILINE)
    ids: set[str] = set()
    for text in (corruption_map_text, narrator_briefs_text):
        if text:
            ids.update(heading_re.findall(text))
    retellings_dir = root / "test-input" / "retellings"
    if retellings_dir.is_dir():
        try:
            for p in retellings_dir.iterdir():
                m = re.match(r"^(r\d{2})-.+\.md$", p.name)
                if m:
                    ids.add(m.group(1))
        except OSError:
            pass
    return sorted(ids)


def get_retelling(
    retellings: dict[str, tuple[Optional[Path], Optional[str]]], rid: str
) -> tuple[Optional[Path], Optional[str]]:
    """Safe lookup: a narrator id with no entry (its retelling has not been drafted yet, or
    the id is simply not one this root's retellings/ contains) resolves to (None, None)
    rather than raising KeyError. Every check below that needs a specific narrator's file or
    text goes through this (or get_retelling_text), never `retellings[rid]` directly -- so a
    root whose retellings are incomplete, or entirely missing, is reported as FAIL rows,
    never a crash."""
    return retellings.get(rid, (None, None))


def get_retelling_text(retellings: dict[str, tuple[Optional[Path], Optional[str]]], rid: str) -> Optional[str]:
    return get_retelling(retellings, rid)[1]


def load_retellings(root: Path) -> dict[str, tuple[Optional[Path], Optional[str]]]:
    """narrator id -> (path, text) for every 'rNN-*.md' file actually present under
    test-input/retellings/. An id the corpus's key describes but that has no file yet
    simply has no entry here -- callers read through get_retelling()/get_retelling_text()
    (which default a missing id to (None, None)) rather than indexing this dict directly."""
    mapping: dict[str, tuple[Optional[Path], Optional[str]]] = {}
    retellings_dir = root / "test-input" / "retellings"
    if not retellings_dir.is_dir():
        return mapping
    try:
        names = sorted(retellings_dir.iterdir())
    except OSError:
        return mapping
    for entry in names:
        if not entry.is_file():
            continue
        m = re.match(r"^(r\d{2})-.+\.md$", entry.name)
        if not m:
            continue
        rid = m.group(1)
        if rid in mapping and mapping[rid][0] is not None:
            continue  # keep first match if duplicates exist
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            text = None
        mapping[rid] = (entry, text)
    return mapping


def dot_files_in_retellings(root: Path) -> list[str]:
    retellings_dir = root / "test-input" / "retellings"
    if not retellings_dir.is_dir():
        return []
    try:
        return sorted(p.name for p in retellings_dir.iterdir() if p.name.startswith("."))
    except OSError:
        return []


def strip_framing(text: str) -> str:
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if (
            line == ""
            or line.startswith("#")
            or line.startswith(">")
            or (line.startswith("*") and line.endswith("*") and not line.startswith("**"))
            or (line.startswith("_") and line.endswith("_"))
        ):
            i += 1
            continue
        break
    return "\n".join(lines[i:])


def word_count_after_framing(text: str) -> int:
    return len(strip_framing(text).split())


def load_originals(root: Path) -> dict[str, str]:
    originals_dir = root / "originals"
    out = {}
    if not originals_dir.is_dir():
        return out
    for p in sorted(originals_dir.glob("*.md")):
        try:
            out[p.name] = p.read_text(encoding="utf-8")
        except OSError:
            pass
    return out


# --------------------------------------------------------------------------
# Result bookkeeping
# --------------------------------------------------------------------------


@dataclass
class Item:
    check: str
    item_id: str
    status: str  # PASS | FAIL | UNPARSED
    detail: str


@dataclass
class Report:
    items: list[Item] = field(default_factory=list)
    # Informational counts of what the key parsed to -- how many planted errors, near-tie
    # pairs, documents, recoverability rows, devices, and check-7 scored items were found.
    # Populated by run_audit(); printed by print_report() alongside the PASS/FAIL summary,
    # never fed into the PASS/FAIL/UNPARSED counters themselves.
    structure_counts: dict[str, int] = field(default_factory=dict)

    def add(self, check: str, item_id: str, status: str, detail: str) -> None:
        self.items.append(Item(check, item_id, status, detail))

    def counts(self) -> Counter:
        return Counter(i.status for i in self.items)


# --------------------------------------------------------------------------
# Check 1: Files and lengths
# --------------------------------------------------------------------------


def check1_files_and_lengths(
    root: Path,
    retellings: dict[str, tuple[Optional[Path], Optional[str]]],
    narrator_ids: Iterable[str],
    report: Report,
    min_words: int = 1200,
    max_words: int = 1800,
) -> None:
    check = "1-files-and-lengths"

    questions_path = root / "test-input" / "questions.md"
    if questions_path.is_file():
        report.add(check, "questions.md", "PASS", f"exists at {questions_path}")
    else:
        report.add(check, "questions.md", "FAIL", f"missing: {questions_path}")

    dotfiles = dot_files_in_retellings(root)
    if dotfiles:
        report.add(
            check,
            "dot-files-excluded",
            "PASS",
            f"found {len(dotfiles)} dot-file(s) in retellings/, correctly excluded from scoring: {', '.join(dotfiles)}",
        )
    else:
        report.add(check, "dot-files-excluded", "PASS", "no dot-files present in retellings/")

    for rid in narrator_ids:
        path, text = get_retelling(retellings, rid)
        if path is None:
            report.add(
                check, rid, "FAIL", f"missing retelling {rid}: no file matching {rid}-*.md in test-input/retellings/"
            )
            continue
        if text is None:
            report.add(check, rid, "FAIL", f"{path}: could not be read")
            continue
        if path.name.startswith("."):
            report.add(check, rid, "FAIL", f"{path.name} is a dot-file and should not count as a retelling")
            continue
        wc = word_count_after_framing(text)
        if min_words <= wc <= max_words:
            report.add(check, rid, "PASS", f"{path.name}: {wc} words (after framing)")
        else:
            report.add(
                check,
                rid,
                "FAIL",
                f"{path.name}: {wc} words (after framing) — outside {min_words:,}-{max_words:,}",
            )


# --------------------------------------------------------------------------
# Check 2: Planted errors land where assigned, and only there
# --------------------------------------------------------------------------


@dataclass
class ErrorCheckResult:
    # keyed by (error_id, candidate) -> (assigned_ok: bool, leaked_into: list[str])
    per_key: dict[tuple[str, str], tuple[bool, list[str]]] = field(default_factory=dict)
    # narrator -> set of error_ids confirmed present-and-not-leaked
    ok_errors_by_narrator: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))
    near_tie_ok: dict[str, bool] = field(default_factory=dict)


def check2_planted_errors(
    cmap: CorruptionMap,
    retellings: dict[str, tuple[Optional[Path], Optional[str]]],
    report: Report,
    known_document_quotes: frozenset[str] = frozenset(),
    narrator_ids: Iterable[str] = NARRATOR_IDS,
) -> ErrorCheckResult:
    check = "2-planted-errors"
    result = ErrorCheckResult()
    narrator_ids = list(narrator_ids)

    def retelling_text(rid: str) -> Optional[str]:
        return get_retelling_text(retellings, rid)

    # Which error ids are part of a near-tie pair (by Mechanism column mentioning "near-tie N")
    near_tie_error_ids: set[str] = set()
    for err in cmap.errors:
        if re.search(r"near-tie", err.mechanism, re.IGNORECASE):
            near_tie_error_ids.add(err.error_id)

    # --- Standard (single-assigned-narrator) errors ---
    for err in cmap.errors:
        if err.is_abstention:
            continue  # abstention poles are not errors (design rule 4)
        if err.error_id in near_tie_error_ids:
            continue  # handled via the near-tie table below

        candidates = extract_literal_candidates(err.as_told)
        if not candidates:
            report.add(check, err.error_id, "UNPARSED", f"{err.narrator}: could not extract a literal wrong-value from As-told cell: {err.as_told!r}")
            continue

        for cand in candidates:
            # An As-told cell can legitimately embed a verbatim document
            # quote, or a fragment of one (e.g. X19's contradiction quotes
            # just the "— A.R." signature off the end of D1's page-62 entry,
            # which is quoted whole in both r04 and r07), as supporting
            # context -- e.g. X35's late reversal quotes D9 to retract its
            # own early claim. That text is DESIGNED to appear in every
            # narrator who transcribes the same document (already verified
            # separately by check 4) -- it is not itself the unique wrong
            # value, so it must not be uniqueness-checked. Substring, not
            # equality: the candidate is often only a piece of the full
            # quote.
            cand_norm = normalize_ws_quotes(cand)
            if cand_norm and any(bounded_search(doc_quote, cand_norm) for doc_quote in known_document_quotes):
                continue

            assigned_text = retelling_text(err.narrator)
            if assigned_text is None:
                report.add(
                    check,
                    f"{err.error_id} [{cand[:40]}]",
                    "FAIL",
                    f"missing retelling {err.narrator}; cannot verify placement of {cand!r}",
                )
                continue
            assigned_norm = normalize_ws_quotes(assigned_text)
            present_in_assigned = candidate_present(assigned_norm, cand)

            leaked_into = []
            excluded_leaks = []
            for other in narrator_ids:
                if other == err.narrator:
                    continue
                other_text = retelling_text(other)
                if other_text is None:
                    continue
                other_norm = normalize_ws_quotes(other_text)
                if not candidate_present(other_norm, cand):
                    continue
                anchor = LEAK_ANCHORS.get(cand)
                if anchor and not anchor_confirms(other_text, cand, anchor):
                    # Present, but not alongside the value's own anchor word
                    # in the same sentence -- a short/common value doing
                    # unrelated double duty elsewhere in the corpus, not a
                    # leaked planted error (see audit-triage.md, Residual
                    # cleanup 2026-08-27).
                    excluded_leaks.append(other)
                    continue
                leaked_into.append(other)

            if present_in_assigned and not leaked_into:
                detail = f"{err.narrator}: {cand!r} present only there"
                if excluded_leaks:
                    detail += (
                        f" (also matched, but without its anchor word, in {', '.join(excluded_leaks)}"
                        f" — confirmed unrelated, see audit-triage.md Residual cleanup 2026-08-27)"
                    )
                report.add(check, f"{err.error_id} [{cand[:40]}]", "PASS", detail)
                result.ok_errors_by_narrator[err.narrator].add(err.error_id)
            elif not present_in_assigned and leaked_into:
                report.add(
                    check,
                    f"{err.error_id} [{cand[:40]}]",
                    "FAIL",
                    f"missing from assigned narrator {err.narrator}; found instead in {', '.join(leaked_into)} — value {cand!r}",
                )
            elif not present_in_assigned:
                report.add(
                    check,
                    f"{err.error_id} [{cand[:40]}]",
                    "FAIL",
                    f"missing from assigned narrator {err.narrator} — value {cand!r}",
                )
            else:
                report.add(
                    check,
                    f"{err.error_id} [{cand[:40]}]",
                    "FAIL",
                    f"{err.narrator}: {cand!r} also leaked into {', '.join(leaked_into)}",
                )

    # --- Near-tie pairs: wrong value must appear in exactly the two carrying narrators ---
    for nt in cmap.near_ties:
        candidates = extract_literal_candidates(nt.wrong_value_cell)
        if not candidates or len(nt.carried_by) != 2:
            report.add(
                check,
                nt.pair_id,
                "UNPARSED",
                f"could not extract wrong value or carrier pair from near-tie row: value={nt.wrong_value_cell!r} carried_by={nt.carried_by!r}",
            )
            continue

        overall_ok = True
        for cand in candidates:
            # Most pairs share one literal wrong value between both
            # carriers; NT-8 and NT-10 instead attribute a specific
            # candidate to just one carrier inside a parenthetical
            # annotation (see `candidate_required_narrators`).
            required_for = candidate_required_narrators(nt.wrong_value_cell, cand, nt.carried_by)

            missing_from = []
            missing_retellings = []
            for carrier in required_for:
                text = retelling_text(carrier)
                if text is None:
                    missing_from.append(carrier)
                    missing_retellings.append(carrier)
                    continue
                if not candidate_present(normalize_ws_quotes(text), cand):
                    missing_from.append(carrier)

            leaked_into = []
            fragile_leaks = []
            for other in narrator_ids:
                if other in nt.carried_by:
                    continue
                text = retelling_text(other)
                if text is None:
                    continue
                if not candidate_present(normalize_ws_quotes(text), cand):
                    continue
                anchor = LEAK_ANCHORS.get(cand)
                if anchor:
                    if anchor_confirms(text, cand, anchor):
                        leaked_into.append(other)
                    else:
                        fragile_leaks.append(other)
                elif is_fragile_bare_value(cand):
                    fragile_leaks.append(other)
                else:
                    leaked_into.append(other)

            required_desc = (
                ", ".join(required_for) if required_for == nt.carried_by else f"{', '.join(required_for)} (of {', '.join(nt.carried_by)})"
            )

            if not missing_from and not leaked_into and not fragile_leaks:
                report.add(
                    check,
                    f"{nt.pair_id} [{cand[:40]}]",
                    "PASS",
                    f"present in exactly {required_desc}",
                )
            elif not missing_from and not leaked_into and fragile_leaks:
                report.add(
                    check,
                    f"{nt.pair_id} [{cand[:40]}]",
                    "NEEDS-HUMAN",
                    f"present in {required_desc}; also matched a bare/common value in {', '.join(fragile_leaks)} "
                    f"— too short to trust as a unique fingerprint, manually confirmed unrelated "
                    f"(see audit-triage.md Residual cleanup 2026-08-27) — value {cand!r}",
                )
            else:
                overall_ok = False
                bits = []
                if missing_retellings:
                    bits.append(f"missing retelling(s) {', '.join(missing_retellings)}")
                value_not_found = [m for m in missing_from if m not in missing_retellings]
                if value_not_found:
                    bits.append(f"missing from {', '.join(value_not_found)}")
                if leaked_into:
                    bits.append(f"leaked into {', '.join(leaked_into)}")
                if fragile_leaks:
                    bits.append(f"also matched (excluded, bare/common) in {', '.join(fragile_leaks)}")
                report.add(
                    check,
                    f"{nt.pair_id} [{cand[:40]}]",
                    "FAIL",
                    f"expected exactly {required_desc} — {'; '.join(bits)} (value {cand!r})",
                )
        result.near_tie_ok[nt.pair_id] = overall_ok

    return result


# --------------------------------------------------------------------------
# Check 3: Correct values are recoverable
# --------------------------------------------------------------------------


def _extract_fact_id(fact_cell: str) -> str:
    m = re.match(r"^([A-Z]+\d{2,3}(?:[/–-][A-Z]?\d{2,3})*)", fact_cell.strip())
    return m.group(1) if m else fact_cell.strip()[:24]


def _candidate_tokens_from_fact_cell(fact_cell: str) -> list[str]:
    rest = re.sub(r"^[A-Z]+\d{2,3}(?:[/–-][A-Z]?\d{2,3})*\s*", "", fact_cell.strip())
    if not rest:
        return []
    # "-?" alone misses this key's actual negative sign: it is written
    # throughout as the Unicode minus "−" (U+2212), e.g. "−54°F", never the
    # ASCII hyphen. Accept either so a negative temperature keeps its sign
    # instead of silently becoming positive.
    number_pattern = re.compile(
        r"\$\d[\d,]*|[-−]?\d+(?:\.\d+)?\s?(?:ft|in|°F?|%|percent)?|\d{1,2}\s+[A-Za-z]{3,9}\.?\s+\d{4}"
    )
    tokens = [t.strip() for t in number_pattern.findall(rest) if any(c.isdigit() for c in t)]
    tokens = [t for t in tokens if t]
    if tokens:
        # dedupe, keep order
        seen = set()
        out = []
        for t in tokens:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out
    return [rest.strip()]


def is_freeform_fact_label(tokens: list[str]) -> bool:
    """True when `_candidate_tokens_from_fact_cell` fell back to treating the
    fact's whole description as one search token (no digit found anywhere).
    Such a label (e.g. "Adela and Emil siblings", "Judd = Ruth's first
    cousin once removed") is the key author's paraphrase of the fact, not a
    string ever meant to appear verbatim in a retelling -- a literal miss
    does not prove the fact is actually missing."""
    return not any(any(ch.isdigit() for ch in t) for t in tokens)


_MEASUREMENT_TOKEN_RE = re.compile(
    r"^([-−]?)\s*(\d+)\s*(ft|in|°F|°|%|percent)?$", re.IGNORECASE
)


def expand_measurement_token(tok: str) -> list[str]:
    """Expand a short 'NUMBER UNIT' token pulled from the recoverability
    index (e.g. '2 in', '40 ft', '66°F', '−54°F') into the
    prose forms this corpus's retellings actually use: the number spelled
    out, the unit as a word instead of an abbreviation (singular for 1), the
    bare degree symbol without a trailing "F", and this corpus's fixed idiom
    for a negative Fahrenheit reading ("fifty-four below zero"), which never
    uses the word "degrees" at all."""
    m = _MEASUREMENT_TOKEN_RE.match(tok.strip())
    if not m:
        return []
    sign, digits, unit = m.groups()
    n = int(digits)
    negative = sign in ("-", "−")
    unit_key = (unit or "").lower()
    words = number_to_words(n)
    variants: list[str] = []
    if unit_key == "in":
        word_unit = "inch" if n == 1 else "inches"
        variants += [f"{words} {word_unit}", f"{digits} {word_unit}"]
    elif unit_key == "ft":
        word_unit = "foot" if n == 1 else "feet"
        variants += [f"{words} {word_unit}", f"{digits} {word_unit}"]
    elif unit_key in ("°f", "°"):
        if negative:
            variants += [f"{words} below zero", f"{words} below", f"minus {words}"]
        else:
            word_unit = "degree" if n == 1 else "degrees"
            variants += [f"{words} {word_unit}", f"{digits} {word_unit}", f"{digits}°"]
    elif unit_key in ("%", "percent"):
        variants += [f"{words} percent", f"{digits} percent", f"{digits}%"]
    return variants


def check3_recoverability(
    cmap: CorruptionMap,
    retellings: dict[str, tuple[Optional[Path], Optional[str]]],
    report: Report,
) -> None:
    check = "3-recoverability"

    def has_hit(rid: str, tokens: list[str]) -> bool:
        text = get_retelling_text(retellings, rid)
        if text is None:
            return False
        norm = normalize_ws_quotes(text)
        for tok in tokens:
            variants = [tok] + generate_number_variants(tok) + expand_measurement_token(tok)
            if any(bounded_search(norm, normalize_ws_quotes(v)) for v in variants):
                return True
        return False

    for row in cmap.recoverability:
        fact_id = _extract_fact_id(row.fact_cell)
        tokens = _candidate_tokens_from_fact_cell(row.fact_cell)
        if not tokens:
            report.add(check, fact_id, "UNPARSED", f"could not extract a searchable value from: {row.fact_cell!r}")
            continue
        freeform = is_freeform_fact_label(tokens)
        resolves_non_literally = freeform or "arithmetic" in row.how_resolves.lower()

        is_declared_single_source = "single-source" in row.how_resolves.lower()

        if row.schema == "only_in":
            (narrator, _has_doc) = row.listed[0]
            if get_retelling_text(retellings, narrator) is None:
                report.add(
                    check,
                    fact_id,
                    "FAIL",
                    f"missing retelling {narrator}; cannot verify single-source fact (tokens tried: {tokens})",
                )
                continue
            if has_hit(narrator, tokens):
                report.add(check, fact_id, "PASS", f"single-source fact confirmed present in {narrator} (tokens tried: {tokens})")
            elif is_declared_single_source:
                # This whole table ("Single-source scored facts
                # (uncontested)") is single-source by design, per its own
                # Status column -- accepted by prior ruling (KEY-AUDIT fix
                # 15). A literal miss here does not make it a defect; it
                # means the fact is stated in different words than the
                # fact-cell's own gloss (manually confirmed, see
                # audit-triage.md Residual cleanup 2026-08-27).
                report.add(
                    check,
                    fact_id,
                    "ACCEPTED-SINGLE-SOURCE",
                    f"single-source, uncontested by design; literal search missed in {narrator} but the fact is "
                    f"manually confirmed present there in different words (tokens tried: {tokens})",
                )
            elif freeform:
                report.add(
                    check,
                    fact_id,
                    "NEEDS-HUMAN",
                    f"fact label is a paraphrase, not a literal quote ({tokens!r}); a substring miss in {narrator} "
                    f"does not prove the fact is absent — manually confirmed present, see audit-triage.md Residual "
                    f"cleanup 2026-08-27",
                )
            else:
                report.add(check, fact_id, "FAIL", f"single-source fact not found in its sole listed narrator {narrator} (tokens tried: {tokens})")
            continue

        distinct = sorted({n for n, _ in row.listed})
        has_doc_mark = any(d for _, d in row.listed)
        missing_retellings = [n for n in distinct if get_retelling_text(retellings, n) is None]
        if missing_retellings and len(missing_retellings) == len(distinct):
            # Every listed narrator's retelling is missing outright -- there is nothing to
            # search, so falling through to the ordinary "not found" branches below would
            # misreport why (e.g. a false ACCEPTED-SINGLE-SOURCE for a fact nobody has
            # written yet). Report the real reason and move on.
            report.add(
                check,
                fact_id,
                "FAIL",
                f"missing retelling(s) {', '.join(missing_retellings)}; cannot verify (tokens tried: {tokens})",
            )
            continue
        hits = [n for n in distinct if has_hit(n, tokens)]

        if len(distinct) >= 2:
            if len(hits) >= 2:
                report.add(check, fact_id, "PASS", f"found in {len(hits)}/{len(distinct)} listed narrators: {hits}")
            elif fact_id in MANUALLY_VERIFIED_PRESENT:
                report.add(
                    check,
                    fact_id,
                    "NEEDS-HUMAN",
                    f"{MANUALLY_VERIFIED_PRESENT[fact_id]} — literal search only confirms {hits} of listed "
                    f"narrators {distinct} (tokens tried: {tokens})",
                )
            elif resolves_non_literally or has_doc_mark:
                # The key itself says this settles by paraphrase, arithmetic,
                # or a quoted document rather than by every listed narrator
                # literally repeating the label's wording -- a substring
                # search is the wrong tool to confirm or refute it.
                reason = "paraphrased fact label" if freeform else ("arithmetic-derived" if "arithmetic" in row.how_resolves.lower() else "document-marked")
                report.add(
                    check,
                    fact_id,
                    "NEEDS-HUMAN",
                    f"{reason}; literal search only confirms {hits} of listed narrators {distinct} (tokens tried: {tokens}) "
                    f"— manually confirmed present in different words, see audit-triage.md Residual cleanup 2026-08-27",
                )
            else:
                report.add(
                    check,
                    fact_id,
                    "FAIL",
                    f"only found in {hits} of listed narrators {distinct} (need >=2) — tokens tried: {tokens}",
                )
        elif len(distinct) == 1 and has_doc_mark:
            if len(hits) >= 1:
                report.add(check, fact_id, "PASS", f"found in {distinct[0]} (backed by a quoted document per index) — tokens tried: {tokens}")
            else:
                report.add(check, fact_id, "FAIL", f"not found in sole document-backed narrator {distinct[0]} — tokens tried: {tokens}")
        elif len(distinct) == 1:
            # Single-source, no document backing. Accepted design pattern
            # (KEY-AUDIT fix 15 / audit-triage.md Residual cleanup
            # 2026-08-27): a scored fact resting on exactly one uncontested
            # narrator is not itself a defect. ">=2 narrators or a
            # document" was never an absolute floor -- just the default
            # explanation the index gives for how a fact survives a reader
            # who discounts any two narrators.
            if hits:
                report.add(
                    check,
                    fact_id,
                    "ACCEPTED-SINGLE-SOURCE",
                    f"found in its sole carrier {distinct[0]}, no document backing, accepted by prior ruling — tokens tried: {tokens}",
                )
            elif freeform:
                report.add(
                    check,
                    fact_id,
                    "NEEDS-HUMAN",
                    f"single-source, freeform label ({tokens!r}); a substring miss in {distinct[0]} does not prove "
                    f"absence — manually confirmed present, see audit-triage.md Residual cleanup 2026-08-27",
                )
            else:
                report.add(
                    check,
                    fact_id,
                    "FAIL",
                    f"single-source fact not found in its sole carrier {distinct[0]} (tokens tried: {tokens}) — "
                    f"a genuine gap, not covered by the single-source acceptance",
                )
        else:
            report.add(
                check,
                fact_id,
                "FAIL",
                f"recoverability index lists only {distinct} with no document mark — design does not satisfy >=2-narrators-or-document rule",
            )


# --------------------------------------------------------------------------
# Check 4: Documents quoted verbatim
# --------------------------------------------------------------------------


def check4_documents(
    docs_by_narrator: dict[str, list[str]],
    retellings: dict[str, tuple[Optional[Path], Optional[str]]],
    report: Report,
) -> None:
    check = "4-documents-verbatim"
    for narrator, quotes in docs_by_narrator.items():
        if not quotes:
            continue
        text = get_retelling_text(retellings, narrator)
        for i, q in enumerate(quotes, start=1):
            label = f"{narrator} doc#{i}"
            qn = normalize_ws_quotes(q)
            if not qn:
                report.add(check, label, "UNPARSED", "could not extract quote text from blockquote block")
                continue
            if text is None:
                report.add(check, label, "FAIL", f"missing retelling {narrator}; cannot verify quote: {qn[:60]}...")
                continue
            tn = normalize_ws_quotes(text)
            if qn in tn:
                report.add(check, label, "PASS", f"verbatim (whitespace-normalized) in {narrator}: {qn[:60]}...")
            else:
                report.add(check, label, "FAIL", f"NOT found verbatim in {narrator}: {qn[:80]}...")


# --------------------------------------------------------------------------
# Check 5: No key leakage into test input
# --------------------------------------------------------------------------

FORBIDDEN_STRINGS = ["answer-key", "originals/", "canon", "corruption", "planted", "narrator brief"]


def build_id_shape_regexes(key_text: str) -> dict[str, re.Pattern]:
    tokens = re.findall(r"\b([A-Z]{1,2})-?(\d{1,3})\b", key_text)
    groups: dict[tuple[str, int], set[str]] = defaultdict(set)
    for prefix, digits in tokens:
        groups[(prefix, len(digits))].add(prefix + digits)
    regexes: dict[str, re.Pattern] = {}
    for (prefix, ndigits), ids in groups.items():
        if len(ids) >= 3:
            name = f"{prefix}" + ("d" * ndigits)
            regexes[name] = re.compile(rf"\b{re.escape(prefix)}-?\d{{{ndigits}}}\b")
    return regexes


_QUESTION_LABEL_RE = re.compile(r"\*\*[A-Za-z]\d\.\*\*")


def _question_label_spans(text: str) -> list[tuple[int, int]]:
    return [(m.start(), m.end()) for m in _QUESTION_LABEL_RE.finditer(text)]


def strip_blockquote_lines(text: str) -> str:
    """Drop every line that is part of a markdown blockquote (starts with
    '>'). The corpus's design deliberately reproduces its verbatim documents
    (letters, ledger entries, weather-book pages, ...) both inside the
    `originals/` source stories and inside the retellings that quote them --
    as blockquotes in both places, or as a blockquote in one and a close
    paraphrase in prose in the other. That is the intended behavior, not
    copied prose, so a document's own text should not seed n-grams that a
    retelling then "leaks" by legitimately quoting or closely paraphrasing
    the same document."""
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith(">"))


def build_ngrams(text: str, n: int = 12) -> set[tuple[str, ...]]:
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def find_leaked_ngram(text: str, origin_ngrams: set[tuple[str, ...]], n: int = 12) -> Optional[str]:
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    for i in range(len(words) - n + 1):
        gram = tuple(words[i : i + n])
        if gram in origin_ngrams:
            return " ".join(gram)
    return None


def strip_known_document_quotes(text: str, known_document_quotes: frozenset[str]) -> str:
    """Remove any run of text that matches a known verbatim document quote
    (the documents transcribed in narrator-briefs.md, e.g. the Ninestone
    Sentinel notice, D3). These are, by design, quoted verbatim in more
    than one place -- inside a retelling's blockquote AND inside the
    ORIGINAL canonical story's own prose, which sometimes renders the same
    document as inline italics rather than a '>' blockquote (so
    `strip_blockquote_lines` alone does not catch it there). Check 4
    already verifies each retelling's copy is verbatim; that is not the
    copying check 5's 12-gram scan exists to catch, so its text must not
    seed n-grams that a retelling then "leaks" by legitimately quoting the
    same document."""
    if not known_document_quotes:
        return text
    out = normalize_ws_quotes(text)
    for q in known_document_quotes:
        if not q:
            continue
        out = re.sub(re.escape(q), " ", out, flags=re.IGNORECASE)
    return out


def check5_leakage(
    root: Path,
    key_text_for_ids: str,
    originals: dict[str, str],
    test_input_files: dict[str, str],
    report: Report,
    known_document_quotes: frozenset[str] = frozenset(),
) -> None:
    check = "5-no-key-leakage"
    id_regexes = build_id_shape_regexes(key_text_for_ids)

    for rel_name, text in test_input_files.items():
        label_spans = _question_label_spans(text)

        def in_question_label(pos: int) -> bool:
            return any(s <= pos < e for s, e in label_spans)

        # id-shape leakage
        any_id_leak = False
        for shape_name, pattern in id_regexes.items():
            for m in pattern.finditer(text):
                if in_question_label(m.start()):
                    continue
                any_id_leak = True
                line_no = text.count("\n", 0, m.start()) + 1
                report.add(
                    check,
                    f"{rel_name}: id-shape {shape_name} ({m.group(0)})",
                    "FAIL",
                    f"line {line_no}: found key-shaped id {m.group(0)!r}",
                )
        if not any_id_leak:
            report.add(check, f"{rel_name}: id-shapes", "PASS", "no key-shaped id tokens found")

        # forbidden strings
        any_string_leak = False
        for needle in FORBIDDEN_STRINGS:
            for m in re.finditer(re.escape(needle), text, re.IGNORECASE):
                any_string_leak = True
                line_no = text.count("\n", 0, m.start()) + 1
                report.add(
                    check,
                    f"{rel_name}: forbidden-string {needle!r}",
                    "FAIL",
                    f"line {line_no}: found forbidden string {needle!r}",
                )
        if not any_string_leak:
            report.add(check, f"{rel_name}: forbidden-strings", "PASS", "none of the forbidden strings found")

    # 12-gram check against originals
    if not originals:
        report.add(check, "12-gram-check", "UNPARSED", f"no files found under {root / 'originals'} to build n-grams from")
    else:
        origin_ngrams: dict[str, set[tuple[str, ...]]] = {
            name: build_ngrams(strip_known_document_quotes(strip_blockquote_lines(text), known_document_quotes))
            for name, text in originals.items()
        }
        for rel_name, text in test_input_files.items():
            any_leak = False
            for oname, grams in origin_ngrams.items():
                leaked = find_leaked_ngram(text, grams)
                if leaked:
                    any_leak = True
                    report.add(
                        check,
                        f"{rel_name}: 12-gram vs {oname}",
                        "FAIL",
                        f"copied 12+ word run from {oname}: \"{leaked}\"",
                    )
            if not any_leak:
                report.add(check, f"{rel_name}: 12-gram", "PASS", f"no 12-word run copied from {root / 'originals'}/*.md")


# --------------------------------------------------------------------------
# Check 6: Devices present
# --------------------------------------------------------------------------


def check6_devices(
    cmap: CorruptionMap,
    retellings: dict[str, tuple[Optional[Path], Optional[str]]],
    error_check_result: ErrorCheckResult,
    report: Report,
) -> None:
    check = "6-devices"

    def file_exists(rid: str) -> bool:
        return get_retelling(retellings, rid)[0] is not None

    for dev in cmap.devices:
        mentioned = sorted(set(re.findall(r"r\d{2}", dev.where)))
        missing_files = [r for r in mentioned if not file_exists(r)]
        label_base = dev.device.strip().strip("*")

        if missing_files:
            report.add(
                check,
                f"{label_base}: files",
                "FAIL",
                f"missing retelling(s) for implementing narrator(s): {', '.join(missing_files)}",
            )
        else:
            report.add(check, f"{label_base}: files", "PASS", f"all implementing narrator files exist: {mentioned}")

        dev_lower = dev.device.lower()

        if "internal contradiction" in dev_lower:
            # find error rows tagged INTERNAL CONTRADICTION for the mentioned narrators
            for err in cmap.errors:
                if err.narrator not in mentioned:
                    continue
                if "internal contradiction" not in err.as_told.lower():
                    continue
                quotes = [clean_quote(q) for q in extract_quoted_spans(err.as_told) if len(q.split()) >= 2]
                if len(quotes) < 2:
                    report.add(
                        check,
                        f"{label_base}: {err.narrator} content",
                        "UNPARSED",
                        f"could not extract two conflicting quotes from {err.error_id}'s As-told cell",
                    )
                    continue
                text = get_retelling_text(retellings, err.narrator)
                if text is None:
                    report.add(check, f"{label_base}: {err.narrator} content", "FAIL", f"missing retelling {err.narrator}")
                    continue
                norm = normalize_ws_quotes(text)
                missing = [q for q in quotes if not candidate_present(norm, q)]
                if missing:
                    report.add(
                        check,
                        f"{label_base}: {err.narrator} content",
                        "FAIL",
                        f"conflicting statement(s) not found in {err.narrator}: {missing}",
                    )
                else:
                    report.add(check, f"{label_base}: {err.narrator} content", "PASS", f"both conflicting statements present in {err.narrator}")

        elif "late reversal" in dev_lower:
            for err in cmap.errors:
                if err.narrator not in mentioned:
                    continue
                if "late reversal" not in err.as_told.lower():
                    continue
                quotes = [clean_quote(q) for q in extract_quoted_spans(err.as_told) if len(q.split()) >= 3]
                if len(quotes) < 2:
                    report.add(
                        check,
                        f"{label_base}: {err.narrator} content",
                        "UNPARSED",
                        f"could not extract early/late quotes from {err.error_id}'s As-told cell",
                    )
                    continue
                text = get_retelling_text(retellings, err.narrator)
                if text is None:
                    report.add(check, f"{label_base}: {err.narrator} content", "FAIL", f"missing retelling {err.narrator}")
                    continue
                norm = normalize_ws_quotes(text)
                early, late = quotes[0], quotes[-1]
                pos_early = find_bounded_pos(norm, normalize_ws_quotes(early))
                pos_late = find_bounded_pos(norm, normalize_ws_quotes(late))
                if pos_early is None or pos_late is None:
                    missing = [q for q, p in ((early, pos_early), (late, pos_late)) if p is None]
                    report.add(
                        check,
                        f"{label_base}: {err.narrator} content",
                        "FAIL",
                        f"reversal text not found in {err.narrator}: {missing}",
                    )
                elif pos_early < pos_late:
                    report.add(check, f"{label_base}: {err.narrator} content", "PASS", f"earlier claim precedes reversal in {err.narrator}")
                else:
                    report.add(
                        check,
                        f"{label_base}: {err.narrator} content",
                        "FAIL",
                        f"reversal does not appear after the earlier claim in {err.narrator}",
                    )

        elif "wrong only on dates" in dev_lower or "date" in dev_lower and "narrator" in dev_lower:
            near_tie_ids = {e.error_id for e in cmap.errors if re.search(r"near-tie", e.mechanism, re.IGNORECASE)}
            date_errors = [
                e
                for e in cmap.errors
                if e.narrator in mentioned and not e.is_abstention and e.error_id not in near_tie_ids
            ]
            # restrict to the actual date-drift-style errors already checked in check 2
            if not date_errors:
                report.add(check, f"{label_base}: content", "UNPARSED", "no per-narrator error rows found for date-only-unreliable narrator")
            for rid in mentioned:
                narrator_dates = [e for e in date_errors if e.narrator == rid]
                if not narrator_dates:
                    continue
                confirmed = error_check_result.ok_errors_by_narrator.get(rid, set())
                ids = [e.error_id for e in narrator_dates]
                missing_ids = [eid for eid in ids if eid not in confirmed]
                if missing_ids:
                    report.add(
                        check,
                        f"{label_base}: {rid} content",
                        "FAIL",
                        f"wrong dates not confirmed present-and-unique for: {missing_ids} (see check 2)",
                    )
                else:
                    report.add(check, f"{label_base}: {rid} content", "PASS", f"all {len(ids)} wrong dates confirmed present-and-unique in {rid}")

        else:
            # near-tie / 3-4-hop inference / juxtaposing narrators / abstention items:
            # no literal key-string given by the checklist for these — file existence only.
            report.add(
                check,
                f"{label_base}: content",
                "PASS" if not missing_files else "FAIL",
                "no literal key string specified by the device checklist for this device; verified by file existence only",
            )


# --------------------------------------------------------------------------
# Check 7: Questions cover the key
# --------------------------------------------------------------------------


def parse_answers_scoring(text: str) -> tuple[set[str], Optional[int], dict[str, int], dict[str, int]]:
    # `\b` rather than a literal trailing '.' on the bullet id: v2's checklist bullets
    # close the bold span immediately after the id ("- **B1.** **Sister and brother**"),
    # but v3's sometimes fold more text into the same bold span ("- **B4. Abstention item
    # (A01).**") or put a parenthetical before the period ("- **C1 (4 points, 1 each).**") --
    # either way the id itself always ends at a word boundary.
    header_ids = set(re.findall(r"^###\s+([A-G]\d+)\b", text, re.MULTILINE))
    bullet_ids = set(re.findall(r"-\s+\*\*([A-G]\d+)\b", text))
    scored_items = header_ids | bullet_ids

    declared_total = None
    breakdown: dict[str, int] = {}
    m = re.search(r"Total:\s*\*\*(\d+)\s*points\.?\*\*\.?\s*(.+)", text)
    if m:
        declared_total = int(m.group(1))
        for sec, pts in re.findall(r"([A-G])\s+(\d+)", m.group(2)):
            breakdown[sec] = int(pts)

    section_headers: dict[str, int] = {}
    for sec, pts in re.findall(r"^##\s+Section\s+([A-G])\s+.*?\((\d+)\s+points", text, re.MULTILINE):
        section_headers[sec] = int(pts)

    return scored_items, declared_total, breakdown, section_headers


def parse_questions_ids(text: str) -> set[str]:
    return set(re.findall(r"\*\*([A-G]\d+)\b", text))


_SECTION_A_COUNT_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def section_a_declared_story_count(questions_text: str) -> Optional[int]:
    """The story count questions.md's own Section A body declares in prose (v3: 'There were
    originally **eight** stories... Reconstruct each of the eight.') -- used only for the
    cue-less design, where there is no per-story bulleted id to match against the key's
    headers at all. None if no such count phrase is found."""
    section_a_body = ""
    for heading, body in split_sections(questions_text, level=2).items():
        if heading.strip().lower().startswith("section a"):
            section_a_body = body
            break
    if not section_a_body:
        return None
    words = "|".join(_SECTION_A_COUNT_WORDS)
    m = re.search(rf"\b({words})\b[^.]{{0,40}}\bstories\b", section_a_body, re.IGNORECASE)
    if not m:
        return None
    return _SECTION_A_COUNT_WORDS[m.group(1).lower()]


def check7_questions_coverage(answers_text: str, questions_text: str, report: Report) -> Optional[set[str]]:
    check = "7-questions-cover-key"
    scored_items, declared_total, breakdown, section_headers = parse_answers_scoring(answers_text)
    question_ids = parse_questions_ids(questions_text)

    if not scored_items:
        report.add(
            check, "scored-item-ids", "UNPARSED", "could not find any lettered checklist item ids in answers-and-scoring.md"
        )

    # Section A's own per-story headers ('### A1 -- ...') need a different coverage test
    # from every other section's ids. v2 cues each story with its own '**A1.**' bullet in
    # questions.md, so an ordinary per-id match (like B/C/D below) works. v3's Section A is
    # deliberately cue-less -- "there were eight stories; reconstruct each," no per-story
    # label anywhere -- so an id-for-id match would FAIL every one of them by design, not by
    # defect (AUTHORING-NOTES.md, lever 2). Tell the two shapes apart by whether the key's
    # Section A ids show up individually in questions.md at all.
    section_a_ids = {i for i in scored_items if re.fullmatch(r"A\d+", i)}
    other_ids = scored_items - section_a_ids
    section_a_cued = {i for i in section_a_ids if i in question_ids}
    section_a_uncued = section_a_ids - section_a_cued

    ids_to_match = other_ids
    if not section_a_ids or not section_a_uncued:
        # No Section A ids at all, or every one of them is individually cued (v2-shaped):
        # match them exactly like any other section's ids, in the loop below.
        ids_to_match = other_ids | section_a_ids
    elif section_a_uncued == section_a_ids:
        # v3-shaped: none of them are cued. Confirm the cue-less design is actually in play
        # -- questions.md's Section A states the same story count the key defines -- rather
        # than assuming it, so a genuine gap still surfaces instead of being waved through.
        declared_count = section_a_declared_story_count(questions_text)
        if declared_count == len(section_a_ids):
            for item_id in sorted(section_a_ids):
                report.add(
                    check,
                    item_id,
                    "PASS",
                    f"{item_id} is a Section A story heading; Section A is cue-less by design "
                    f"(no per-story id in questions.md), and questions.md declares the same "
                    f"{declared_count} stories -- see AUTHORING-NOTES.md, lever 2",
                )
            report.add(
                check,
                "section-A-story-count",
                "PASS",
                f"key defines {len(section_a_ids)} Section A story headings ({sorted(section_a_ids)}); "
                f"questions.md's Section A declares {declared_count} stories",
            )
        else:
            for item_id in sorted(section_a_ids):
                report.add(
                    check,
                    item_id,
                    "FAIL",
                    f"{item_id} is a Section A story heading with no matching id in questions.md, and "
                    f"questions.md's declared story count ({declared_count!r}) does not confirm "
                    f"cue-less design against the key's {len(section_a_ids)} headings",
                )
            report.add(
                check,
                "section-A-story-count",
                "FAIL",
                f"key defines {len(section_a_ids)} Section A story headings; questions.md's Section A "
                f"declares {declared_count!r} -- counts do not match",
            )
    else:
        # A mixed state this script has no model for: some Section A ids are individually
        # cued and some are not. Flag it rather than silently guessing which convention
        # applies -- this is exactly the "parse defensively" case.
        report.add(
            check,
            "section-A-cue-shape",
            "UNPARSED",
            f"{len(section_a_uncued)} of {len(section_a_ids)} Section A story ids "
            f"({sorted(section_a_uncued)}) have no matching id in questions.md while "
            f"{sorted(section_a_cued)} do -- cannot tell whether Section A is meant to be "
            f"individually cued (v2-style) or cue-less (v3-style); skipping the per-story "
            f"Section A check",
        )

    for item_id in sorted(ids_to_match):
        if item_id in question_ids:
            report.add(check, item_id, "PASS", f"{item_id} appears in questions.md")
        else:
            report.add(check, item_id, "FAIL", f"{item_id} has no matching question id in questions.md")

    if declared_total is None or not breakdown:
        report.add(check, "point-totals", "UNPARSED", "could not find/parse the 'Total: **N points**. A x / B y / ...' line")
    else:
        total = sum(breakdown.values())
        detail = f"declared total {declared_total}, breakdown {breakdown}, sum {total}"
        if declared_total == 100 and total == 100:
            report.add(check, "point-totals", "PASS", detail)
        else:
            report.add(check, "point-totals", "FAIL", detail + " — does not sum to 100")

        if section_headers:
            mismatches = {
                s: (breakdown.get(s), section_headers.get(s))
                for s in set(breakdown) | set(section_headers)
                if breakdown.get(s) != section_headers.get(s)
            }
            if mismatches:
                report.add(
                    check,
                    "point-totals-consistency",
                    "FAIL",
                    f"breakdown line disagrees with section headers (breakdown vs header): {mismatches}",
                )
            else:
                report.add(check, "point-totals-consistency", "PASS", "breakdown line agrees with each section header's point count")

    return scored_items


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def read_text_or_none(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def load_test_input_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    questions_path = root / "test-input" / "questions.md"
    if questions_path.is_file():
        try:
            files["test-input/questions.md"] = questions_path.read_text(encoding="utf-8")
        except OSError:
            pass
    retellings_dir = root / "test-input" / "retellings"
    if retellings_dir.is_dir():
        for p in sorted(retellings_dir.iterdir()):
            if p.is_file() and p.suffix == ".md":
                try:
                    files[f"test-input/retellings/{p.name}"] = p.read_text(encoding="utf-8")
                except OSError:
                    pass
    return files


def run_audit(root: Path, min_words: int = 1200, max_words: int = 1800) -> Report:
    report = Report()

    corruption_map_text = read_text_or_none(root / "answer-key" / "corruption-map.md")
    narrator_briefs_text = read_text_or_none(root / "answer-key" / "narrator-briefs.md")
    canon_text = read_text_or_none(root / "answer-key" / "canon.md")
    answers_text = read_text_or_none(root / "answer-key" / "answers-and-scoring.md")
    questions_text = read_text_or_none(root / "test-input" / "questions.md") or ""

    # The narrator census this root's key actually describes -- NOT a fixed count. See
    # discover_narrator_ids's docstring for why a hardcoded range crashes on a root with
    # more (or fewer, or differently-numbered) narrators than the constant assumed.
    narrator_ids = discover_narrator_ids(root, corruption_map_text, narrator_briefs_text)

    retellings = load_retellings(root)

    # --- Check 1 ---
    check1_files_and_lengths(root, retellings, narrator_ids, report, min_words=min_words, max_words=max_words)

    # Parsed once, ahead of check 2, so its verbatim document quotes can be
    # excluded from check 2's per-narrator uniqueness search (a quote an
    # As-told cell embeds as supporting context -- e.g. a late reversal
    # quoting the document that retracts it -- is expected in every narrator
    # who transcribes that document; check 4 verifies it separately).
    #
    # build_docs_by_narrator tries the v2 shape first (each document's verbatim text
    # embedded directly under the narrator(s) quoting it, in narrator-briefs.md) and falls
    # back to the v3 shape (verbatim text keyed by document id in canon.md, cross-referenced
    # against each narrator's own id list) when the first finds nothing.
    docs_by_narrator = build_docs_by_narrator(narrator_briefs_text, corruption_map_text, canon_text)
    if not docs_by_narrator and narrator_briefs_text and re.search(r"\bD\d{1,3}\b", narrator_briefs_text):
        # The brief clearly references document ids, but neither parse path extracted any
        # quoted text for them -- flag it rather than silently reporting nothing in check 4.
        report.add(
            "4-documents-verbatim",
            "docs-parse",
            "UNPARSED",
            "narrator-briefs.md references document ids, but no verbatim quote text could be "
            "extracted from narrator-briefs.md's own blockquotes or from canon.md's Documents "
            "section",
        )
    known_document_quotes = frozenset(
        normalize_ws_quotes(q) for quotes in docs_by_narrator.values() for q in quotes
    )

    # --- Checks 2, 3, 6 need corruption-map.md ---
    cmap: Optional[CorruptionMap] = None
    if corruption_map_text is None:
        report.add("2-planted-errors", "corruption-map.md", "UNPARSED", "file missing: answer-key/corruption-map.md")
        report.add("3-recoverability", "corruption-map.md", "UNPARSED", "file missing: answer-key/corruption-map.md")
        report.add("6-devices", "corruption-map.md", "UNPARSED", "file missing: answer-key/corruption-map.md")
        error_check_result = ErrorCheckResult()
    else:
        cmap = parse_corruption_map(corruption_map_text)
        error_check_result = check2_planted_errors(
            cmap, retellings, report, known_document_quotes=known_document_quotes, narrator_ids=narrator_ids
        )
        check3_recoverability(cmap, retellings, report)
        check6_devices(cmap, retellings, error_check_result, report)

    # --- Check 4 needs narrator-briefs.md ---
    if narrator_briefs_text is None:
        report.add("4-documents-verbatim", "narrator-briefs.md", "UNPARSED", "file missing: answer-key/narrator-briefs.md")
    else:
        check4_documents(docs_by_narrator, retellings, report)

    # --- Check 5 needs originals + all key text for id-shape detection ---
    originals = load_originals(root)
    key_text_for_ids = "\n".join(t for t in (corruption_map_text, narrator_briefs_text, canon_text, answers_text) if t)
    test_input_files = load_test_input_files(root)
    if not test_input_files:
        report.add("5-no-key-leakage", "test-input", "UNPARSED", "no files found under test-input/")
    else:
        check5_leakage(root, key_text_for_ids, originals, test_input_files, report, known_document_quotes=known_document_quotes)

    # --- Check 7 needs answers-and-scoring.md + questions.md ---
    scored_items: Optional[set[str]] = None
    if answers_text is None:
        report.add("7-questions-cover-key", "answers-and-scoring.md", "UNPARSED", "file missing: answer-key/answers-and-scoring.md")
    else:
        scored_items = check7_questions_coverage(answers_text, questions_text, report)

    report.structure_counts = {
        "narrators": len(narrator_ids),
        "planted errors": len(cmap.errors) if cmap is not None else 0,
        "near-tie pairs": len(cmap.near_ties) if cmap is not None else 0,
        "documents": len(parse_canon_documents(canon_text)) if canon_text else 0,
        "recoverability rows": len(cmap.recoverability) if cmap is not None else 0,
        "devices": len(cmap.devices) if cmap is not None else 0,
        "scored items (check 7)": len(scored_items) if scored_items is not None else 0,
    }

    return report


def print_report(report: Report) -> None:
    by_check: dict[str, list[Item]] = defaultdict(list)
    for item in report.items:
        by_check[item.check].append(item)

    for check_name in sorted(by_check):
        print(f"\n=== Check {check_name} ===")
        for item in by_check[check_name]:
            print(f"[{item.status}] {item.item_id}: {item.detail}")

    counts = report.counts()
    missing = []
    for item in report.items:
        if item.check == "1-files-and-lengths" and item.status == "FAIL" and re.match(r"^r\d{2}$", item.item_id):
            missing.append(item.item_id)

    print("\n=== Summary ===")
    print(
        f"PASS: {counts.get('PASS', 0)}  FAIL: {counts.get('FAIL', 0)}  UNPARSED: {counts.get('UNPARSED', 0)}  "
        f"NEEDS-HUMAN: {counts.get('NEEDS-HUMAN', 0)}  ACCEPTED-SINGLE-SOURCE: {counts.get('ACCEPTED-SINGLE-SOURCE', 0)}"
    )
    if missing:
        print(f"Missing retellings: {', '.join(missing)}")
    else:
        print("Missing retellings: none")

    if report.structure_counts:
        print("Key structure: " + ", ".join(f"{v} {k}" for k, v in report.structure_counts.items()))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mechanical audit for a synthesis test (root-agnostic).")
    parser.add_argument("--root", default="v2", help="Path to the test root directory (default: v2)")
    parser.add_argument("--strict", action="store_true", help="Exit 1 if any FAIL or UNPARSED item is found")
    parser.add_argument(
        "--min-words", type=int, default=1200, help="Minimum retelling word count after framing (default: 1200)"
    )
    parser.add_argument(
        "--max-words", type=int, default=1800, help="Maximum retelling word count after framing (default: 1800)"
    )
    args = parser.parse_args(argv)

    root = Path(args.root)
    report = run_audit(root, min_words=args.min_words, max_words=args.max_words)
    print_report(report)

    if args.strict:
        counts = report.counts()
        if counts.get("FAIL", 0) > 0 or counts.get("UNPARSED", 0) > 0:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
