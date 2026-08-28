"""Tests for the v2 mechanical audit (audit.py).

Builds a tiny fake `v2`-shaped root under tmp_path with two real narrators
(r01, r02) plus references to two narrators that are never given a
retelling file (r03, r09, standing in for "not authored yet"), and checks
that every one of the seven checks reports the right PASS/FAIL/UNPARSED.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

import audit


# --------------------------------------------------------------------------
# Fixture: a tiny fake v2 root
# --------------------------------------------------------------------------

CORRUPTION_MAP_MD = """\
# Corruption Map, vTest (SECRET)

Design rules placeholder.

---

## r01 — Alice, a witness

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | The bridge was **red**. | Blue. | Off-by-color |
| X02 | F002 | Sheet 3 called for **four feet** of clearance. | **Three feet.** | **Near-tie 1** (partner r02) |
| X04 | F005 | **INTERNAL CONTRADICTION.** Early: "I saw nobody there that day." Late: "I saw him standing by the bridge that morning." | He was there. | Self-contradiction |
| X05 | F006 | The flag was **green**. | Yellow. | Off-by-color |
| X07 | F009 | There were **twelve widgets** in the crate. | Ten. | **Near-tie 2** (partner r03) |

---

## r02 — Bob, an engineer

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X03 | F002 | The span specified **four feet** of clearance. | **Three feet.** | **Near-tie 1** (partner r01) |
| X06 | F010 | The survey was made in **1899**. | 1900. | Date drift |

---

## r03 — Carol, a clerk (never authored)

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X08 | F011 | The gate was locked in **March**. | April. | Off-by-month |
| X09 | F009 | There were **twelve widgets** counted. | Ten. | **Near-tie 2** (partner r01) |

---

## r04 — Dana, a witness (never authored)

Placeholder section; no retelling was ever written for this narrator in the fixture.

---

## r05 — Eli, a witness (never authored)

Placeholder section; no retelling was ever written for this narrator in the fixture.

---

## r12 — Mallory, a witness (never authored)

Placeholder section; no retelling was ever written for this narrator in the fixture.

---

## Near-tie pairs (explicit)

| Pair | Wrong value | Carried by | Correct value | Settled by |
|---|---|---|---|---|
| **NT-1** | Sheet 3 specified **4 feet** of clearance | r01, r02 | **3 feet** | a survey document |
| **NT-2** | **twelve widgets** in the crate | r01, r03 | **ten widgets** | a ledger |

---

## Recoverability index

### Places and events

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F003 the town was called Millbrook | r01, r02 | — | Majority |
| F004 the population was 500 | r01, r02 | — | Majority |

### Single-source scored facts (uncontested)

| Fact | Only in | Status |
|---|---|---|
| F007 the founder was named Sam | r01 | Single-source, uncontested |

---

## Device checklist (Spec D3)

| Device | Where implemented | Facts touched |
|---|---|---|
| **Internal contradictions in one retelling** | **r01** | F005 |
| **Near-tie error broken only by a quoted document** | r01, r02 | F002 |
| **A narrator wrong only on dates** | **r02** | F010 |
| **Two or more narrators juxtaposing separate stories** | r01, r09 | F001 |
"""

NARRATOR_BRIEFS_MD = """\
# Narrator Briefs, vTest

## r01 — Alice, a witness

**Documents she quotes verbatim.**

> *The bridge measured two hundred feet across, per the county survey.*
> — county survey, 1889

---

## r02 — Bob, an engineer

**Documents he quotes verbatim.**

> *The span was built to a clearance of three feet, confirmed by inspection.*
> — inspection report, 1901
"""

CANON_MD = """\
# Canon, vTest

F001, F002, F003, F004, F005, F006, F007, F009, F010, F011 are all defined elsewhere.
"""

ANSWERS_SCORING_MD = """\
# Answers & Scoring Key, vTest

Total: **100 points.** A 60 / B 40.

## Section A — Reconstruction (60 points)

### A1 — thing one (30 points)

1. blah **F001**

### A2 — thing two (30 points)

1. blah **F002**

## Section B — Relationships (40 points)

- **B1.** blah blah **F003** — 20.
- **B2.** blah blah **F004** — 20.
"""

QUESTIONS_MD = """\
# Test Questions (fixture)

Some intro text with an accidental leaked id F004 sitting bare in a sentence, and a
mention of the corruption in local governance which should trip a different check.

## Section A

- **A1.** Question one text.
- **A2.** Question two text.

## Section B

- **B1.** Question three text.
"""

# The 12-word (or longer) sentence that will be deliberately leaked into r01's retelling.
ORIGINAL_SENTENCE = (
    "The old mill by the river had stood empty for thirty long years before anyone dared to return."
)

ORIGINALS_MD = f"""\
# Story One — The Old Mill

{ORIGINAL_SENTENCE} Nobody in the valley could say exactly why.
"""


def _padded_body(required_sentences: list[str], target_words: int) -> str:
    """Join required sentences with filler until the word count lands >= target_words
    (and comfortably under 1800), using audit.py's own word-count convention."""
    body = " ".join(required_sentences)
    filler_phrase = "This is a plain filler sentence added only to reach the required length."
    filler_words = len(filler_phrase.split())
    while len(body.split()) < target_words:
        body += " " + filler_phrase
    return body


@pytest.fixture
def fake_root(tmp_path) -> Path:
    root = tmp_path / "v2"
    (root / "answer-key").mkdir(parents=True)
    (root / "test-input" / "retellings").mkdir(parents=True)
    (root / "originals").mkdir(parents=True)

    (root / "answer-key" / "corruption-map.md").write_text(CORRUPTION_MAP_MD, encoding="utf-8")
    (root / "answer-key" / "narrator-briefs.md").write_text(NARRATOR_BRIEFS_MD, encoding="utf-8")
    (root / "answer-key" / "canon.md").write_text(CANON_MD, encoding="utf-8")
    (root / "answer-key" / "answers-and-scoring.md").write_text(ANSWERS_SCORING_MD, encoding="utf-8")
    (root / "test-input" / "questions.md").write_text(QUESTIONS_MD, encoding="utf-8")
    (root / "originals" / "01-the-old-mill.md").write_text(ORIGINALS_MD, encoding="utf-8")

    # r01: in-range word count (~1300 words), carries X01/X02/X04/X05/X07's assigned
    # values, the near-tie values, the recoverability tokens, a document quote that
    # does NOT match verbatim (deliberate FAIL), and the leaked 12-gram from originals.
    r01_required = [
        "I remember the bridge was red, though everyone else disagreed with me about the color.",
        "Sheet 3 called for four feet of clearance, and I was there when they measured it out.",
        "There were twelve widgets in the crate when I counted them myself that afternoon.",
        "I saw nobody there that day. That is exactly what I told the sheriff at the time.",
        "Weeks later I changed my story and said something different to the same sheriff.",
        "I saw him standing by the bridge that morning. I have never forgotten it since.",
        "The flag was green, plain as anything, whatever anyone else remembers about it.",
        "Everyone agreed that the town was called Millbrook, and had been for generations.",
        "The population was 500 that year, according to the count I took myself.",
        "Everyone knew that the founder was named Sam, and nobody argued about it.",
        "According to the old county survey, the bridge was about two hundred feet long.",
        ORIGINAL_SENTENCE,
    ]
    r01_text = "# r01 — Alice, a witness\n\n" + _padded_body(r01_required, target_words=1300)
    (root / "test-input" / "retellings" / "r01-alice.md").write_text(r01_text, encoding="utf-8")

    # r02: deliberately SHORT (out of the 1,200-1,800 range), carries X03's assigned
    # near-tie value, the standalone date error 1899 (assigned only to r02), the
    # leaked "green" (should NOT be there per the key, testing the leak-detection
    # FAIL path), Millbrook (recoverability PASS partner) but NOT the 500 population
    # figure (recoverability FAIL partner), and a document quote that DOES match
    # verbatim.
    r02_text = (
        "# r02 — Bob, an engineer\n\n"
        "The span specified four feet of clearance, confirmed against the drawings. "
        "The survey was made in 1899, according to my own notes. "
        "Everyone agreed that the town was called Millbrook, and had been for generations. "
        "Oddly enough somebody down the road also mentioned the flag was green that year. "
        "The span was built to a clearance of three feet, confirmed by inspection."
    )
    (root / "test-input" / "retellings" / "r02-bob.md").write_text(r02_text, encoding="utf-8")

    return root


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def statuses(report: audit.Report, check: str, contains: str) -> list[str]:
    return [i.status for i in report.items if i.check == check and contains in i.item_id]


def one_status(report: audit.Report, check: str, contains: str) -> str:
    found = statuses(report, check, contains)
    assert found, f"no item found for check={check!r} contains={contains!r}"
    assert len(found) == 1, f"expected exactly one match for {contains!r}, got {found}"
    return found[0]


def exact_status(report: audit.Report, check: str, item_id: str) -> str:
    found = [i.status for i in report.items if i.check == check and i.item_id == item_id]
    assert found, f"no item found for check={check!r} item_id={item_id!r}"
    assert len(found) == 1, f"expected exactly one match for {item_id!r}, got {found}"
    return found[0]


