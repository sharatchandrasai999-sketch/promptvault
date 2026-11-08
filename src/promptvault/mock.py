"""A deterministic mock LLM — no API keys, no network, no cost.

The mock reads the *prompt text* for simple keyword instructions and
transforms the input accordingly, so two prompt wordings can genuinely
produce different outputs and an A/B test can tell them apart:

- prompt mentions "uppercase" -> input uppercased
- prompt mentions "lowercase" -> input lowercased
- prompt mentions "reverse"   -> input reversed
- otherwise                  -> input returned unchanged
"""

from __future__ import annotations


def mock_reply(prompt_text: str, user_input: str) -> str:
    """Return the mock model's reply for ``user_input`` under ``prompt_text``."""
    lowered = prompt_text.lower()
    if "uppercase" in lowered:
        return user_input.upper()
    if "lowercase" in lowered:
        return user_input.lower()
    if "reverse" in lowered:
        return user_input[::-1]
    return user_input
