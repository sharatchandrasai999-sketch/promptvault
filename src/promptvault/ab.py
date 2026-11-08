"""A/B comparison of two prompt versions over a small test set.

The test set is a JSON file holding a list of::

    {"input": ..., "expected": ...}

Each version is run through the deterministic mock LLM (see ``mock.py``)
and scored by exact match against ``expected``. Latency is real elapsed
time per call, measured with ``time.perf_counter`` — it is small and
noisy for a mock, but it is measured, not invented.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .mock import mock_reply
from .store import PromptVaultError, get_version


def _score(prompt_text: str, testset: list[dict]) -> tuple[float, float]:
    """Return (exact-match accuracy, mean latency in ms) for one prompt."""
    correct = 0
    latencies: list[float] = []
    for case in testset:
        start = time.perf_counter()
        reply = mock_reply(prompt_text, str(case["input"]))
        latencies.append((time.perf_counter() - start) * 1000)
        if reply == str(case["expected"]):
            correct += 1
    accuracy = correct / len(testset) if testset else 0.0
    mean_latency = sum(latencies) / len(latencies) if latencies else 0.0
    return accuracy, mean_latency


def run_ab(store: Path, name: str, v1: int, v2: int, testset_path: str) -> dict:
    """Compare versions ``v1`` and ``v2`` of ``name``; return the results."""
    if not Path(testset_path).exists():
        raise PromptVaultError(f"test set file not found: {testset_path}")
    try:
        testset = json.loads(Path(testset_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptVaultError(f"test set is not valid JSON: {exc}") from exc
    if not isinstance(testset, list) or not testset:
        raise PromptVaultError("test set must be a non-empty JSON list")
    for case in testset:
        if not isinstance(case, dict) or "input" not in case or "expected" not in case:
            raise PromptVaultError('each test case needs "input" and "expected"')

    text1 = get_version(store, name, v1)["text"]
    text2 = get_version(store, name, v2)["text"]
    acc1, lat1 = _score(text1, testset)
    acc2, lat2 = _score(text2, testset)

    if (acc1, -lat1) >= (acc2, -lat2):
        winner = v1
    else:
        winner = v2

    return {
        "name": name,
        "cases": len(testset),
        "v1": {"version": v1, "accuracy": acc1, "mean_latency_ms": lat1},
        "v2": {"version": v2, "accuracy": acc2, "mean_latency_ms": lat2},
        "winner": winner,
    }
