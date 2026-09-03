from __future__ import annotations

from typing import Any


def evaluate_amount(left: float | None, right: float | None, absolute_tolerance: float, percent_tolerance: float) -> tuple[bool, float | None, float | None]:
    if left is None or right is None:
        return False, None, None
    variance = left - right
    absolute = abs(variance)
    percent = absolute / max(abs(left), abs(right), 1e-12) * 100
    return absolute <= absolute_tolerance or percent <= percent_tolerance, variance, percent


def evaluate_date(left: Any, right: Any, tolerance_days: int) -> bool:
    from .engine import _date
    l, r = _date(left), _date(right)
    return l is not None and r is not None and abs((l - r).days) <= tolerance_days


def evaluate_currency(left: Any, right: Any) -> bool:
    return str(left or "").upper() == str(right or "").upper()


def evaluate_sign(left: float | None, right: float | None) -> bool:
    if left is None or right is None or left == 0 or right == 0:
        return True
    return (left < 0) == (right < 0)