# --------------------------------------------------------------------------
# Check 1: files and lengths
# --------------------------------------------------------------------------


def test_check1_questions_md_exists(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "1-files-and-lengths", "questions.md") == "PASS"


def test_check1_r01_in_range_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "1-files-and-lengths", "r01") == "PASS"


def test_check1_r02_too_short_fails(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "1-files-and-lengths", "r02") == "FAIL"


def test_check1_missing_narrators_reported_as_failures(fake_root):
    report = audit.run_audit(fake_root)
    # r03..r12 were never authored in this fixture.
    for rid in ["r03", "r04", "r05", "r12"]:
        assert one_status(report, "1-files-and-lengths", rid) == "FAIL"


# --------------------------------------------------------------------------
# Check 2: planted errors land where assigned, and only there
# --------------------------------------------------------------------------


def test_check2_standalone_error_present_only_in_assigned_narrator_passes(fake_root):
    report = audit.run_audit(fake_root)
    # X01 "red" is assigned to r01 only, and r02's text never mentions red.
    assert one_status(report, "2-planted-errors", "X01") == "PASS"


def test_check2_leaked_error_fails(fake_root):
    report = audit.run_audit(fake_root)
    # X05 "green" is assigned to r01 only, but the fixture deliberately also
    # puts "green" in r02 -> must be reported as a leak.
    assert one_status(report, "2-planted-errors", "X05") == "FAIL"


def test_check2_missing_assigned_narrator_fails(fake_root):
    report = audit.run_audit(fake_root)
    # X08 is assigned to r03, which was never authored.
    assert one_status(report, "2-planted-errors", "X08") == "FAIL"


def test_check2_internal_contradiction_quotes_each_checked(fake_root):
    report = audit.run_audit(fake_root)
    found = [i for i in report.items if i.check == "2-planted-errors" and i.item_id.startswith("X04")]
    assert len(found) == 2
    assert all(i.status == "PASS" for i in found)


def test_check2_near_tie_present_in_exactly_both_carriers_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "2-planted-errors", "NT-1") == "PASS"


def test_check2_near_tie_missing_from_one_carrier_fails(fake_root):
    report = audit.run_audit(fake_root)
    # NT-2 is carried by r01 (has it) and r03 (never authored) -> FAIL.
    assert one_status(report, "2-planted-errors", "NT-2") == "FAIL"


# --------------------------------------------------------------------------
# Check 3: correct values are recoverable
# --------------------------------------------------------------------------


def test_check3_fact_in_two_narrators_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "3-recoverability", "F003") == "PASS"


def test_check3_fact_in_only_one_of_two_listed_narrators_fails(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "3-recoverability", "F004") == "FAIL"


def test_check3_single_source_fact_confirmed_present_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "3-recoverability", "F007") == "PASS"


# --------------------------------------------------------------------------
# Check 4: documents quoted verbatim
# --------------------------------------------------------------------------


def test_check4_verbatim_quote_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "4-documents-verbatim", "r02 doc#1") == "PASS"


def test_check4_paraphrased_quote_fails(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "4-documents-verbatim", "r01 doc#1") == "FAIL"


# --------------------------------------------------------------------------
# Check 5: no key leakage into test input
# --------------------------------------------------------------------------


def test_check5_id_shape_leak_detected_in_questions(fake_root):
    report = audit.run_audit(fake_root)
    found = [
        i
        for i in report.items
        if i.check == "5-no-key-leakage" and "questions.md" in i.item_id and "id-shape" in i.item_id
    ]
    assert any(i.status == "FAIL" for i in found)


def test_check5_forbidden_string_leak_detected_in_questions(fake_root):
    report = audit.run_audit(fake_root)
    found = [
        i
        for i in report.items
        if i.check == "5-no-key-leakage" and "questions.md" in i.item_id and "forbidden-string" in i.item_id
    ]
    assert any(i.status == "FAIL" for i in found)


def test_check5_twelve_gram_leak_detected_in_r01(fake_root):
    report = audit.run_audit(fake_root)
    found = [
        i
        for i in report.items
        if i.check == "5-no-key-leakage" and "r01" in i.item_id and "12-gram" in i.item_id
    ]
    assert any(i.status == "FAIL" for i in found)


def test_check5_r02_has_no_leakage(fake_root):
    report = audit.run_audit(fake_root)
    r02_items = [i for i in report.items if i.check == "5-no-key-leakage" and "r02-bob.md" in i.item_id]
    assert r02_items
    assert all(i.status == "PASS" for i in r02_items)


# --------------------------------------------------------------------------
# Check 6: devices present
# --------------------------------------------------------------------------


def test_check6_internal_contradiction_device_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "6-devices", "Internal contradictions in one retelling: r01 content") == "PASS"


def test_check6_date_only_narrator_device_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert one_status(report, "6-devices", "A narrator wrong only on dates: r02 content") == "PASS"


def test_check6_generic_device_with_existing_files_passes(fake_root):
    report = audit.run_audit(fake_root)
    assert (
        one_status(report, "6-devices", "Near-tie error broken only by a quoted document: files") == "PASS"
    )


def test_check6_generic_device_with_missing_file_fails(fake_root):
    report = audit.run_audit(fake_root)
    # r09 is mentioned but never authored (and never even appears in the
    # corruption map's own narrator sections) -> the device's file check fails.
    assert (
        one_status(report, "6-devices", "Two or more narrators juxtaposing separate stories: files") == "FAIL"
    )


# --------------------------------------------------------------------------
# Check 7: questions cover the key
# --------------------------------------------------------------------------


def test_check7_matched_item_ids_pass(fake_root):
    report = audit.run_audit(fake_root)
    for item_id in ["A1", "A2", "B1"]:
        assert one_status(report, "7-questions-cover-key", item_id) == "PASS"


def test_check7_unmatched_item_id_fails(fake_root):
    report = audit.run_audit(fake_root)
    # B2 exists in answers-and-scoring.md but questions.md never asks it.
    assert one_status(report, "7-questions-cover-key", "B2") == "FAIL"


def test_check7_point_totals_pass_when_consistent(fake_root):
    report = audit.run_audit(fake_root)
    assert exact_status(report, "7-questions-cover-key", "point-totals") == "PASS"
    assert exact_status(report, "7-questions-cover-key", "point-totals-consistency") == "PASS"


def test_check7_point_totals_fail_when_they_do_not_sum_to_100():
    report = audit.Report()
    answers_text = (
        "Total: **100 points.** A 60 / B 30.\n\n"
        "## Section A — Reconstruction (60 points)\n\n### A1 — x (60 points)\n1. blah\n\n"
        "## Section B — Relationships (30 points)\n\n- **B1.** blah — 30.\n"
    )
    questions_text = "- **A1.** q\n- **B1.** q\n"
    audit.check7_questions_coverage(answers_text, questions_text, report)
    assert exact_status(report, "7-questions-cover-key", "point-totals") == "FAIL"


def test_check7_reports_unparsed_when_total_line_missing():
    report = audit.Report()
    answers_text = "## Section A — Reconstruction (30 points)\n\n### A1 — x (30 points)\n1. blah\n"
    questions_text = "- **A1.** q\n"
    audit.check7_questions_coverage(answers_text, questions_text, report)
    assert exact_status(report, "7-questions-cover-key", "point-totals") == "UNPARSED"


# --------------------------------------------------------------------------
# --strict exit code behavior
# --------------------------------------------------------------------------


def test_strict_mode_returns_nonzero_when_failures_exist(fake_root):
    rc = audit.main(["--root", str(fake_root), "--strict"])
    assert rc == 1


def test_non_strict_mode_returns_zero_even_with_failures(fake_root):
    rc = audit.main(["--root", str(fake_root)])
    assert rc == 0


# --------------------------------------------------------------------------
# Pure-function unit tests (small, targeted)
# --------------------------------------------------------------------------


def test_bounded_search_does_not_match_inside_hyphenated_compound():
    assert audit.bounded_search("the book showed fifty-seven nights", "fifty") is False
    assert audit.bounded_search("the coefficient was fifty degrees", "fifty") is True


def test_bounded_search_respects_word_boundaries_for_digits():
    assert audit.bounded_search("the span had 24 inches of play", "4 inches") is False
    assert audit.bounded_search("the span had 4 inches of play", "4 inches") is True


def test_words_to_number_and_back():
    assert audit.words_to_number("fifty-seven") == 57
    assert audit.words_to_number("four") == 4
    assert audit.words_to_number("two thousand five hundred and ten") == 2510
    assert "fifty-seven" == audit.number_to_words(57)
    assert "two thousand five hundred and ten" == audit.number_to_words(2510, with_and=True)


def test_generate_number_variants_digit_and_word_forms():
    variants = audit.generate_number_variants("four inches")
    assert any("4" in v for v in variants)


