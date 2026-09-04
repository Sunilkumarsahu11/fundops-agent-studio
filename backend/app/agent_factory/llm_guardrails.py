from __future__ import annotations

import re
from typing import Any


class LLMGuardrailError(ValueError):
    """Raised when an LLM request violates deterministic safety limits."""


_INJECTION_PATTERNS = (
    r"ignore\s+(all|any|previous|prior)\s+instructions",
    r"system\s+prompt",
    r"developer\s+message",
    r"reveal\s+(your|the)\s+(prompt|instructions)",
    r"disable\s+(the\s+)?(guardrails|controls|validation)",
    r"bypass\s+(approval|governance|validation)",
)


def validate_user_request(text: str, max_chars: int) -> str:
    value = text.strip()
    if not value:
        raise LLMGuardrailError("LLM request cannot be empty")
    if len(value) > max_chars:
        raise LLMGuardrailError(f"Request exceeds LLM_MAX_INPUT_CHARS={max_chars}")
    if any(re.search(pattern, value, re.IGNORECASE) for pattern in _INJECTION_PATTERNS):
        raise LLMGuardrailError("Request contains an instruction that attempts to override agent governance")
    return value


def compact_result(result: dict[str, Any], max_chars: int) -> dict[str, Any]:
    """Bound explanation context; never alter the financial result semantics."""
    text = str(result)
    if len(text) <= max_chars:
        return result
    summary: dict[str, Any] = {"truncated_for_explanation": True}
    for key in ("status", "summary", "exception_count", "warnings", "reconciliation_id"):
        if key in result:
            summary[key] = result[key]
    return summary


def validate_plan_size(step_count: int, tool_count: int, max_steps: int, max_tools: int) -> None:
    if step_count < 1:
        raise LLMGuardrailError("LLM produced no executable workflow steps")
    if step_count > max_steps:
        raise LLMGuardrailError(f"LLM plan exceeds maximum workflow steps: {max_steps}")
    if tool_count > max_tools:
        raise LLMGuardrailError(f"LLM plan exceeds maximum tool selections: {max_tools}")
