from __future__ import annotations


def classify_variance(abs_variance: float, threshold: float) -> str:
    """Classify an exception deterministically; LLMs must not decide materiality."""
    if threshold <= 0:
        return "material" if abs_variance > 0 else "immaterial"
    return "material" if abs_variance >= threshold else "immaterial"
