from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def similarity(left: Any, right: Any) -> float:
    return SequenceMatcher(None, str(left).strip().casefold(), str(right).strip().casefold()).ratio()


def best_fuzzy_match(left: Any, candidates: list[Any], field: str, threshold: float = 0.9) -> tuple[Any | None, float]:
    best = (None, 0.0)
    for candidate in candidates:
        score = similarity(left.data.get(field), candidate.data.get(field))
        if score > best[1]:
            best = (candidate, score)
    return best if best[1] >= threshold else (None, best[1])
