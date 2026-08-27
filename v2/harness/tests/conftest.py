"""Shared pytest fixtures: sys.path setup and a fake Anthropic client (no network, no credentials)."""
from __future__ import annotations

import sys
from pathlib import Path

HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

import pytest


class FakeUsage:
    def __init__(self, input_tokens=1, output_tokens=1, cache_creation_input_tokens=0, cache_read_input_tokens=0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation_input_tokens
        self.cache_read_input_tokens = cache_read_input_tokens


class FakeBlock:
    def __init__(self, text: str):
        self.text = text


class FakeResponse:
    def __init__(self, text: str, usage: FakeUsage | None = None):
        self.content = [FakeBlock(text)]
        self.usage = usage or FakeUsage()


class FakeCountResult:
    def __init__(self, input_tokens: int):
        self.input_tokens = input_tokens


class FakeMessages:
    """Stands in for client.messages: records every call and answers from a responder callback."""

    def __init__(self, responder=None):
        self.calls: list[dict] = []
        self.count_tokens_calls: list[dict] = []
        self.responder = responder or (lambda index, kwargs: f"response-{index}")

    def create(self, **kwargs):
        index = len(self.calls)
        self.calls.append(kwargs)
        text = self.responder(index, kwargs)
        return FakeResponse(text)

    def count_tokens(self, **kwargs):
        self.count_tokens_calls.append(kwargs)
        content = kwargs["messages"][0]["content"]
        return FakeCountResult(input_tokens=max(1, len(content) // 4))


class FakeClient:
    def __init__(self, responder=None):
        self.messages = FakeMessages(responder)


@pytest.fixture
def fake_client_factory():
    return FakeClient


@pytest.fixture
def no_sleep():
    """A sleep() stand-in that does nothing, so retry/backoff tests never actually wait."""
    return lambda seconds: None


@pytest.fixture
def sample_inputs_dir(tmp_path):
    """A tiny 3-retelling, 2-noise-doc fixture tree, shaped like the real v2/test-input layout."""
    retellings_dir = tmp_path / "test-input" / "retellings"
    retellings_dir.mkdir(parents=True)
    questions_path = tmp_path / "test-input" / "questions.md"
    noise_dir = tmp_path / "noise"
    noise_dir.mkdir(parents=True)
    noise_questions_path = noise_dir / "questions.md"

    # Written out of order on purpose, to prove sorting (not creation order) fixes the sequence.
    (retellings_dir / "r03.md").write_text("RETELLING-THREE body", encoding="utf-8")
    (retellings_dir / "r01.md").write_text("RETELLING-ONE body", encoding="utf-8")
    (retellings_dir / "r02.md").write_text("RETELLING-TWO body", encoding="utf-8")

    (noise_dir / "n02.md").write_text("NOISE-DOC-TWO body", encoding="utf-8")
    (noise_dir / "n01.md").write_text("NOISE-DOC-ONE body", encoding="utf-8")

    questions_path.write_text("QUESTIONS-MARKER: what happened?", encoding="utf-8")
    noise_questions_path.write_text("1. Question for doc one?\n2. Question for doc two?\n", encoding="utf-8")

    return {
        "retellings_dir": retellings_dir,
        "questions_path": questions_path,
        "noise_dir": noise_dir,
        "noise_questions_path": noise_questions_path,
    }
