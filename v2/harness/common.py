"""Shared helpers used by run_v2.py, judge.py and report.py.

Kept separate so each entry point stays focused on its own CLI and control flow. Nothing here makes
a network call on import; the Anthropic SDK is only touched inside functions that actually need it,
so tests that inject a fake client never require credentials.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

REQUEST_TIMEOUT_S = 600.0
BACKOFF_CAP_S = 4.0
MAX_ATTEMPTS = 3
CHARS_PER_TOKEN_ESTIMATE = 4


# --------------------------------------------------------------------------- env / paths

def load_dotenv(path: Path) -> dict[str, str]:
    """Parse KEY=value lines from `path` and set them in os.environ (existing env vars win).

    Returns the dict of values found in the file, whether or not they were applied. Missing file is
    not an error: it just means nothing is loaded.
    """
    found: dict[str, str] = {}
    if not path.is_file():
        return found
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        if not key:
            continue
        found[key] = value
        os.environ.setdefault(key, value)
    return found


def repo_root_from(harness_file: str) -> Path:
    """Two levels up from a file inside v2/harness/ is the repo root."""
    return Path(harness_file).resolve().parents[2]


# --------------------------------------------------------------------------- token estimate

def estimate_tokens(text: str) -> int:
    """4-chars-per-token estimate, used when no credentials are available to count for real."""
    if not text:
        return 0
    return max(1, (len(text) + CHARS_PER_TOKEN_ESTIMATE - 1) // CHARS_PER_TOKEN_ESTIMATE)


def count_tokens_for_text(client: Any, model: str, text: str, has_credentials: bool) -> tuple[int, str]:
    """Token count for one file's text plus the method used ("api" or "estimate").

    Falls back to the estimate on any error from the count-tokens endpoint, since a dry-run preview
    must never fail just because the pricing/counting call did.
    """
    if has_credentials and client is not None:
        try:
            result = client.messages.count_tokens(
                model=model, messages=[{"role": "user", "content": text}]
            )
            return int(result.input_tokens), "api"
        except Exception:
            pass
    return estimate_tokens(text), "estimate"


# --------------------------------------------------------------------------- usage / cost

def usage_to_dict(usage: Any) -> dict[str, int]:
    """Normalize an Anthropic Usage object (or a plain dict, for fakes) into a fixed set of int fields."""
    def get(name: str) -> int:
        if usage is None:
            return 0
        if isinstance(usage, dict):
            value = usage.get(name)
        else:
            value = getattr(usage, name, None)
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0

    return {
        "input_tokens": get("input_tokens"),
        "output_tokens": get("output_tokens"),
        "cache_creation_input_tokens": get("cache_creation_input_tokens"),
        "cache_read_input_tokens": get("cache_read_input_tokens"),
    }


def load_prices(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cost_usd(usage: dict[str, int], model_id: str, prices: dict) -> float | None:
    """List-price cost of one call, or None if the model has no price row."""
    p = prices.get(model_id)
    if p is None:
        return None
    per = 1_000_000
    return (
        usage["input_tokens"] * p["input_per_M"] / per
        + usage["cache_read_input_tokens"] * p["cached_input_per_M"] / per
        + usage["cache_creation_input_tokens"] * p["cache_write_per_M"] / per
        + usage["output_tokens"] * p["output_per_M"] / per
    )


def sum_usage(entries: list[dict[str, int]]) -> dict[str, int]:
    totals = {"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}
    for entry in entries:
        for key in totals:
            totals[key] += entry.get(key, 0)
    return totals


# --------------------------------------------------------------------------- response helpers

def extract_text(response: Any) -> str:
    """Join every text block of a Messages API response into one string."""
    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")
    if not content:
        return ""
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts)


# --------------------------------------------------------------------------- retrying call

def call_with_retries(
    client: Any,
    *,
    model: str,
    system: str | None,
    messages: list[dict],
    max_tokens: int,
    sleep: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
) -> tuple[Any, float]:
    """Call messages.create with up to `max_attempts` visible, billed attempts.

    Backoff between attempts is 1 s, 2 s, 4 s (2**i capped at BACKOFF_CAP_S); the last attempt is not
    followed by a sleep. Returns (response, latency_seconds) for the attempt that succeeded. Raises
    RuntimeError, chained from the last exception, if every attempt fails.
    """
    kwargs: dict[str, Any] = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system is not None:
        kwargs["system"] = system

    last_exc: Exception | None = None
    for attempt_index in range(max_attempts):
        start = time.monotonic()
        try:
            response = client.messages.create(**kwargs)
            return response, time.monotonic() - start
        except Exception as exc:  # noqa: BLE001 - every attempt is logged, then re-raised after the last
            last_exc = exc
            print(
                f"attempt {attempt_index + 1}/{max_attempts} failed: {type(exc).__name__}: {exc}",
                flush=True,
            )
            if attempt_index + 1 < max_attempts:
                sleep(min(2 ** attempt_index, BACKOFF_CAP_S))
    raise RuntimeError(f"all {max_attempts} attempts failed: {last_exc}") from last_exc


# --------------------------------------------------------------------------- judge JSON parsing

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_json(text: str) -> dict:
    """Parse the judge's JSON reply, fenced or bare.

    Tries, in order: a ```json ... ``` (or bare ```...```) fence; the whole text; the first
    balanced-brace object found in the text. Raises ValueError with the offending text on failure.
    """
    candidates: list[str] = []
    fence_match = _FENCE_RE.search(text)
    if fence_match:
        candidates.append(fence_match.group(1).strip())
    candidates.append(text.strip())

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(text[first_brace : last_brace + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, TypeError):
            continue
    raise ValueError(f"could not parse JSON from judge response: {text!r}")


# --------------------------------------------------------------------------- misc file helpers

def read_text_files_sorted(directory: Path, pattern: str = "*.md", exclude: set[str] | None = None) -> list[tuple[str, str]]:
    """(filename, text) pairs for files matching `pattern` in `directory`, sorted by filename."""
    exclude = exclude or set()
    if not directory.is_dir():
        return []
    paths = sorted(p for p in directory.glob(pattern) if p.name not in exclude)
    return [(p.name, p.read_text(encoding="utf-8")) for p in paths]