def test_id_shape_detection_ignores_question_labels_but_catches_bare_ids():
    key_text = " ".join(f"F{n:03d}" for n in range(1, 6))  # F001..F005, 5 distinct -> qualifies
    text_with_label = "- **D1.** A question about something.\nAn incidental mention of F002 in prose."
    report = audit.Report()
    audit.check5_leakage(
        Path("."),
        key_text,
        {"orig.md": "irrelevant text with no overlap here at all for twelve gram testing purposes today"},
        {"fake.md": text_with_label},
        report,
    )
    id_items = [i for i in report.items if "id-shape" in i.item_id]
    # The bare F002 mention must be caught...
    assert any(i.status == "FAIL" and "F002" in i.detail for i in id_items)
    # ...but "D1." inside the bold question-label markup must not trigger a match
    # (there is no D-shape group here since it never reaches the >=3 threshold,
    # so this also exercises that D1 alone doesn't get treated as a leak).
    assert not any("D1" in i.detail for i in id_items if i.status == "FAIL")


def test_build_ngrams_and_find_leaked_ngram():
    origin_text = "the quick brown fox jumps over the lazy dog again and again without end"
    grams = audit.build_ngrams(origin_text, n=12)
    leaking_text = "before this point there was nothing and then the quick brown fox jumps over the lazy dog again and again without end and that was all"
    leaked = audit.find_leaked_ngram(leaking_text, grams, n=12)
    assert leaked is not None
    clean_text = "this text shares no long run of words with the origin passage at all, none whatsoever"
    assert audit.find_leaked_ngram(clean_text, grams, n=12) is None


def test_strip_framing_skips_heading_and_italic_lines():
    text = "# Title\n\n*a short italic framing note*\n\nActual prose begins here and continues on."
    body = audit.strip_framing(text)
    assert body.startswith("Actual prose begins here")


# --------------------------------------------------------------------------
# Regression tests for the v2.1 audit-triage script fixes
# --------------------------------------------------------------------------


def test_dedupe_headers_disambiguates_repeated_column_names():
    # The real near-tie table has two "Carried by" columns (wrong-value
    # carriers, then correct-value carriers). dict(zip(...)) would keep only
    # the last one unless duplicates are disambiguated first.
    header = ["pair", "wrong value", "carried by", "correct value", "carried by", "settled by"]
    deduped = audit.dedupe_headers(header)
    assert deduped == ["pair", "wrong value", "carried by", "correct value", "carried by (2)", "settled by"]
    # A header with no repeats is untouched.
    assert audit.dedupe_headers(["fact", "correct in", "corrupted in"]) == ["fact", "correct in", "corrupted in"]


def test_parse_table_keeps_both_columns_when_header_repeats():
    block = [
        "| Pair | Wrong value | Carried by | Correct value | Carried by | Settled by |",
        "|---|---|---|---|---|---|",
        "| NT-1 | 4 in | r02, r09 | 3 in | r04, r07 | a document |",
    ]
    rows = audit.parse_table(block)
    assert len(rows) == 1
    # First occurrence keeps its name -> wrong-value carriers, not correct-value ones.
    assert rows[0]["carried by"] == "r02, r09"
    assert rows[0]["carried by (2)"] == "r04, r07"


NEAR_TIE_DUP_HEADER_CORRUPTION_MAP_MD = """\
# Corruption Map, vTest-duphead (SECRET)

---

## r01 — Alice, a witness

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | The span called for **four inches**. | Three inches. | **Near-tie 1** (partner r02) |

---

## r02 — Bob, an engineer

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X02 | F001 | Sheet 3 specified **four inches**. | Three inches. | **Near-tie 1** (partner r01) |

---

## r03 — Carol, a clerk

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X03 | F002 | The rockers travel **three inches**. | Three inches. | Correct, uncontested |

---

## Near-tie pairs (explicit)

| Pair | Wrong value | Carried by | Correct value | Carried by | Settled by |
|---|---|---|---|---|---|
| **NT-1** | **four inches** | r01, r02 | **three inches** | r03, r04 | a document |
"""


@pytest.fixture
def duphead_root(tmp_path) -> Path:
    root = tmp_path / "v2"
    (root / "answer-key").mkdir(parents=True)
    (root / "test-input" / "retellings").mkdir(parents=True)
    (root / "answer-key" / "corruption-map.md").write_text(NEAR_TIE_DUP_HEADER_CORRUPTION_MAP_MD, encoding="utf-8")
    (root / "test-input" / "questions.md").write_text("# Questions\n", encoding="utf-8")
    (root / "test-input" / "retellings" / "r01-alice.md").write_text(
        "# r01\n\nSheet 3 called for four inches of travel, or so I always understood it.", encoding="utf-8"
    )
    (root / "test-input" / "retellings" / "r02-bob.md").write_text(
        "# r02\n\nSheet 3 specified four inches of travel on that nest.", encoding="utf-8"
    )
    (root / "test-input" / "retellings" / "r03-carol.md").write_text(
        "# r03\n\nThe rockers travel three inches each way, I measured it myself.", encoding="utf-8"
    )
    (root / "test-input" / "retellings" / "r04-dana.md").write_text(
        "# r04\n\nThe drawing calls for three inches of travel on that span.", encoding="utf-8"
    )
    return root


def test_near_tie_duplicate_carried_by_headers_checks_the_wrong_value_carriers(duphead_root):
    cmap_text = (duphead_root / "answer-key" / "corruption-map.md").read_text(encoding="utf-8")
    cmap = audit.parse_corruption_map(cmap_text)
    assert len(cmap.near_ties) == 1
    nt = cmap.near_ties[0]
    # Before the dedupe fix this came back as ["r03", "r04"] (the CORRECT
    # value's carriers, from the second "Carried by" column clobbering the
    # first) instead of the wrong value's actual carriers.
    assert nt.carried_by == ["r01", "r02"]

    retellings = audit.load_retellings(duphead_root)
    report = audit.Report()
    result = audit.check2_planted_errors(cmap, retellings, report)
    assert one_status(report, "2-planted-errors", "NT-1") == "PASS"
    assert result.near_tie_ok["NT-1"] is True


def test_clean_quote_strips_embedded_bold_markers():
    assert audit.clean_quote('maintained over **eight** miles') == "maintained over eight miles"
    assert audit.clean_quote("**— A.R.**") == "— A.R"


def test_parse_narrator_briefs_documents_stops_at_first_closing_asterisk():
    # A citation line glued directly under the blockquote (itself containing
    # **bold** or *italics*) must not be swallowed into the quote by a greedy
    # regex reading from the opening "*" to the LAST "*" in the whole block.
    text = (
        "## r01 — Alice\n\n"
        "> *No lives were lost, and the engine is on her side.*\n"
        "> — *Ninestone Sentinel*, 8 March 1898\n"
    )
    docs = audit.parse_narrator_briefs_documents(text)
    assert docs["r01"] == ["No lives were lost, and the engine is on her side."]


