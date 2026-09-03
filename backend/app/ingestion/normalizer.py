from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_value(value: Any, target_type: str) -> Any:
    if value in (None, ""):
        return None
    if target_type == "string":
        return str(value).strip()
    if target_type == "integer":
        return int(str(value).replace(",", "").strip())
    if target_type in {"number", "money"}:
        try:
            return float(Decimal(str(value).replace(",", "").replace("£", "").replace("$", "").strip()))
        except InvalidOperation as exc:
            raise ValueError(f"Cannot normalize value as {target_type}: {value!r}") from exc
    if target_type == "boolean":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "yes", "y", "1"}:
            return True
        if normalized in {"false", "no", "n", "0"}:
            return False
        raise ValueError(f"Cannot normalize boolean value: {value!r}")
    if target_type == "date":
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(str(value).strip(), fmt).date().isoformat()
            except ValueError:
                continue
        raise ValueError(f"Cannot normalize date value: {value!r}")
    if target_type == "datetime":
        if isinstance(value, datetime):
            return value.isoformat()
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).isoformat()
    return value
