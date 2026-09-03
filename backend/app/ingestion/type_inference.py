from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any


def infer_type(values: list[Any]) -> str:
    non_null = [v for v in values if v not in (None, "")]
    if not non_null:
        return "string"
    if all(isinstance(v, bool) for v in non_null):
        return "boolean"
    if all(isinstance(v, int) and not isinstance(v, bool) for v in non_null):
        return "integer"
    if all(isinstance(v, (int, float, Decimal)) and not isinstance(v, bool) for v in non_null):
        return "number"
    if all(isinstance(v, datetime) for v in non_null):
        return "datetime"
    if all(isinstance(v, date) for v in non_null):
        return "date"
    if all(isinstance(v, str) and _looks_like_date(v) for v in non_null):
        return "date"
    if all(isinstance(v, str) and _looks_like_number(v) for v in non_null):
        return "number"
    return "string"


def _looks_like_date(value: str) -> bool:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            datetime.strptime(value.strip(), fmt)
            return True
        except ValueError:
            continue
    return False


def _looks_like_number(value: str) -> bool:
    try:
        float(value.replace(",", "").strip())
        return True
    except ValueError:
        return False