def test_known_document_quote_fragment_excluded_from_uniqueness_check():
    # X01's As-told cell quotes only the tail of a document that both r01 and
    # r02 transcribe in full elsewhere. That fragment must not be held to
    # check 2's "unique to one narrator" rule.
    cmap_text = """\
## r01 — Alice

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | Signed "— A.R." at the foot of the page. | Someone else's initials. | Self-refuting |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "Entered here so that it is somewhere. — A.R."),
        "r02": (Path("r02.md"), "Entered here so that it is somewhere. — A.R."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    known_quotes = frozenset({audit.normalize_ws_quotes("Entered here so that it is somewhere. — A.R.")})
    report = audit.Report()
    audit.check2_planted_errors(cmap, retellings, report, known_document_quotes=known_quotes)
    # No FAIL should be reported for the "— A.R." fragment now that it is
    # recognized as document text shared by design.
    assert not [i for i in report.items if i.status == "FAIL"]


def test_candidate_present_handles_ellipsis_elided_quote():
    haystack = audit.normalize_ws_quotes(
        "Forty tons is forty tons. A nest of rollers was never meant for that load. I say the weight did it."
    )
    assert audit.candidate_present(haystack, "Forty tons is forty tons… I say the weight did it") is True
    assert audit.candidate_present(haystack, "Forty tons is forty tons… nothing like the weight did it") is False


def test_candidate_present_handles_semicolon_period_clause_boundary():
    haystack = audit.normalize_ws_quotes(
        "My father had no hand in that bridge. He was in the Ninestone office the whole time it was building."
    )
    candidate = "My father had no hand in that bridge; he was in the Ninestone office the whole time it was building"
    assert audit.candidate_present(haystack, candidate) is True


def test_expand_measurement_token_inches_feet_and_degrees():
    assert "two inches" in audit.expand_measurement_token("2 in")
    assert "forty feet" in audit.expand_measurement_token("40 ft")
    assert "forty degrees" in audit.expand_measurement_token("40°")
    assert "66°" in audit.expand_measurement_token("66°F")


def test_expand_measurement_token_negative_temperature_uses_below_zero_idiom():
    # This corpus's fixed convention for a negative Fahrenheit reading is
    # "N below zero" (sometimes just "N below"), never "N degrees".
    variants = audit.expand_measurement_token("−54°F")  # unicode minus
    assert "fifty-four below zero" in variants
    assert "fifty-four below" in variants


def test_candidate_tokens_from_fact_cell_keeps_unicode_minus_sign():
    tokens = audit._candidate_tokens_from_fact_cell("F062 −54°F as specified")
    assert any(t.startswith("−") for t in tokens)


def test_strip_blockquote_lines_removes_only_quoted_paragraphs():
    text = (
        "Some narration here.\n\n"
        "> *A verbatim document quote goes here, word for word.*\n\n"
        "More narration afterward, unrelated to the quote."
    )
    stripped = audit.strip_blockquote_lines(text)
    assert "verbatim document quote" not in stripped
    assert "Some narration here." in stripped
    assert "More narration afterward" in stripped


def test_check5_document_quote_shared_with_original_is_not_flagged_as_leaked_prose(tmp_path):
    # A document quoted verbatim in both the original source story (as a
    # blockquote) and a retelling (also as a blockquote) is DESIGNED overlap,
    # not copied prose -- it must not trip the 12-gram leak check. A retelling
    # that copies the original's own NARRATION (not a blockquoted document)
    # for 12+ words must still be caught.
    originals = {
        "01-story.md": (
            "Some scene-setting narration leads in.\n\n"
            "> *Rule for the long span: one inch in three hundred feet for forty degrees.*\n\n"
            "The narration then goes off in its own direction after that, unrelated to any quote."
        )
    }
    retelling_with_shared_document = (
        "# r01\n\n"
        "> *Rule for the long span: one inch in three hundred feet for forty degrees.*\n\n"
        "That is all I have to say about it."
    )
    retelling_that_copies_narration = (
        "# r02\n\n"
        "The narration then goes off in its own direction after that, unrelated to any quote, "
        "and I have nothing further to add here."
    )
    test_input_files = {
        "test-input/retellings/r01.md": retelling_with_shared_document,
        "test-input/retellings/r02.md": retelling_that_copies_narration,
    }
    report = audit.Report()
    audit.check5_leakage(tmp_path, "", originals, test_input_files, report)
    twelve_gram_items = [i for i in report.items if "12-gram" in i.item_id]
    r01_items = [i for i in twelve_gram_items if "r01.md" in i.item_id]
    r02_items = [i for i in twelve_gram_items if "r02.md" in i.item_id]
    assert all(i.status == "PASS" for i in r01_items)
    assert any(i.status == "FAIL" for i in r02_items)


def test_check3_freeform_fact_label_reports_needs_human_not_fail():
    # Residual cleanup, 2026-08-27: this branch was renamed from UNPARSED to
    # NEEDS-HUMAN, since it always represents a fact manually confirmed
    # present in different words, not merely an unparseable row.
    cmap_text = """\
## Recoverability index

### People

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F900 Alice and Bob are cousins | r01, r02 | — | Majority |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "Alice and Bob grew up together as cousins, everyone said so."),
        "r02": (Path("r02.md"), "Nothing about that relationship is mentioned here at all."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    report = audit.Report()
    audit.check3_recoverability(cmap, retellings, report)
    assert exact_status(report, "3-recoverability", "F900") == "NEEDS-HUMAN"


def test_check3_arithmetic_marked_fact_reports_needs_human_not_fail():
    cmap_text = """\
## Recoverability index

### Numbers

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F901 −54°F as specified | r01, r02 | — | Arithmetic: 66 minus 3x40 |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "That works out to fifty-four below zero, which nobody has ever measured."),
        "r02": (Path("r02.md"), "This narrator never does the arithmetic out loud."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    report = audit.Report()
    audit.check3_recoverability(cmap, retellings, report)
    assert exact_status(report, "3-recoverability", "F901") == "NEEDS-HUMAN"


def test_check3_single_source_no_doc_mark_hit_reports_accepted_single_source():
    # F004/F006/F007/F083-style row: exactly one carrier, no document mark.
    # Accepted by prior ruling (KEY-AUDIT fix 15) rather than FAILed outright
    # merely for resting on one narrator.
    cmap_text = """\
## Recoverability index

### People

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F910 built 1904 | r01 | — | Single-source for the year |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "The bridge was built in 1904, everyone agrees."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid != "r01"},
    }
    report = audit.Report()
    audit.check3_recoverability(cmap, retellings, report)
    assert exact_status(report, "3-recoverability", "F910") == "ACCEPTED-SINGLE-SOURCE"


def test_check3_single_source_no_doc_mark_genuine_miss_still_fails():
    # The single-source acceptance must not swallow a real gap: a plain
    # numeric single-source claim that is genuinely absent from its sole
    # carrier should still FAIL.
    cmap_text = """\
## Recoverability index

### People

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F911 built 1904 | r01 | — | Single-source for the year |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "Nothing about the build year is mentioned here."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid != "r01"},
    }
    report = audit.Report()
    audit.check3_recoverability(cmap, retellings, report)
    assert exact_status(report, "3-recoverability", "F911") == "FAIL"


def test_check3_only_in_declared_single_source_miss_reports_accepted_single_source():
    # The "Single-source scored facts (uncontested)" table's own Status
    # column says "single-source" -- a literal miss there is not a defect.
    cmap_text = """\
## Recoverability index

### Single-source scored facts (uncontested)

| Fact | Only in | Status |
|---|---|---|
| The founder was named Sam | r01 | Single-source, uncontested |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "Everybody around here knew the man who started the company."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid != "r01"},
    }
    report = audit.Report()
    audit.check3_recoverability(cmap, retellings, report)
    # fact_id falls back to the fact cell's own text (truncated to 24 chars)
    # when it has no leading F-number, so match on a short substring.
    assert one_status(report, "3-recoverability", "founder was named") == "ACCEPTED-SINGLE-SOURCE"


def test_check3_plain_numeric_fact_still_fails_when_genuinely_short(tmp_path):
    # A row with no document mark, no "arithmetic" resolution, and a bare
    # numeric token that is genuinely only found in one of two listed
    # narrators should still FAIL -- the UNPARSED downgrade must not paper
    # over an ordinary, checkable majority-fact discrepancy.
    cmap_text = """\
## Recoverability index

### Numbers

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F902 built 1904 | r01, r02 | — | Majority |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "The bridge was built in 1904, everyone agrees."),
        "r02": (Path("r02.md"), "Nothing about the build year is mentioned here."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    report = audit.Report()
    audit.check3_recoverability(cmap, retellings, report)
    assert exact_status(report, "3-recoverability", "F902") == "FAIL"


# --------------------------------------------------------------------------
# Residual cleanup, 2026-08-27: anchor-gated leak detection, near-tie
# per-narrator candidate attribution, single-source acceptance, and the
# known-document-quote exclusion for check 5's originals-side n-grams.
# --------------------------------------------------------------------------


def test_is_fragile_bare_value_flags_short_numbers_only():
    assert audit.is_fragile_bare_value("8") is True
    assert audit.is_fragile_bare_value("13") is True
    assert audit.is_fragile_bare_value("30") is True
    assert audit.is_fragile_bare_value("4 inches") is False
    assert audit.is_fragile_bare_value("nephew") is False


def test_split_sentence_units_treats_blockquote_line_as_its_own_unit():
    text = "Some narration ends here. Then more.\n> — Cadder Valley Railroad to A. Rennick, 30 April 1901"
    units = audit.split_sentence_units(text)
    assert "Some narration ends here." in units
    assert "Then more." in units
    assert any("Cadder Valley Railroad to A. Rennick" in u for u in units)


def test_anchor_confirms_true_when_value_and_anchor_share_a_sentence():
    text = "Dorsey was old Warren Tice's nephew, you know."
    assert audit.anchor_confirms(text, "nephew", "Tice") is True


def test_anchor_confirms_false_when_value_and_anchor_are_in_different_sentences():
    text = "He was Emil's son, which made him my mother's nephew and my first cousin."
    assert audit.anchor_confirms(text, "nephew", "Tice") is False


def test_candidate_required_narrators_splits_per_narrator_annotation():
    cell = 'Judd was Ruth\'s **great-uncle** (r04: "my father\'s uncle"; r01: "his grand-niece")'
    assert audit.candidate_required_narrators(cell, "my father's uncle", ["r01", "r04"]) == ["r04"]
    assert audit.candidate_required_narrators(cell, "his grand-niece", ["r01", "r04"]) == ["r01"]


def test_candidate_required_narrators_falls_back_when_no_parenthetical_narrows_it():
    cell = "**four inches** of travel"
    assert audit.candidate_required_narrators(cell, "four inches", ["r02", "r09"]) == ["r02", "r09"]


def test_candidate_required_narrators_main_clause_value_keeps_full_requirement():
    # A candidate that lives OUTSIDE the parenthetical (the shared "8") is
    # not narrowed just because a different candidate's parenthetical
    # mentions one carrier by name.
    cell = "**8** silent nights (r09 states only this; r06 additionally sums it to **69** in all)"
    assert audit.candidate_required_narrators(cell, "8", ["r06", "r09"]) == ["r06", "r09"]
    assert audit.candidate_required_narrators(cell, "69", ["r06", "r09"]) == ["r06"]


def test_strip_known_document_quotes_removes_quote_text():
    text = "Some narration. No lives were lost. Two of the gang are hurt. More narration."
    known = frozenset({audit.normalize_ws_quotes("No lives were lost. Two of the gang are hurt.")})
    out = audit.strip_known_document_quotes(text, known)
    assert "no lives were lost" not in out.lower()
    assert "some narration" in out.lower()
    assert "more narration" in out.lower()


def test_check2_anchor_excludes_unrelated_use_of_a_short_value():
    # X16-style: the planted value ("1902") is a bare year that also occurs,
    # unrelated, in another narrator -- but only alongside its own row's
    # anchor word ("purchase") in the assigned narrator, not in the other
    # narrator's unrelated sentence.
    cmap_text = """\
