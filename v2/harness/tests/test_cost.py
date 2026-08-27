"""Cost math: usage normalization, list-price cost, and the 4-chars-per-token estimate."""
from __future__ import annotations

import common

PRICES = {
    "fake-model": {
        "input_per_M": 2.0,
        "cached_input_per_M": 0.2,
        "cache_write_per_M": 2.5,
        "output_per_M": 10.0,
    }
}


def test_usage_to_dict_handles_object_and_dict():
    class Obj:
        input_tokens = 10
        output_tokens = 5
        cache_creation_input_tokens = 3
        cache_read_input_tokens = 2

    from_obj = common.usage_to_dict(Obj())
    assert from_obj == {
        "input_tokens": 10,
        "output_tokens": 5,
        "cache_creation_input_tokens": 3,
        "cache_read_input_tokens": 2,
    }

    from_dict = common.usage_to_dict({"input_tokens": 1, "output_tokens": 2})
    assert from_dict["input_tokens"] == 1
    assert from_dict["output_tokens"] == 2
    assert from_dict["cache_creation_input_tokens"] == 0
    assert from_dict["cache_read_input_tokens"] == 0

    assert common.usage_to_dict(None) == {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }


def test_cost_usd_matches_hand_computed_value():
    usage = {
        "input_tokens": 1_000_000,
        "output_tokens": 1_000_000,
        "cache_creation_input_tokens": 1_000_000,
        "cache_read_input_tokens": 1_000_000,
    }
    cost = common.cost_usd(usage, "fake-model", PRICES)
    # 2.0 + 0.2 + 2.5 + 10.0
    assert cost == 14.7


def test_cost_usd_unknown_model_returns_none():
    usage = {"input_tokens": 100, "output_tokens": 100, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    assert common.cost_usd(usage, "no-such-model", PRICES) is None


def test_sum_usage_adds_across_entries():
    entries = [
        {"input_tokens": 10, "output_tokens": 1, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0},
        {"input_tokens": 5, "output_tokens": 2, "cache_creation_input_tokens": 1, "cache_read_input_tokens": 3},
    ]
    totals = common.sum_usage(entries)
    assert totals == {
        "input_tokens": 15,
        "output_tokens": 3,
        "cache_creation_input_tokens": 1,
        "cache_read_input_tokens": 3,
    }


def test_estimate_tokens_is_four_chars_per_token():
    assert common.estimate_tokens("") == 0
    assert common.estimate_tokens("ab") == 1
    assert common.estimate_tokens("a" * 8) == 2
    assert common.estimate_tokens("a" * 9) == 3


def test_count_tokens_for_text_uses_estimate_without_credentials():
    tokens, method = common.count_tokens_for_text(None, "fake-model", "a" * 40, has_credentials=False)
    assert method == "estimate"
    assert tokens == 10


def test_count_tokens_for_text_uses_api_with_credentials(fake_client_factory):
    client = fake_client_factory()
    tokens, method = common.count_tokens_for_text(client, "fake-model", "a" * 40, has_credentials=True)
    assert method == "api"
    assert tokens == 10
    assert len(client.messages.count_tokens_calls) == 1
