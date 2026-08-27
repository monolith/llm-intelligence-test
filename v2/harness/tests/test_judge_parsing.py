"""Judge JSON parsing: fenced and unfenced responses, and judge_once end-to-end with a fake client."""
from __future__ import annotations

import pytest

import common
import judge

VERDICT = {
    "sections": {
        "A": {"items": [{"id": "A1", "points": 1, "note": "ok"}], "total": 1},
        "B": {"items": [{"id": "B1", "points": 0, "note": "wrong"}], "total": 0},
    },
    "deductions": [{"reason": "asserted a planted error", "points": -1}],
    "total": 0,
}


def test_extract_json_handles_fenced_response():
    text = "Here is my scoring:\n```json\n" + _dumps(VERDICT) + "\n```\nThanks."
    assert common.extract_json(text) == VERDICT


def test_extract_json_handles_bare_fence():
    text = "```\n" + _dumps(VERDICT) + "\n```"
    assert common.extract_json(text) == VERDICT


def test_extract_json_handles_unfenced_response():
    text = _dumps(VERDICT)
    assert common.extract_json(text) == VERDICT


def test_extract_json_handles_surrounding_prose():
    text = "Sure, scoring now.\n\n" + _dumps(VERDICT) + "\n\nLet me know if you want detail."
    assert common.extract_json(text) == VERDICT


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError):
        common.extract_json("not json at all")


def test_judge_once_parses_fake_client_reply(fake_client_factory, no_sleep):
    def responder(_index, _kwargs):
        return "```json\n" + _dumps(VERDICT) + "\n```"

    client = fake_client_factory(responder)
    result = judge.judge_once(client, "fake-model", "KEY TEXT", "ANSWERS TEXT", 100, sleep=no_sleep)
    assert result == VERDICT


def test_section_totals_and_max_abs_diff():
    totals = judge.section_totals(VERDICT)
    assert totals["A"] == 1
    assert totals["B"] == 0
    assert totals["deductions"] == -1
    assert totals["total"] == 0

    other = dict(VERDICT, total=3)
    assert judge.max_abs_diff([VERDICT, other]) == 3
    assert judge.max_abs_diff([VERDICT]) == 0.0


def _dumps(obj):
    import json

    return json.dumps(obj)