## r01 — Alice

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | The purchase was in **1902**. | 1901. | Off-by-one |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "The purchase was made in 1902, my father always said."),
        "r02": (Path("r02.md"), "She married Josiah Frayne in 1902, an unrelated fact entirely."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    report = audit.Report()
    audit.check2_planted_errors(cmap, retellings, report)
    assert one_status(report, "2-planted-errors", "X01") == "PASS"


def test_check2_near_tie_bare_value_leak_downgrades_to_needs_human():
    cmap_text = """\
## r06 — Farm book

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X18 | F900 | **8** silent nights. | 5. | **Near-tie 1** (partner r09) |

## r09 — Memorandum

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X47 | F900 | **8** silent nights. | 5. | **Near-tie 1** (partner r06) |

## Near-tie pairs (explicit)

| Pair | Wrong value | Carried by | Correct value | Settled by |
|---|---|---|---|---|
| **NT-1** | **8** silent nights | r06, r09 | **5** | a document |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r06": (Path("r06.md"), "There were eight silent nights, by my own count."),
        "r09": (Path("r09.md"), "Eight such nights appear in the depot record."),
        "r11": (Path("r11.md"), "Eight miles of descending grade, unrelated to any of this."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r06", "r09", "r11")},
    }
    report = audit.Report()
    audit.check2_planted_errors(cmap, retellings, report)
    assert one_status(report, "2-planted-errors", "NT-1") == "NEEDS-HUMAN"


def test_check2_near_tie_per_narrator_annotation_passes():
    # NT-8-style: each carrier states its OWN different wrong phrasing, not
    # a shared literal value -- the row's parenthetical annotation says so.
    cmap_text = """\
## r01 — Alice

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X37 | F008 | Ruth was Judd's **grand-niece**. | First cousin once removed. | **Near-tie 1** (partner r04) |

## r04 — Dana

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X14 | F008 | Judd was **my father's uncle**. | First cousin once removed. | **Near-tie 1** (partner r01) |

## Near-tie pairs (explicit)

| Pair | Wrong value | Carried by | Correct value | Settled by |
|---|---|---|---|---|
| **NT-1** | Judd was Ruth's **great-uncle** (r04: "my father's uncle"; r01: "his grand-niece") | r01, r04 | first cousin once removed | a derivation |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "She was his grand-niece, they told me."),
        "r04": (Path("r04.md"), "Judd Rennick, my father's uncle, lent me the book."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r04")},
    }
    report = audit.Report()
    audit.check2_planted_errors(cmap, retellings, report)
    found = [i for i in report.items if i.check == "2-planted-errors" and i.item_id.startswith("NT-1")]
    assert len(found) == 2
    assert all(i.status == "PASS" for i in found)


def test_check5_document_quote_as_inline_italics_in_original_is_not_flagged():
    # The same document can appear verbatim in the ORIGINAL story as inline
    # italics (not a '>' blockquote), which `strip_blockquote_lines` alone
    # does not catch. `strip_known_document_quotes` must exclude it too.
    known_quotes = frozenset(
        {audit.normalize_ws_quotes("No lives were lost. Two of the gang are hurt, and the engine is on her side.")}
    )
    originals = {
        "01-story.md": (
            "The paper said the same thing in longer words: *No lives were lost. Two of the "
            "gang are hurt, and the engine is on her side.* Nothing else in this passage matters."
        )
    }
    test_input_files = {
        "test-input/retellings/r01.md": (
            "# r01\n\n> *No lives were lost. Two of the gang are hurt, and the engine is on her side.*\n\n"
            "That is all I have to say about it."
        ),
    }
    report = audit.Report()
    audit.check5_leakage(Path("."), "", originals, test_input_files, report, known_document_quotes=known_quotes)
    twelve_gram_items = [i for i in report.items if "12-gram" in i.item_id]
    assert all(i.status == "PASS" for i in twelve_gram_items)


# --------------------------------------------------------------------------
# v3 root-agnostic support: missing retellings never crash, the word-count
# band is a parameter, narrator census is discovered (not a fixed range),
# document text can live in canon.md keyed by id instead of embedded per
# narrator, and Section A can be cue-less.
# --------------------------------------------------------------------------


def test_check1_missing_retelling_detail_names_the_narrator():
    report = audit.Report()
    audit.check1_files_and_lengths(Path("."), {}, ["r09"], report)
    item = [i for i in report.items if i.check == "1-files-and-lengths" and i.item_id == "r09"][0]
    assert item.status == "FAIL"
    assert "missing retelling r09" in item.detail


def test_check1_word_band_is_parameterised_lower_bound():
    retellings = {"r01": (Path("r01.md"), "word " * 1100)}  # below v2's 1,200 floor

    report_default = audit.Report()
    audit.check1_files_and_lengths(Path("."), retellings, ["r01"], report_default)
    assert exact_status(report_default, "1-files-and-lengths", "r01") == "FAIL"

    report_v3_band = audit.Report()
    audit.check1_files_and_lengths(Path("."), retellings, ["r01"], report_v3_band, min_words=1000, max_words=1500)
    assert exact_status(report_v3_band, "1-files-and-lengths", "r01") == "PASS"


def test_check1_word_band_is_parameterised_upper_bound():
    retellings = {"r01": (Path("r01.md"), "word " * 1600)}  # inside v2's band, above v3's 1,500 ceiling

    report_default = audit.Report()
    audit.check1_files_and_lengths(Path("."), retellings, ["r01"], report_default)
    assert exact_status(report_default, "1-files-and-lengths", "r01") == "PASS"

    report_v3_band = audit.Report()
    audit.check1_files_and_lengths(Path("."), retellings, ["r01"], report_v3_band, min_words=1000, max_words=1500)
    assert exact_status(report_v3_band, "1-files-and-lengths", "r01") == "FAIL"


def test_check1_word_band_defaults_stay_v2_shaped():
    retellings = {"r01": (Path("r01.md"), "word " * 1300)}
    report = audit.Report()
    audit.check1_files_and_lengths(Path("."), retellings, ["r01"], report)
    assert exact_status(report, "1-files-and-lengths", "r01") == "PASS"


def test_main_wires_min_words_max_words_flags_through(tmp_path, capsys):
    root = tmp_path / "root"
    (root / "answer-key").mkdir(parents=True)
    (root / "test-input" / "retellings").mkdir(parents=True)
    (root / "test-input" / "questions.md").write_text("# Q\n", encoding="utf-8")
    (root / "test-input" / "retellings" / "r01-a.md").write_text("word " * 1100, encoding="utf-8")

    rc_default = audit.main(["--root", str(root)])
    assert rc_default == 0
    out_default = capsys.readouterr().out
    assert "[FAIL] r01" in out_default

    rc_custom = audit.main(["--root", str(root), "--min-words", "1000", "--max-words", "1500"])
    assert rc_custom == 0
    out_custom = capsys.readouterr().out
    assert "[PASS] r01" in out_custom


def test_discover_narrator_ids_reads_headings_beyond_a_fixed_range(tmp_path):
    # The old NARRATOR_IDS constant stopped at r12; a corpus describing narrators past that
    # (v3 goes to r24) must still be discovered in full.
    root = tmp_path / "root"
    cmap_text = "## r01 — Alice\n\n## r14 — Someone\n\n## r24 — Someone else\n"
    assert audit.discover_narrator_ids(root, cmap_text, None) == ["r01", "r14", "r24"]


def test_discover_narrator_ids_unions_briefs_and_retellings_dir(tmp_path):
    root = tmp_path / "root"
    (root / "test-input" / "retellings").mkdir(parents=True)
    (root / "test-input" / "retellings" / "r05-someone.md").write_text("x", encoding="utf-8")
    cmap_text = "## r01 — Alice\n"
    briefs_text = "## r01 — Alice\n\n## r02 — Bob\n"
    assert audit.discover_narrator_ids(root, cmap_text, briefs_text) == ["r01", "r02", "r05"]


def test_discover_narrator_ids_returns_empty_list_when_nothing_found(tmp_path):
    root = tmp_path / "root"
    assert audit.discover_narrator_ids(root, None, None) == []


def test_check2_narrator_beyond_legacy_range_reports_missing_retelling_not_crash(tmp_path):
    # Direct regression test for the reported crash: `KeyError: 'r14'` inside
    # retelling_text() the instant corruption-map.md described a narrator beyond the old
    # hardcoded NARRATOR_IDS = r01..r12 range, with no retelling on disk for it at all.
    root = tmp_path / "v3-like"
    (root / "answer-key").mkdir(parents=True)
    (root / "test-input" / "retellings").mkdir(parents=True)
    (root / "answer-key" / "corruption-map.md").write_text(
        """\
## r14 — Someone, a narrator well beyond the old twelve-narrator range

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X99 | F200 | The gate was **red**. | Blue. | Unique |
""",
        encoding="utf-8",
    )
    (root / "test-input" / "questions.md").write_text("# Questions\n", encoding="utf-8")

    report = audit.run_audit(root)  # must not raise KeyError
    item = [i for i in report.items if i.check == "2-planted-errors" and i.item_id == "X99 [red]"][0]
    assert item.status == "FAIL"
    assert "missing retelling" in item.detail and "r14" in item.detail


def test_check3_single_source_all_narrators_missing_reports_fail_not_accepted():
    # With the narrator's retelling entirely absent there is nothing to confirm -- must not
    # be reported as ACCEPTED-SINGLE-SOURCE (which would misleadingly claim the fact was
    # manually confirmed present).
    cmap_text = """\
## Recoverability index

### Single-source scored facts (uncontested)

| Fact | Only in | Status |
|---|---|---|
| The founder was named Sam | r09 | Single-source, uncontested |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    report = audit.Report()
    audit.check3_recoverability(cmap, {}, report)
    item = [i for i in report.items if i.check == "3-recoverability"][0]
    assert item.status == "FAIL"
    assert "missing retelling" in item.detail and "r09" in item.detail


def test_check3_majority_fact_all_narrators_missing_reports_fail_not_needs_human():
    cmap_text = """\
## Recoverability index

### People

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F950 Alice and Bob are cousins | r01, r02 | — | Majority |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    report = audit.Report()
    audit.check3_recoverability(cmap, {}, report)
    assert exact_status(report, "3-recoverability", "F950") == "FAIL"
    item = [i for i in report.items if i.check == "3-recoverability" and i.item_id == "F950"][0]
    assert "missing retelling" in item.detail


def test_run_audit_end_to_end_no_crash_beyond_legacy_range_with_all_retellings_missing(tmp_path):
    root = tmp_path / "v3-like"
    (root / "answer-key").mkdir(parents=True)
    (root / "test-input" / "retellings").mkdir(parents=True)
    (root / "answer-key" / "corruption-map.md").write_text(
        """\
## r13 — First narrator beyond the old range

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | The gate was **red**. | Blue. | Unique |

## r14 — Second narrator beyond the old range

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X02 | F002 | The flag was **green**. | Yellow. | **Near-tie 1** (partner r13) |

## Near-tie pairs (explicit)

| Pair | Wrong value | Carried by | Correct value | Settled by |
|---|---|---|---|---|
| **NT-1** | **green** | r13, r14 | yellow | a document |

## Recoverability index

### People

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F900 something true | r13, r14 | — | Majority |

## Device checklist

| Device | Where implemented | Facts touched |
|---|---|---|
| **Internal contradictions in one retelling** | r13, r14 | F001 |
""",
        encoding="utf-8",
    )
    (root / "test-input" / "questions.md").write_text("# Questions\n", encoding="utf-8")

    report = audit.run_audit(root)  # must not raise
    counts = report.counts()
    assert counts["FAIL"] > 0
    assert any("missing retelling" in i.detail and ("r13" in i.detail or "r14" in i.detail) for i in report.items)
    assert report.structure_counts["narrators"] == 2
    assert report.structure_counts["planted errors"] == 2
    assert report.structure_counts["near-tie pairs"] == 1


def test_parse_canon_documents_extracts_verbatim_text_by_id():
    canon_text = """\
## 6. Documents (verbatim — these outrank memory)

**D1 — By-laws of the Association, Article VII**
> *Article VII. Every patron shall be paid by test.*

**D2 — Invoice, Ammon & Sons, 14 April 1897**
> *Sold to the Association: 6 doz. pipettes, 17.6 c.c.*
"""
    docs = audit.parse_canon_documents(canon_text)
    assert docs["D1"] == "Article VII. Every patron shall be paid by test."
    assert docs["D2"] == "Sold to the Association: 6 doz. pipettes, 17.6 c.c."


def test_build_docs_by_narrator_falls_back_to_canon_when_briefs_has_no_blockquotes():
    # v3-shaped key: narrator-briefs.md never embeds document text directly (no '>' lines
    # at all), only says which ids a narrator quotes; the text itself lives once, in
    # canon.md, keyed by document id.
    narrator_briefs_text = """\
## r02 — Effie Loomis

**Documents.** **D1** and **D8**, both verbatim.
"""
    canon_text = """\
## 6. Documents (verbatim — these outrank memory)

**D1 — By-laws, Article VII**
> *Article VII. Every patron shall be paid by test.*

**D8 — Minutes of the board**
> *The board awards the patrons thirty-eight hundred dollars.*
"""
    docs_by_narrator = audit.build_docs_by_narrator(narrator_briefs_text, None, canon_text)
    assert docs_by_narrator["r02"] == [
        "Article VII. Every patron shall be paid by test.",
        "The board awards the patrons thirty-eight hundred dollars.",
    ]


def test_build_docs_by_narrator_excludes_ids_only_referred_to_without_transcribing():
    narrator_briefs_text = """\
## r13 — Alonzo Frick

**Documents.** The exhibit list (his own reproduction); he refers to D8 without transcribing it.
"""
    canon_text = """\
## 6. Documents (verbatim — these outrank memory)

**D8 — Minutes of the board**
> *The board awards the patrons thirty-eight hundred dollars.*
"""
    docs_by_narrator = audit.build_docs_by_narrator(narrator_briefs_text, None, canon_text)
    assert "r13" not in docs_by_narrator


def test_build_docs_by_narrator_prefers_v2_style_embedded_blockquotes():
    # When narrator-briefs.md already embeds the document text directly (v2 shape), that
    # must win even if a canon.md Documents section also happens to be present.
    narrator_briefs_text = (
        "## r01 — Alice\n\n"
        "**Documents she quotes verbatim.**\n\n"
        "> *No lives were lost.*\n"
        "> — *Ninestone Sentinel*, 8 March 1898\n"
    )
    canon_text = """\
## 6. Documents (verbatim — these outrank memory)

**D1 — Some other document**
> *Completely different text.*
"""
    docs_by_narrator = audit.build_docs_by_narrator(narrator_briefs_text, None, canon_text)
    assert docs_by_narrator["r01"] == ["No lives were lost."]


def test_check7_section_a_cueless_design_passes_when_story_count_matches():
    answers_text = """\
Total: **20 points.** A 12 / B 8

## Section A -- Reconstruction (12 points)

### A1 -- first story (6 points)
1. Something. **F001**

### A2 -- second story (6 points)

## Section B -- Relationships (8 points)

- **B1.** Something. **F010**
"""
    questions_text = """\
## Section A -- Reconstruction (12 points)

There were originally **two** stories. Reconstruct each of the two.

## Section B -- Relationships (8 points)

- **B1.** What was the relationship?
"""
    report = audit.Report()
    scored_items = audit.check7_questions_coverage(answers_text, questions_text, report)
    assert exact_status(report, "7-questions-cover-key", "A1") == "PASS"
    assert exact_status(report, "7-questions-cover-key", "A2") == "PASS"
    assert exact_status(report, "7-questions-cover-key", "section-A-story-count") == "PASS"
    assert exact_status(report, "7-questions-cover-key", "B1") == "PASS"
    assert scored_items == {"A1", "A2", "B1"}


def test_check7_section_a_cueless_design_fails_when_story_count_does_not_match():
    answers_text = """\
### A1 -- first story (6 points)
### A2 -- second story (6 points)
### A3 -- third story (6 points)
"""
    questions_text = """\
## Section A -- Reconstruction (18 points)

There were originally **two** stories. Reconstruct each of the two.
"""
    report = audit.Report()
    audit.check7_questions_coverage(answers_text, questions_text, report)
    assert exact_status(report, "7-questions-cover-key", "A1") == "FAIL"
    assert exact_status(report, "7-questions-cover-key", "section-A-story-count") == "FAIL"


def test_check7_section_a_v2_style_cued_ids_still_matched_individually():
    # Regression: when every Section A id IS individually cued in questions.md (v2 shape),
    # behavior must be unchanged -- an ordinary per-id match, no cue-less machinery kicks in.
    answers_text = """\
### A1 -- first story (8 points)
### A2 -- second story (8 points)
"""
    questions_text = """\
## Section A -- Reconstruction (16 points)

- **A1.** The first story.
- **A2.** The second story.
"""
    report = audit.Report()
    audit.check7_questions_coverage(answers_text, questions_text, report)
    assert exact_status(report, "7-questions-cover-key", "A1") == "PASS"
    assert exact_status(report, "7-questions-cover-key", "A2") == "PASS"
    assert not [i for i in report.items if i.item_id == "section-A-story-count"]


def test_check7_section_a_mixed_cue_state_reports_unparsed_rather_than_guessing():
    answers_text = """\
### A1 -- first story (6 points)
### A2 -- second story (6 points)
"""
    questions_text = """\
## Section A -- Reconstruction (12 points)

- **A1.** The first story, named for the solver.

There were originally **two** stories.
"""
    report = audit.Report()
    audit.check7_questions_coverage(answers_text, questions_text, report)
    assert exact_status(report, "7-questions-cover-key", "section-A-cue-shape") == "UNPARSED"
    assert not [i for i in report.items if i.item_id in ("A1", "A2")]


def test_check7_bullet_id_bold_span_may_extend_past_the_id():
    # v3's answers-and-scoring.md sometimes folds more text into the same bold span as the
    # id ("- **B4. Abstention item (A01).**"), unlike v2's immediate-close style
    # ("- **B1.** ..."). Both must be recognized, and the abstention id folded into the same
    # span must NOT itself be picked up as a separate scored item.
    answers_text = "- **B4. Abstention item (A01).** States that whether it can be determined."
    scored_items, *_ = audit.parse_answers_scoring(answers_text)
    assert "B4" in scored_items
    assert "A01" not in scored_items


def test_check7_bullet_id_with_parenthetical_before_period_is_recognized():
    # v3's Section C bullets put a parenthetical between the id and the period
    # ("- **C1 (4 points, 1 each).**") rather than closing the bold immediately.
    answers_text = "- **C1 (4 points, 1 each).**\n  (a) something"
    scored_items, *_ = audit.parse_answers_scoring(answers_text)
    assert "C1" in scored_items


# --------------------------------------------------------------------------
# v3 audit-triage, 2026-08-28
# --------------------------------------------------------------------------


def test_strip_blockquote_markers_removes_leading_marker_but_keeps_content():
    text = "> Ostrey Hollow station. Begun this 4th day of May, 1896. Glass borrowed\n> of Larrow Green until our own comes."
    assert audit.strip_blockquote_markers(text) == (
        "Ostrey Hollow station. Begun this 4th day of May, 1896. Glass borrowed\nof Larrow Green until our own comes."
    )


def test_normalize_ws_quotes_does_not_leave_a_stray_gt_at_a_line_wrap():
    # A multi-line blockquote's continuation lines each start with '> ' in the
    # source markdown; naive whitespace collapse alone turns the line break
    # into a plain space and leaves a literal '>' glued mid-sentence.
    text = "> Every patron shall be paid for the milk he delivers according to the number\n> of pounds of butter fat."
    normalized = audit.normalize_ws_quotes(text)
    assert ">" not in normalized
    assert "number of pounds" in normalized


def test_normalize_ws_quotes_strips_per_line_italics_in_a_wrapped_blockquote():
    # Some retellings wrap EACH line of a multi-line document quote in its
    # own italics ("> *line one*\n> *line two*") rather than opening the
    # span once across the whole quote -- left in place, the per-line
    # closing/reopening asterisks survive as literal '*' characters glued
    # between lines.
    text = "> *Sold to the Association, for the station:*\n> *6 doz. pipettes at .35 — 25.20*"
    normalized = audit.normalize_ws_quotes(text)
    assert "*" not in normalized
    assert "station: 6 doz. pipettes" in normalized


def test_strip_markdown_tables_drops_table_lines_keeps_prose():
    text = "Some prose.\n| Season | Test |\n|---|---|\n| 1915 | 3.79 |\nMore prose."
    stripped = audit.strip_markdown_tables(text)
    assert "|" not in stripped
    assert "Some prose." in stripped
    assert "More prose." in stripped


def test_word_count_after_framing_excludes_tables_and_blockquote_markers(tmp_path):
    text = (
        "# Title\n\n*Framing note.*\n\none two three\n"
        "| a | b |\n|---|---|\n| c | d |\n"
        "> four\n> five\n"
    )
    # "one two three four five" = 5 words; the table's cells/pipes and the
    # blockquote's '>' markers must not be counted.
    assert audit.word_count_after_framing(text) == 5


def test_number_to_words_handles_millions_and_mixed_thousands():
    assert audit.number_to_words(44_000_000) == "forty-four million"
    assert audit.number_to_words(40_000_000) == "forty million"
    assert audit.number_to_words(1_600_000) == "one million six hundred thousand"
    assert audit.number_to_words(67_000) == "sixty-seven thousand"
    assert audit.number_to_words(19_600) == "nineteen thousand six hundred"
    # Small-number behavior from before this pass must be unchanged.
    assert audit.number_to_words(2510, with_and=True) == "two thousand five hundred and ten"


def test_number_to_hundreds_idiom_only_fires_for_round_thousands():
    assert audit.number_to_hundreds_idiom(3500) == "thirty-five hundred"
    assert audit.number_to_hundreds_idiom(1900) == "nineteen hundred"
    assert audit.number_to_hundreds_idiom(3542) is None  # has its own remainder
    assert audit.number_to_hundreds_idiom(500) is None  # below 1,100


def test_generate_number_variants_includes_hundreds_idiom():
    variants = audit.generate_number_variants("$3,500")
    assert any("thirty-five hundred" in v for v in variants)


def test_expand_measurement_token_handles_pounds_and_dozen():
    assert "sixty-seven thousand pounds" in audit.expand_measurement_token("67,000 lb")
    assert "forty-four million pounds" in audit.expand_measurement_token("44,000,000 lb")
    assert "five dozen" in audit.expand_measurement_token("5 doz.")
    assert "six dozen" in audit.expand_measurement_token("6 dozen")


def test_expand_decimal_token_handles_hundredths_tenths_and_two_part_forms():
    assert "three sixty-one" in audit.expand_decimal_token("3.61")
    assert "three eighty-five" in audit.expand_decimal_token("3.85")
    assert "nineteen hundredths" in audit.expand_decimal_token("0.19")
    variants = audit.expand_decimal_token("0.20")
    assert "twenty hundredths" in variants
    assert "two tenths" in variants


def test_expand_year_token_gives_two_part_and_round_century_forms():
    assert "eighteen sixty-eight" in audit.expand_year_token("1868")
    assert "nineteen hundred" in audit.expand_year_token("1900")
    assert "nineteen hundred and seven" in audit.expand_year_token("1907")


def test_expand_year_shorthand_gives_bare_tail_only():
    # r17 (a taped interview) and r23 (a first-person memoir) both drop the
    # century for their own wrong dates ("in ninety-nine", "in twenty-two").
    # Deliberately a SEPARATE function from `expand_year_token` -- see
    # `candidate_present`'s `strict` flag.
    assert audit.expand_year_shorthand("1899") == ["ninety-nine"]
    assert audit.expand_year_shorthand("1922") == ["twenty-two"]
    assert audit.expand_year_shorthand("1900") == []  # round century has no bare tail
    assert "ninety-nine" not in audit.expand_year_token("1899")


def test_candidate_present_strict_omits_fragile_year_shorthand():
    # The bare shorthand form collides with an unrelated count/age/duration
    # far too easily to trust when checking whether a value has LEAKED into
    # some OTHER narrator (v2's own corpus: "eighteen seventy-six" against
    # an unrelated "written at seventy-six").
    text = "written at seventy-six by the keeper of the record"
    assert audit.candidate_present(text, "1876") is True
    assert audit.candidate_present(text, "1876", strict=True) is False
    # Non-shorthand forms still work under strict mode.
    full_text = "she was born in eighteen seventy-six, by her own account"
    assert audit.candidate_present(full_text, "1876", strict=True) is True


def test_expand_date_token_gives_ordinal_prose_form():
    assert audit.expand_date_token("1 May 1898") == ["the first of May, 1898"]
    assert audit.expand_date_token("12 July 1923") == ["the twelfth of July, 1923"]
    assert audit.expand_date_token("not a date") == []


def test_expand_currency_token_gives_dollars_and_cents_prose():
    assert audit.expand_currency_token("$77.39") == ["seventy-seven dollars and thirty-nine cents"]


def test_generate_plural_variants_gives_singular_cousin_form():
    variants = audit.generate_plural_variants("Ivy and Hazel first cousins once removed")
    assert any("first cousin once removed" in v and "cousins" not in v for v in variants)


def test_candidate_present_finds_hundred_idiom_decimal_and_ordinal_date_forms():
    # Each of these mirrors an actual v3 retelling sentence that a plain
    # digit<->word conversion could not have matched before this pass.
    assert audit.candidate_present("they paid thirty-five hundred dollars and called it settled", "$3,500")
    assert audit.candidate_present("the average of this station was three eighty-five", "3.85")
    assert audit.candidate_present("went into use on the first of may, 1898, and remained", "1 May 1898")
    assert audit.candidate_present("she went up that ladder in the winter of nineteen thirteen", "1913")


def test_extract_fact_id_accepts_trailing_lowercase_letter_suffix():
    # canon.md's own convention (F098, F098a, F098b, F098c are four DIFFERENT
    # facts) must not collapse "F098a ..." and a separate "F098 ..." row to
    # the same extracted id.
    assert audit._extract_fact_id("F098a Larrow Green's own average 3.78") == "F098a"
    assert audit._extract_fact_id("F098 sixteen seasons, ~0.19 higher") == "F098"


def test_candidate_tokens_from_fact_cell_strips_lettered_fact_id():
    tokens = audit._candidate_tokens_from_fact_cell("F098a Larrow Green's own average 3.78")
    assert tokens == ["3.78"]


def test_recoverability_parsing_captures_every_narrator_id_in_one_token():
    # A "Correct in" cell can cram several ids into one comma-separated
    # segment via ';'/'and' inside a parenthetical gloss.
    cmap_text = """\
## Recoverability index

| Fact | Correct in | Corrupted in | How it resolves |
|---|---|---|---|
| F098a Larrow Green's own average 3.78 | r14, r22 (the figure); r07 and r09 (the comparison) | — | Two sources |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    assert len(cmap.recoverability) == 1
    ids = sorted(n for n, _ in cmap.recoverability[0].listed)
    assert ids == ["r07", "r09", "r14", "r22"]


def test_is_known_document_fragment_handles_ellipsis_across_two_pieces():
    known = frozenset(
        {audit.normalize_ws_quotes(
            "Ostrey Hollow station. Begun this 4th day of May, 1896. Glass borrowed of "
            "Larrow Green until our own comes. A. Keddie."
        )}
    )
    cand = audit.normalize_ws_quotes("Begun this 4th day of May, 1896 … A. Keddie")
    assert audit.is_known_document_fragment(cand, known)
    assert not audit.is_known_document_fragment(
        audit.normalize_ws_quotes("An entirely unrelated sentence"), known
    )


def test_check2_document_fragment_exclusion_requires_quoted_context():
    # X94-style: a bare **bold** wrong-value candidate (no quotation marks at
    # all in the As-told cell) must NOT be excluded just because the same
    # short digit string happens to appear, unrelated, inside some other
    # document's own verbatim text (D5's "the nine weeks of 1911").
    cmap_text = """\
## r01 — Alice

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | Selby Vose became manager in **1911**. | 1913. | Date drift |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    known_document_quotes = frozenset(
        {"the recorded average held steady, save the nine weeks of 1911 that are noted in their place"}
    )
    retellings = {
        "r01": (Path("r01.md"), "Selby Vose became manager in 1911, everyone agreed."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid != "r01"},
    }
    report = audit.Report()
    audit.check2_planted_errors(
        cmap, retellings, report, known_document_quotes=known_document_quotes, narrator_ids=audit.NARRATOR_IDS
    )
    assert one_status(report, "2-planted-errors", "X01") == "PASS"


def test_find_leaked_ngram_skips_a_run_that_is_itself_a_known_document_quote():
    # An original story can quote only a short CLAUSE of a longer document
    # sentence inline (e.g. its closing words, as an aside) -- too irregular
    # a fragment for whole-quote stripping upstream to catch, so the found
    # 12-word run itself must be checked against the known document quotes.
    known = frozenset(
        {
            "i have never taken a pound of cream out of that station and there is not a "
            "man in this room who thinks i have when he is by himself"
        }
    )
    # Twelve words, all drawn verbatim from the known D9-style quote above.
    origin_text = "his own denial there is not a man in this room who thinks i have when he is by himself was accurate"
    origin_ngrams = audit.build_ngrams(origin_text)
    retelling_text = "and there is not a man in this room who thinks i have when he is by himself either"
    assert audit.find_leaked_ngram(retelling_text, origin_ngrams, known_document_quotes=known) is None
    # Without the known-document exclusion, the same run is (correctly) still flagged.
    assert audit.find_leaked_ngram(retelling_text, origin_ngrams) is not None


def test_strip_known_document_quotes_does_not_touch_unrelated_short_words():
    # Guards against the failure mode a sentence-level fragment stripper
    # would have: a known quote beginning with a bare initial ("A. Keddie")
    # must never turn into a pattern that matches every "A" in unrelated text.
    known = frozenset({"begun this 4th day of may, 1896. a. keddie."})
    text = "A man walked a long way and saw a bird."
    assert audit.strip_known_document_quotes(text, known) == audit.normalize_ws_quotes(text)


def test_is_fragile_bare_value_flags_spelled_out_bare_numbers():
    assert audit.is_fragile_bare_value("Seven")
    assert audit.is_fragile_bare_value("eleven")
    assert audit.is_fragile_bare_value("twenty-six")
    # A digit string of 3+ characters (an exact year, in practice) is a
    # trustworthy fingerprint on its own.
    assert not audit.is_fragile_bare_value("1868")
    # A number combined with other context is unaffected -- it is governed
    # by LEAK_ANCHORS instead, not blanket fragility.
    assert not audit.is_fragile_bare_value("4 inches")
    assert not audit.is_fragile_bare_value("nephew")


def test_check2_standalone_bare_number_word_leak_downgrades_to_needs_human():
    # X07-style: the wrong value is nothing but a common spelled-out number
    # ("Seven"), which recurs constantly elsewhere in the corpus for
    # unrelated counts/distances -- present in its assigned narrator, but a
    # leak elsewhere should be NEEDS-HUMAN, not a hard FAIL.
    cmap_text = """\
## r01 — Alice

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | **Seven** farms had rights on the bottom. | Six. | Unique |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "Seven farms had rights on the bottom, everyone agreed."),
        "r02": (Path("r02.md"), "Seven miles of hill road, unrelated to any of this."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    report = audit.Report()
    audit.check2_planted_errors(cmap, retellings, report)
    assert one_status(report, "2-planted-errors", "X01") == "NEEDS-HUMAN"


def test_check2_standalone_still_fails_a_genuine_leak_of_a_distinctive_value():
    # The fragile-value downgrade must not swallow a REAL leak of a
    # distinctive (non-bare-number) wrong value.
    cmap_text = """\
## r01 — Alice

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| X01 | F001 | The bridge was **crimson**. | Blue. | Off-by-color |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    retellings = {
        "r01": (Path("r01.md"), "The bridge was crimson, everybody said so."),
        "r02": (Path("r02.md"), "I too remember the bridge being crimson that year."),
        **{rid: (None, None) for rid in audit.NARRATOR_IDS if rid not in ("r01", "r02")},
    }
    report = audit.Report()
    audit.check2_planted_errors(cmap, retellings, report)
    assert one_status(report, "2-planted-errors", "X01") == "FAIL"


def test_parse_narrator_document_ids_excludes_none_verbatim_caveat():
    # r19-style: "**Documents.** None verbatim; it paraphrases D14 loosely
    # and must not be allowed to quote it." must not be read as r19
    # transcribing D14 -- check 4 would otherwise demand a verbatim match
    # the key explicitly forbids.
    text = """\
## r19 — A newspaper feature

**Documents.** None verbatim; it paraphrases D14 loosely and must not be allowed to quote it.
"""
    ids = audit.parse_narrator_document_ids(text)
    assert ids == {}


def test_parse_narrator_document_ids_still_reads_a_genuine_bolded_list():
    text = """\
## r07 — Accession notes

**Documents.** **D1, D2, D3** — all verbatim.
"""
    ids = audit.parse_narrator_document_ids(text)
    assert ids == {"r07": ["D1", "D2", "D3"]}


def test_parse_corruption_map_skips_a_withdrawn_struck_through_error_row():
    # A validation pass can withdraw a previously-live error after re-keying
    # its fact a different way; the row is kept (struck through) as a
    # record, and must not be checked as if it were still live.
    cmap_text = """\
## r06 — Merle Strawn

| id | Corrupts | As told | Truth | Mechanism |
|---|---|---|---|---|
| ~~X23~~ | — | ~~He took the circuit in **1907**.~~ | — | **WITHDRAWN (validation ruling 2).** Re-keyed as NT-23. |
| X24 | F001 | The book was **blue**. | Red. | Unique |
"""
    cmap = audit.parse_corruption_map(cmap_text)
    ids = [e.error_id for e in cmap.errors]
    assert "X24" in ids
    assert not any("X23" in i for i in ids)


def test_missing_retellings_summary_line_excludes_word_count_failures(capsys):
    # A retelling that EXISTS but is outside the word-count band is a
    # "1-files-and-lengths" FAIL under the bare "rNN" item id, same as a
    # truly absent file -- the summary line must not call the former
    # "missing".
    report = audit.Report()
    report.add("1-files-and-lengths", "r10", "FAIL", "r10-letter.md: 1554 words (after framing) — outside 1,000-1,500")
    report.add("1-files-and-lengths", "r11", "FAIL", "missing retelling r11: no file matching r11-*.md in test-input/retellings/")
    audit.print_report(report)
    out = capsys.readouterr().out
    assert "Missing retellings: r11" in out
    assert "r10" not in out.split("Missing retellings:")[1].split("\n")[0]
