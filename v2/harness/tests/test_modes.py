"""Message construction for all three modes, against a fake client (no network, no credentials)."""
from __future__ import annotations

import common
import run_v2


def responder(index, kwargs):
    last_user = kwargs["messages"][-1]["content"]
    if "Your context will be replaced" in last_user:
        return "NOTES-CONTENT-XYZ"
    return f"ack-{index}"


def load(sample_inputs_dir, mode):
    return run_v2.load_inputs(
        sample_inputs_dir["retellings_dir"],
        sample_inputs_dir["questions_path"],
        sample_inputs_dir["noise_dir"],
        sample_inputs_dir["noise_questions_path"],
        mode,
    )


def test_read_text_files_sorted_ignores_creation_order(sample_inputs_dir):
    # n02.md was written before n01.md; the fixed order must still be n01 then n02.
    docs = common.read_text_files_sorted(sample_inputs_dir["noise_dir"], "*.md", exclude={"questions.md"})
    assert [name for name, _ in docs] == ["n01.md", "n02.md"]
    assert docs[0][1] == "NOISE-DOC-ONE body"
    assert docs[1][1] == "NOISE-DOC-TWO body"


def test_single_mode_sends_one_request(sample_inputs_dir, fake_client_factory, no_sleep):
    client = fake_client_factory(responder)
    inputs = load(sample_inputs_dir, "single")

    outcome = run_v2.run_single(client, "fake-model", inputs, 100, {}, sleep=no_sleep)

    assert len(client.messages.calls) == 1
    content = client.messages.calls[0]["messages"][0]["content"]
    assert "RETELLING-ONE body" in content
    assert "RETELLING-TWO body" in content
    assert "RETELLING-THREE body" in content
    assert "QUESTIONS-MARKER" in content
    assert outcome.final_answer == "ack-0"
    assert outcome.num_compactions == 0


def test_sequential_mode_request_count_and_order(sample_inputs_dir, fake_client_factory, no_sleep):
    client = fake_client_factory(responder)
    inputs = load(sample_inputs_dir, "sequential")

    outcome = run_v2.run_sequential(client, "fake-model", inputs, 100, {}, sleep=no_sleep)

    # 3 retellings + 1 questions turn
    assert len(client.messages.calls) == 4
    assert outcome.num_compactions == 0

    first_call_text = client.messages.calls[0]["messages"][-1]["content"]
    assert "Retelling r01 of 3" in first_call_text
    assert "RETELLING-ONE body" in first_call_text

    second_call_text = client.messages.calls[1]["messages"][-1]["content"]
    assert "Retelling r02 of 3" in second_call_text
    assert "RETELLING-TWO body" in second_call_text

    # the questions turn comes last
    last_call = client.messages.calls[-1]
    assert "QUESTIONS-MARKER" in last_call["messages"][-1]["content"]


def test_noisy_mode_noise_docs_fixed_order_and_compaction_replaces_history(
    sample_inputs_dir, fake_client_factory, no_sleep, monkeypatch
):
    # 3 retellings in the fixture; force a compaction after the 2nd so we don't need 12 turns to see one.
    monkeypatch.setattr(run_v2, "COMPACTION_POINTS", {2})
    client = fake_client_factory(responder)
    inputs = load(sample_inputs_dir, "noisy")
    assert len(inputs.noise_docs) == 2

    outcome = run_v2.run_noisy(client, "fake-model", inputs, 100, {}, sleep=no_sleep)

    # retelling1, noise1, retelling2, noise2, compaction, retelling3 (no noise doc left), questions
    calls = client.messages.calls
    assert len(calls) == 7
    assert outcome.num_compactions == 1

    # noise docs appear in fixed order, paired with the matching noise question
    noise1_text = calls[1]["messages"][-1]["content"]
    assert "NOISE-DOC-ONE body" in noise1_text
    assert "Question for doc one?" in noise1_text

    noise2_text = calls[3]["messages"][-1]["content"]
    assert "NOISE-DOC-TWO body" in noise2_text
    assert "Question for doc two?" in noise2_text

    # the compaction call (index 4) still sees the full prior history
    compaction_call = calls[4]
    assert len(compaction_call["messages"]) > 2
    assert "Your context will be replaced" in compaction_call["messages"][-1]["content"]

    # the call right after compaction (retelling 3) sees ONLY the collapsed notes + ack + itself
    post_compaction_call = calls[5]
    assert len(post_compaction_call["messages"]) == 3
    assert post_compaction_call["messages"][0]["role"] == "user"
    assert post_compaction_call["messages"][0]["content"].startswith("Notes from your earlier reading:")
    assert "NOTES-CONTENT-XYZ" in post_compaction_call["messages"][0]["content"]
    assert post_compaction_call["messages"][1]["role"] == "assistant"
    assert "Retelling r03 of 3" in post_compaction_call["messages"][2]["content"]

    # the questions turn comes last
    last_call = calls[-1]
    assert "QUESTIONS-MARKER" in last_call["messages"][-1]["content"]
